"""Resultados empíricos e cenários condicionais com rastreabilidade."""
from __future__ import annotations

import itertools
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

from .common import ROOT,basis,dump_json,finite_or_none,save_csv,save_frame,week_start
from .statistics import block_indices,distribution,holding_crossing,pair_pnl,weekly_intervals
from .trades import build_trades,minute_robustness


def fidelity(config,hourly,weekends):
    rows=[]
    periods=[('full',None),('recent_104_weeks',weekends.tail(104).week.min())]
    for period,since in periods:
        h=hourly[hourly.valid & ((hourly.t>=since) if since is not None else True)]
        w=weekends[weekends.valid & ((weekends.week>=since) if since is not None else True)]
        samples=[('common_hours',h.basis_log_bps,h.week),('reopen',w.b_0,w.week),('one_hour',w.b_1h,w.week),('seven_hours',w.b_7h,w.week)]
        for name,values,weeks in samples:
            out={'sample':name,'period':period,**distribution(values),**weekly_intervals(values,weeks,config)}
            out['tail_observations']=int(np.sum(np.abs(values.dropna())>=out['p95_abs_bps'])) if out['n'] else 0
            rows.append(out)
        for regime,flag in [('large_gap',True),('other_gap',False)]:
            take=w[w.stress_flag.eq(flag)]
            out={'sample':'reopen_'+regime,'period':period,**distribution(take.b_0),**weekly_intervals(take.b_0,take.week,config)}
            out['tail_observations']=int(np.sum(take.b_0.abs()>=out['p95_abs_bps'])) if out['n'] else 0
            rows.append(out)
    result=pd.DataFrame(rows)
    save_csv(result,'T1_fidelidade.csv')
    worst=weekends[weekends.valid].assign(abs_basis=lambda x:x.b_0.abs()).nlargest(5,'abs_basis')
    save_csv(worst[['id','week','t_c','t_0','b_c','b_0','g','m','b_1h','b_7h','abs_basis','calendar_status']],'T1_worst_weekends.csv')
    paired=weekends[weekends.valid & weekends[['b_0','b_1h','b_7h']].notna().all(axis=1)]
    paired_rows=[]
    for point,col in [('reopen','b_0'),('one_hour','b_1h'),('seven_hours','b_7h')]:
        paired_rows.append({'point':point,**distribution(paired[col]),**weekly_intervals(paired[col],paired.week,config)})
    save_csv(pd.DataFrame(paired_rows),'T2_hourly_paired.csv')
    sensitivity=[]
    for block in config['analysis']['bootstrap_block_sensitivity_weeks']:
        for name,values,weeks in [('common_hours',hourly.loc[hourly.valid,'basis_log_bps'],hourly.loc[hourly.valid,'week']),('reopen',weekends.loc[weekends.valid,'b_0'],weekends.loc[weekends.valid,'week'])]:
            sensitivity.append({'sample':name,'block_weeks':block,**weekly_intervals(values,weeks,config,block=block)})
    save_csv(pd.DataFrame(sensitivity),'T1_block_sensitivity.csv')
    return result


def holding_costs(config,facts):
    c=config['holding_cost']; rows=[];baseline=[]
    for etf in ['gld','gldm']:
        measured=facts.get(etf,{})
        rate=measured.get('expense_bps_year')
        if rate is None:
            rate=c[etf+'_fee_bps_per_year']
        if abs(rate-c[etf+'_fee_bps_per_year'])>1e-6:
            raise ValueError('Taxa do ETF diverge do parâmetro congelado: validar alteração de vigência.')
        spreads=sorted(set(c['etf_full_spread_bps_grid']+([measured['spread_30d_bps']] if measured.get('spread_30d_bps') is not None else [])))
        combinations=itertools.product(c['notional_usd_grid'],c['token_fee_bps_per_fill_grid'],c['token_full_spread_bps_grid'],c['etf_fee_bps_per_fill_grid'],spreads,c['stablecoin_conversion_roundtrip_bps_grid'],c['network_withdrawal_roundtrip_usd_grid'],c['token_storage_hypothetical_bps_per_year_grid'])
        for n,ft,st,fe,se,conv,network,storage in combinations:
            trt=2*ft+st+conv+10000*network/n; ert=2*fe+se
            cross=holding_crossing(trt,ert,storage,rate)
            for horizon in c['horizon_months_grid']:
                rows.append({'etf':etf.upper(),'notional_usd':n,'horizon_months':horizon,'token_fee_per_fill_bps':ft,
                             'token_full_spread_bps':st,'etf_fee_per_fill_bps':fe,'etf_full_spread_bps':se,
                             'conversion_rt_bps':conv,'network_rt_usd':network,'token_storage_bps_year':storage,
                             'etf_fee_bps_year':rate,'token_cost_bps':trt+storage*horizon/12,'etf_cost_bps':ert+rate*horizon/12,
                             'difference_bps':trt-ert+(storage-rate)*horizon/12,**cross,
                             'cost_status':'scenario_not_historical_realized_cost'})
        b=c['baseline']; se=measured.get('spread_30d_bps')
        if se is None: se=b['etf_full_spread_fallback_bps']
        trt=2*b['token_fee_bps_per_fill']+b['token_full_spread_bps']+b['conversion_roundtrip_bps']+10000*b['network_withdrawal_roundtrip_usd']/b['notional_usd']
        ert=2*b['etf_fee_bps_per_fill']+se
        for storage in c['token_storage_hypothetical_bps_per_year_grid']:
            cross=holding_crossing(trt,ert,storage,rate)
            for horizon in c['horizon_months_grid']:
                baseline.append({'etf':etf.upper(),'horizon_months':horizon,'notional_usd':b['notional_usd'],
                                 'token_storage_bps_year':storage,'token_rt_bps':trt,'etf_rt_bps':ert,
                                 'token_cost_bps':trt+storage*horizon/12,'etf_cost_bps':ert+rate*horizon/12,**cross,
                                 'token_spread_status':'assumed','etf_spread_status':'official_30day_median_current' if measured.get('spread_30d_bps') is not None else 'assumed_fallback',
                                 'source_asof':measured.get('market_asof_text'),'scope':'USD_pretax_equal_access_not_investment_recommendation'})
    save_csv(pd.DataFrame(rows),'T3_custos_etfs.csv')
    base=pd.DataFrame(baseline);save_csv(base,'T3_baseline.csv')
    return base


def evolution(config,hourly):
    h=hourly.copy()
    h['quarter']=h.t.dt.tz_localize(None).dt.to_period('Q')
    h['gold_r']=np.log(h.S).diff().where(h.t.diff().eq(pd.Timedelta(hours=1)) & h.valid & h.valid.shift(1,fill_value=False))
    rows=[]
    start,end=pd.Timestamp(config['data']['start_utc']),pd.Timestamp(config['data']['end_exclusive_utc'])
    for quarter,g in h.groupby('quarter'):
        valid=g[g.valid]
        qa=quarter.start_time.tz_localize('UTC');qb=(quarter+1).start_time.tz_localize('UTC')
        complete=qa>=start and qb<=end
        rows.append({'quarter':str(quarter),'quarter_start':qa,'scheduled_hours_upper_bound':len(g),'valid_hours':len(valid),
                     'coverage_fraction':len(valid)/len(g),'median_abs_bps':valid.basis_log_bps.abs().median(),
                     'p95_abs_bps':valid.basis_log_bps.abs().quantile(.95),'gold_hourly_vol_bps':g.gold_r.std()*10000,
                     'complete_quarter':complete,'inference_eligible':complete and len(valid)/len(g)>=config['analysis']['trend_min_valid_hours_fraction_per_quarter']})
    result=pd.DataFrame(rows);save_csv(result,'T4_evolucao.csv')
    trend=[]
    for floor in [.5,config['analysis']['basis_log_floor_bps'],2.]:
        g=result[result.inference_eligible & result.gold_hourly_vol_bps.gt(0)].dropna().copy()
        if len(g)<config['analysis']['trend_min_complete_quarters']:
            trend.append({'floor_bps':floor,'n_quarters':len(g),'status':'insufficient_quarters'});continue
        y=np.log(g.median_abs_bps.clip(lower=floor))
        if y.std()<1e-9:
            trend.append({'floor_bps':floor,'n_quarters':len(g),'status':'floor_masks_variation'});continue
        times=(g.quarter_start-g.quarter_start.min()).dt.total_seconds()/(365.25*86400)
        X=sm.add_constant(pd.DataFrame({'time_years':times,'log_gold_vol':np.log(g.gold_hourly_vol_bps)},index=g.index))
        fit=sm.OLS(y,X).fit(cov_type='HAC',cov_kwds={'maxlags':config['analysis']['hac_lags_quarters']})
        lo,hi=fit.conf_int().loc['time_years']
        trend.append({'floor_bps':floor,'n_quarters':len(g),'status':'exploratory_association','beta_per_year':float(fit.params['time_years']),
                      'beta_lo':float(lo),'beta_hi':float(hi),'annual_change_fraction':float(np.expm1(fit.params['time_years'])),
                      'p_value_exploratory':float(fit.pvalues['time_years'])})
    trend=pd.DataFrame(trend);save_csv(trend,'T4_trend.csv')
    return result,trend


def _pnl_for(frame,settings,*,scale_basis=1.,scale_costs=1.):
    pin=frame.P_in.to_numpy();pout=frame.P_out.to_numpy()
    if scale_basis!=1:
        pin=frame.S_in.to_numpy()*np.exp(frame.b_in.to_numpy()*scale_basis/10000)
        pout=frame.S_out.to_numpy()*np.exp(frame.b_out.to_numpy()*scale_basis/10000)
    si,so=frame.S_in.to_numpy(),frame.S_out.to_numpy()
    bidin=si-(si-frame.bid_in.to_numpy())*scale_costs
    askin=si+(frame.ask_in.to_numpy()-si)*scale_costs
    bidout=so-(so-frame.bid_out.to_numpy())*scale_costs
    askout=so+(frame.ask_out.to_numpy()-so)*scale_costs
    return pair_pnl(np.sign(frame.signal_basis_bps.to_numpy()*scale_basis),pin,pout,si,so,
                    bid_in=bidin,ask_in=askin,bid_out=bidout,ask_out=askout,
                    token_fee=settings['token_fee_bps_per_fill']*scale_costs,
                    gold_fee=settings['gold_commission_bps_per_fill']*scale_costs,
                    token_spread=settings['token_full_spread_bps']*scale_costs,
                    conversion=settings['conversion_roundtrip_bps']*scale_costs,
                    slippage=settings['slippage_bps_per_fill']*scale_costs)


def convergence(config,minutes,weekends):
    trades=build_trades(config,minutes,weekends)
    baseline=config['convergence']['baseline']
    p=_pnl_for(trades,baseline)
    for name,values in p.items(): trades[name]=np.where(trades.path_valid,values,np.nan)
    trades['week_model_pnl_bps']=np.where(trades.path_valid,np.where(trades.signal_eligible,trades.after_modeled_before_unknown_carry_bps,0),np.nan)
    save_frame(trades,ROOT/'data/panel/trades_A.parquet')
    save_csv(trades,'T2_trade_ledger.csv')
    cfg=config['convergence'];rows=[]
    grid=itertools.product(cfg['token_fee_bps_per_fill_grid'],cfg['token_full_spread_bps_grid'],cfg['gold_commission_bps_per_fill_grid'],cfg['stablecoin_conversion_roundtrip_bps_grid'],cfg['slippage_bps_per_fill_grid'])
    for ft,st,fg,conversion,slip in grid:
        settings={'token_fee_bps_per_fill':ft,'token_full_spread_bps':st,'gold_commission_bps_per_fill':fg,'conversion_roundtrip_bps':conversion,'slippage_bps_per_fill':slip}
        pnl=_pnl_for(trades,settings)['after_modeled_before_unknown_carry_bps']
        for horizon,g in trades.groupby('horizon_hours'):
            ix=g.index; good=g.path_valid & g.signal_eligible
            for carry in cfg['residual_carry_roundtrip_bps_grid']:
                v=pnl[ix][good.to_numpy()]-carry
                rows.append({'horizon_hours':horizon,**settings,'assumed_residual_carry_bps':carry,
                             'calendar_candidates':len(g),'valid_paths':int(g.path_valid.sum()),'signals_available':int(g.signal_available.sum()),
                             'signals':int((g.signal_available & g.signal_eligible & g.calendar_valid).sum()),'evaluated_trades':int(good.sum()),
                             'mean_model_bps':float(np.mean(v)) if len(v) else np.nan,'median_model_bps':float(np.median(v)) if len(v) else np.nan,
                             'positive_fraction':float(np.mean(v>0)) if len(v) else np.nan,'worst_model_bps':float(np.min(v)) if len(v) else np.nan,
                             'cost_status':'conditional_assumptions_borrow_not_verified','inferential_gate_passed':int(g.path_valid.sum())>=cfg['min_valid_weekends_for_aggregate_inference']})
    table=pd.DataFrame(rows);save_csv(table,'T2_convergencia.csv');save_csv(table,'variants.csv')
    primary=trades[trades.horizon_hours.eq(cfg['exit_after_entry_hours'])].copy()
    estimates=[]
    for carry in cfg['residual_carry_roundtrip_bps_grid']:
        v=primary.after_modeled_before_unknown_carry_bps.where(primary.path_valid & primary.signal_eligible)-carry
        out={'assumed_residual_carry_bps':carry,'valid_paths':int(primary.path_valid.sum()),'evaluated_trades':int(v.notna().sum()),
             'calendar_weeks':len(primary),'signals_total':int((primary.calendar_valid & primary.signal_available & primary.signal_eligible).sum()),
             'mean_trade_model_bps':v.mean(),'median_trade_model_bps':v.median(),'worst_trade_model_bps':v.min(),
             'positive_trade_fraction':(v.dropna()>0).mean(),'borrow_and_access_verified':False,
             'mean_gross_mid_bps':primary.loc[primary.evaluated_trade,'gross_mid_bps'].mean(),
             'positive_gross_fraction':(primary.loc[primary.evaluated_trade,'gross_mid_bps']>0).mean(),
             'mean_total_modeled_cost_bps':(primary.loc[primary.evaluated_trade,'gross_mid_bps']-primary.loc[primary.evaluated_trade,'after_modeled_before_unknown_carry_bps']).mean(),
             'signals_unassessed':int((primary.calendar_valid & primary.signal_available & primary.signal_eligible & ~primary.path_valid).sum())}
        if int(primary.path_valid.sum())>=cfg['min_valid_weekends_for_aggregate_inference']:
            out.update(weekly_intervals(v,primary.week,config,signed=True))
        else: out['ci_status']='minimum_valid_paths_gate_failed'
        estimates.append(out)
    stats=pd.DataFrame(estimates);save_csv(stats,'T2_baseline_inference.csv')
    robustness=minute_robustness(config,minutes,weekends);save_csv(robustness,'T2_minute_robustness.csv')
    return trades,stats


def scenarios(config,trades,weekends):
    primary=trades[trades.horizon_hours.eq(config['convergence']['exit_after_entry_hours'])].copy().reset_index(drop=True)
    nvalid=int(primary.path_valid.sum()); stochastic=nvalid>=config['scenarios']['min_recent_valid_weekends']
    out=[]
    if stochastic:
        # Sorteios pareados por cenário, com os mesmos índices e ausências preservadas.
        idx=block_indices(len(primary),config['analysis']['bootstrap_replicates'],config['analysis']['bootstrap_block_weeks'],config['analysis']['bootstrap_seed'])
        idx=idx[:,:config['scenarios']['horizon_weeks']]
    for scenario in ['baseline','lower_friction','stress']:
        settings=config['scenarios'][scenario]
        k,c=settings['basis_scale'],settings['variable_cost_scale']
        eligible=primary.signal_basis_bps.abs().to_numpy()*k>=config['convergence']['signal_abs_basis_min_log_bps']
        pnl=_pnl_for(primary,config['convergence']['baseline'],scale_basis=k,scale_costs=c)['after_modeled_before_unknown_carry_bps']
        values=np.where(primary.path_valid.to_numpy() & eligible,pnl,np.nan)
        b0=primary.weekend_basis_bps.to_numpy()*k
        validb=primary.calendar_valid.to_numpy() & np.isfinite(b0)
        record={'scenario':scenario,'method':'paired_joint_circular_weekly_blocks' if stochastic else 'deterministic_sensitivity_insufficient_joint_paths',
                'valid_joint_paths':nvalid,'calendar_weeks':len(primary),'basis_scale':k,'variable_cost_scale':c,
                'volume_scale':settings['volume_scale'],'storage_bps_year':settings['token_storage_bps_per_year'],
                'assumptions_not_causal_effects':True,'median_abs_bps':np.median(np.abs(b0[validb])) if validb.any() else np.nan,
                'p95_abs_bps':np.quantile(np.abs(b0[validb]),.95) if validb.any() else np.nan,
                'mean_trade_model_before_unknown_carry_bps':np.nanmean(values) if np.isfinite(values).any() else np.nan,
                'modeled_positive_fraction':np.mean(values[np.isfinite(values)]>0) if np.isfinite(values).any() else np.nan,
                'hypothetical_median_capacity_usd':primary.capacity_5pct_usd.median()*settings['volume_scale']}
        if stochastic:
            sample_b=np.where(validb,b0,np.nan)[idx]
            sample_p=values[idx]
            sample_n=np.isfinite(sample_p).sum(axis=1)
            mean=np.divide(np.nansum(sample_p,axis=1),sample_n,out=np.full(len(idx),np.nan),where=sample_n>0)
            stats={'median_abs_bps':np.nanmedian(np.abs(sample_b),axis=1),'p95_abs_bps':np.nanquantile(np.abs(sample_b),.95,axis=1),'mean_trade_model_bps':mean}
            for name,arr in stats.items():
                finite=arr[np.isfinite(arr)]
                record[name+'_lo'],record[name+'_hi']=np.quantile(finite,[.025,.975]) if len(finite) else (np.nan,np.nan)
            record['median_evaluated_trades_per_52_week_resample']=float(np.median(sample_n))
        out.append(record)
    result=pd.DataFrame(out);save_csv(result,'T5_sensibilidade.csv')
    save_csv(pd.DataFrame([{'parameter':p,'factor':s[p],'scenario':name,'interpretation':'assumed_not_estimated'} for name,s in config['scenarios'].items() if isinstance(s,dict) for p in ['basis_scale','variable_cost_scale','volume_scale']]),'T5_scenario_assumptions.csv')
    return result


def risk_map(config,hourly,weekends):
    q=pd.read_parquet(ROOT/'data/interim/fx_1h.parquet')
    v=q[q.has_trade].copy();v['deviation_bps']=(v.close-1)*10000
    worst=v.iloc[v.deviation_bps.abs().argmax()]
    rows=[{'risk':'stablecoin_reference','metric':'largest_absolute_hourly_close_deviation_bps','value':abs(worst.deviation_bps),'date':worst.bar_start,'type':'measured_Bitfinex_not_all_exchanges'},
          {'risk':'stablecoin_reference','metric':'p99_absolute_hourly_close_deviation_bps','value':v.deviation_bps.abs().quantile(.99),'date':'','type':'measured'},
          {'risk':'issuer_and_redemption','metric':'contract_access_and_current_fees','value':np.nan,'date':'','type':'documentary_not_quantified'},
          {'risk':'custody_counterparty_short','metric':'account_specific_access_not_verified','value':np.nan,'date':'','type':'unmeasured_not_zero'}]
    for label,flag in [('large_gap',True),('other_gap',False)]:
        w=weekends[weekends.valid & weekends.stress_flag.eq(flag)]
        rows.append({'risk':label,'metric':'reopen_p95_abs_log_bps','value':w.b_0.abs().quantile(.95),'date':'','n':len(w),'type':'descriptive_small_tail_sample' if len(w)<30 else 'measured'})
    save_csv(pd.DataFrame(rows),'T_riscos.csv')
    fx_compare=pd.read_parquet(ROOT/'data/interim/fx_coinbase_validation.parquet')
    overlap=hourly[hourly.valid].merge(fx_compare[['bar_start','close']],on='bar_start')
    rows=[]
    for name,qvalues in [('Bitfinex_USD_observed',overlap.q),('Coinbase_USD_observed',overlap.close),('USDT_equals_USD_assumption_only',pd.Series(1.,index=overlap.index))]:
        rows.append({'currency_method':name,'sample':'same_common_hours_validation_overlap',**distribution(basis(overlap.p_usdt,qvalues,overlap.S))})
    save_csv(pd.DataFrame(rows),'QA_currency_robustness.csv')


def analyze_all(config):
    from .quality import reference_crosscheck
    reference_crosscheck()
    h=pd.read_parquet(ROOT/'data/panel/panel_hourly.parquet');w=pd.read_parquet(ROOT/'data/panel/panel_weekends.parquet')
    m=pd.read_parquet(ROOT/'data/panel/panel_minutes.parquet')
    facts=json.loads((ROOT/'data/interim/reference_facts.json').read_text())
    fidelity_table=fidelity(config,h,w)
    cost=holding_costs(config,facts)
    quarters,trend=evolution(config,h)
    trades,trade_stats=convergence(config,m,w)
    sim=scenarios(config,trades,w)
    risk_map(config,h,w)
    build_claims(config,h,w,fidelity_table,cost,quarters,trend,trades,trade_stats,sim)
    print('Análises, ledger, custos, bootstrap e cenários concluídos.',flush=True)


def build_claims(config,h,w,fidelity_table,cost,quarters,trend,trades,trade_stats,sim):
    claims=[]
    def add(key,value,unit,source,scope,assumptions=''):
        if isinstance(value,(float,np.floating)) and not np.isfinite(value): value=None
        if isinstance(value,(np.integer,)):value=int(value)
        claims.append({'claim_id':key,'value':value,'unit':unit,'source_file':source,'sample':scope,'assumptions':assumptions})
    add('candidate_weekends',len(w),'weekends','results/panel_status.json','calendar')
    add('valid_weekends',int(w.valid.sum()),'weekends','results/panel_status.json','USD_regular_calendar')
    add('valid_hours',int(h.valid.sum()),'hours','results/panel_status.json','USD_common_hours')
    for sample in ['common_hours','reopen','one_hour','seven_hours']:
        r=fidelity_table[(fidelity_table['sample']==sample)&(fidelity_table.period=='full')].iloc[0]
        for metric in ['median_abs_bps','p95_abs_bps','above_50_fraction','mean_signed_bps','n']:
            add(sample+'_'+metric,r[metric],'count' if metric=='n' else 'fraction' if 'fraction' in metric else 'log_bps','results/T1_fidelidade.csv','full_'+sample)
    for etf in ['GLD','GLDM']:
        r=cost[(cost.etf==etf)&(cost.token_storage_bps_year==0)].iloc[0]
        add(etf+'_crossing_months',r.crossing_months,'months','results/T3_baseline.csv','holding_cost_baseline','token costs assumed; ETF current official fee/spread; USD pretax')
        add(etf+'_status',r.status,'classification','results/T3_baseline.csv','holding_cost_baseline')
        add(etf+'_rt_bps',r.etf_rt_bps,'bps','results/T3_baseline.csv','holding_cost_baseline')
    add('token_rt_bps',cost.iloc[0].token_rt_bps,'bps','results/T3_baseline.csv','holding_cost_baseline','assumed token fees/spread/conversion')
    base=trades[trades.horizon_hours.eq(config['convergence']['exit_after_entry_hours'])]
    add('trade_calendar_weeks',len(base),'weeks','results/T2_baseline_inference.csv','recent_104_calendar_weeks')
    add('trade_valid_paths',int(base.path_valid.sum()),'weeks','results/T2_baseline_inference.csv','recent_104_calendar_weeks')
    add('trade_signals',int((base.signal_available & base.signal_eligible & base.calendar_valid).sum()),'signals','results/T2_baseline_inference.csv','recent_104_calendar_weeks')
    r=trade_stats[trade_stats.assumed_residual_carry_bps.eq(0)].iloc[0]
    for metric in ['evaluated_trades','signals_unassessed','mean_gross_mid_bps','mean_total_modeled_cost_bps','positive_gross_fraction','mean_trade_model_bps','median_trade_model_bps','worst_trade_model_bps','positive_trade_fraction']:
        add(metric,r[metric],'count' if metric in ['evaluated_trades','signals_unassessed'] else 'fraction' if metric.endswith('fraction') else 'bps','results/T2_baseline_inference.csv','recent_104_calendar_weeks','conditional cost assumptions; before unknown borrowing/financing; execution not verified')
    t=trend[trend.floor_bps.eq(config['analysis']['basis_log_floor_bps'])].iloc[0]
    for metric in ['status','n_quarters','beta_per_year','beta_lo','beta_hi']:
        add('trend_'+metric,t.get(metric),'classification' if metric=='status' else 'value','results/T4_trend.csv','complete_quarters','exploratory HAC; association not causality')
    for r in sim.itertuples():
        for metric in ['median_abs_bps','p95_abs_bps','mean_trade_model_before_unknown_carry_bps','method']:
            add(r.scenario+'_'+metric,getattr(r,metric),'classification' if metric=='method' else 'bps','results/T5_sensibilidade.csv','recent_joint_weekly_paths','conditional scenario not forecast')
    add('cutoff_utc',config['data']['end_exclusive_utc'],'timestamp','config/params.json','exclusive_end')
    add('short_access_verified',False,'boolean','config/params.json','all_simulations')
    panel_info=json.loads((ROOT/'results/panel_status.json').read_text())
    add('fx_source_median_abs_difference_bps',panel_info['fx_median_abs_difference_bps'],'log_bps','results/panel_status.json','systematic_first_two_days_each_month')
    add('fx_source_comparison_hours',panel_info['fx_comparison_hours'],'hours','results/panel_status.json','systematic_first_two_days_each_month')
    for key,value in config['convergence']['baseline'].items():add('assumption_'+key,value,'bps','config/params.json','simulation_baseline','hypothesis not observed')
    add('exit_hours',config['convergence']['exit_after_entry_hours'],'hours','config/params.json','simulation')
    add('signal_delay_minutes',config['convergence']['signal_delay_from_reopen_minutes'],'minutes','config/params.json','simulation')
    add('bootstrap_replicates',config['analysis']['bootstrap_replicates'],'replicates','config/params.json','bootstrap')
    frame=pd.DataFrame(claims);save_csv(frame,'claims.csv')
    mapping={r['claim_id']:r['value'] for r in claims}
    dump_json(ROOT/'results/summary.json',mapping)
    decision=pd.DataFrame([
        {'need':'Negociar fora do horário da referência','evidence':'PAXG negocia continuamente; verificar volume e spread no venue','condition':'Acesso ao venue e risco de preço aceito','limit':'negociação contínua não garante preço de execução'},
        {'need':'Exposição ao ouro em horário comum','evidence':f"Mediana absoluta observada: {mapping['common_hours_median_abs_bps']:.2f} bps log",'condition':'Referência e moeda compatíveis','limit':'não demonstra reserva de valor secular'},
        {'need':'Menor custo de manutenção','evidence':f"Cruzamento de custo-base: GLD {mapping['GLD_crossing_months']} meses; GLDM {mapping['GLDM_crossing_months']} meses",'condition':'USD, antes de impostos, custos de token supostos','limit':'custo menor não implica risco menor'},
        {'need':'Capturar convergência','evidence':f"{mapping['evaluated_trades']} operações avaliadas na hipótese-base",'condition':'short, margem, financiamento e liquidez precisam ser verificados','limit':'simulação condicional; sem arbitragem executável comprovada'}])
    save_csv(decision,'T6_decisao.csv')
    text=['# Resultados do projeto','', 'Resultados empíricos e cenários condicionais. Cada linha abaixo possui origem em claims.csv.', '',
          '| ID | Valor | Unidade | Arquivo | Condição |','| --- | --- | --- | --- | --- |']
    for r in claims:text.append(f"| {r['claim_id']} | {r['value']} | {r['unit']} | {r['source_file']} | {r['assumptions']} |")
    text+=['','## Limitações','', 'Preços horários e de minuto são proxies, não quotes simultâneas garantidas. Custos de token e execução dependem das hipóteses declaradas. Empréstimo e financiamento permanecem desconhecidos. Sem conclusão causal sobre competição ou infraestrutura. Dados brutos dos provedores não acompanham o pacote público.']
    (ROOT/'results/RESULTS.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    c=mapping
    def number(key):
        value=c.get(key)
        counts={'valid_hours','valid_weekends','candidate_weekends','fx_source_comparison_hours','trade_calendar_weeks','trade_valid_paths','evaluated_trades','signals_unassessed','trend_n_quarters'}
        if isinstance(value,(float,int,np.floating,np.integer)) and np.isfinite(value):
            return f'{int(value):,}'.replace(',','.') if key in counts else f'{value:.2f}'.replace('.',',')
        return str(value)
    interpretation=f'''# Interpretação dos resultados

Este texto é gerado das tabelas e de claims.csv; não é uma previsão nem recomendação individual.

Descreve o núcleo preservado da pesquisa. A extensão v3, com contrastes pareados, validação temporal e sensibilidade de cobertura, está em [REFINAMENTO.md](REFINAMENTO.md).

## Amostra e qualidade

Foram analisadas {number('valid_hours')} horas válidas e {number('valid_weekends')} dos {number('candidate_weekends')} fins de semana candidatos. O primário usa preços em USD observados, sem preencher câmbio ausente nem barras de ouro inativas. Exceções de calendário não confirmadas ficam fora do primário, registradas em exclusions.csv.

A sobreposição sistemática das fontes de câmbio teve diferença absoluta mediana de {number('fx_source_median_abs_difference_bps')} bps, em {number('fx_source_comparison_hours')} horas. QA_currency_robustness.csv compara a fidelidade na mesma subamostra com as duas fontes e identifica separadamente a hipótese USDT=USD. A checagem independente do ouro contra preço GLD/onças por cota está em QA_gold_reference_summary.json; o proxy do ETF não equivale a uma cotação física executável.

## Fidelidade e reabertura

Em horários comuns, a mediana absoluta foi {number('common_hours_median_abs_bps')} bps log e o p95 foi {number('common_hours_p95_abs_bps')} bps log. Na reabertura, os valores foram {number('reopen_median_abs_bps')} e {number('reopen_p95_abs_bps')} bps log. O desvio absoluto superou 50 bps em {100*c['reopen_above_50_fraction']:.2f}% dos fins de semana válidos.

A mediana após uma hora foi {number('one_hour_median_abs_bps')} bps log; após sete horas, {number('seven_hours_median_abs_bps')} bps log. A trajetória não deve ser confundida com lucro de convergência: o P&L usa preços e quantidades fixas nas duas pernas. A figura de trajetória usa somente fins de semana com os três instantes válidos, e os intervalos são exploratórios em blocos semanais.

## Convergência condicional

Nos últimos {number('trade_calendar_weeks')} fins de semana de calendário, houve {number('trade_valid_paths')} trajetórias completas e {number('evaluated_trades')} operações sinalizadas avaliadas. Outros {number('signals_unassessed')} sinais não tiveram avaliação completa; não foram contabilizados como zero nem declarados sem oportunidade.

O ganho bruto médio por operação foi {number('mean_gross_mid_bps')} bps por perna de ouro, contra {number('mean_total_modeled_cost_bps')} bps de custo total modelado. Após esses custos da hipótese-base, mas antes de empréstimo/financiamento não observados, a média foi {number('mean_trade_model_bps')} bps e a pior operação foi {number('worst_trade_model_bps')} bps. A fração positiva nesse cenário foi {100*c['positive_trade_fraction']:.2f}%.

Esses valores são condicionais a taxa de token {number('assumption_token_fee_bps_per_fill')} bps por execução, spread cheio suposto {number('assumption_token_full_spread_bps')} bps, comissão de ouro {number('assumption_gold_commission_bps_per_fill')} bps por execução, conversão total {number('assumption_conversion_roundtrip_bps')} bps e slippage {number('assumption_slippage_bps_per_fill')} bps por execução. A grade completa está em T2_convergencia.csv. Não se conclui inexistência de arbitragem em outros venues, custos, horizontes ou situações sem dados de saída.

## Token versus ETF

Na hipótese-base de custo, o token tem {number('token_rt_bps')} bps de ida e volta. Os cruzamentos são {number('GLD_crossing_months')} meses contra GLD e {number('GLDM_crossing_months')} meses contra GLDM. Taxas e spread mediano corrente dos ETFs são documentados; taxas, spread do token e conversão são hipóteses. O cálculo pressupõe USD, antes de impostos, mesma possibilidade de acesso e ausência de retirada na rota-base. O arquivo T3_custos_etfs.csv inclui mudanças de tamanho, custos fixos, taxas, spreads, armazenamento e casos sem cruzamento ou com reversão da vantagem.

## Evolução e cenários

A tendência foi estimada em {number('trend_n_quarters')} trimestres completos. A inclinação no log da mediana absoluta por ano foi {number('trend_beta_per_year')}, com intervalo de {number('trend_beta_lo')} a {number('trend_beta_hi')}. O intervalo inclui zero; não há demonstração estatística de melhora nesse desenho. Isso não é prova de ausência de melhora nem identifica competição ou infraestrutura como causas.

O método efetivamente aplicado aos cenários foi `{c['baseline_method']}`. O mínimo pré-definido de trajetórias conjuntas para reamostragem anual não foi reduzido para produzir um resultado mais atraente. Quando o gate falha, a saída é sensibilidade determinística; o ramo estocástico permanece implementado e testado com dados sintéticos de teste, que não aparecem como resultados de mercado.

Menor atrito mantém os caminhos de preço e reduz custos modelados, levando a média condicional a {number('lower_friction_mean_trade_model_before_unknown_carry_bps')} bps. O estresse hipotético altera preços e atritos e produz {number('stress_mean_trade_model_before_unknown_carry_bps')} bps. Esses cenários não são trajetórias prováveis ou datas previstas de maturidade.

## Limites que permanecem

OHLC de minuto não reconstrói livro, impacto ou latência real. Dados faltantes podem selecionar uma amostra diferente dos momentos mais difíceis de operar. Intervalos de reamostragem não cobrem custos omitidos ou erros de modelo. Custódia, resgate, elegibilidade e empréstimo são restrições documentais e específicas do participante. O trabalho informa uma decisão sob condições explícitas e não atribui causalidade à maturidade do mercado.
'''
    (ROOT/'results/INTERPRETACAO.md').write_text(interpretation,encoding='utf-8')
