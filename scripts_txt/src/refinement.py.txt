"""Retrospective extensions: paired changes, temporal forecasting and coverage."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from .common import ROOT, basis, dump_json, save_csv, save_frame, sha256, utc_now
from .statistics import block_indices
from .trades import build_trades
from .analysis import _pnl_for


def load_refinement():
    return json.loads((ROOT/'config/refinement.json').read_text(encoding='utf-8'))


def freeze_refinement(spec):
    baseline=json.loads((ROOT/'results/config_frozen.json').read_text(encoding='utf-8'))
    if baseline['config_hash']!=spec['baseline_config_hash']:
        raise ValueError('A extensão não corresponde à configuração-base preservada.')
    signature=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()
    path=ROOT/'results/refinement_config_frozen.json'
    if path.exists():
        snapshot=json.loads(path.read_text(encoding='utf-8'))
        if snapshot['config_hash']!=signature:
            raise ValueError('Configuração da extensão mudou após o congelamento; versionar a revisão.')
    else:
        dump_json(path,{'frozen_at_utc':utc_now(),'config_hash':signature,'config':spec,
                        'note':'Extensão retrospectiva posterior aos resultados v2; não é pré-registro independente.'})
    return signature


def calendar_interval(values, weeks, spec, statistic='mean'):
    """One value per calendar week, with missing weeks kept in block resampling."""
    s=pd.Series(np.asarray(values,dtype=float),index=pd.DatetimeIndex(weeks)).sort_index()
    if s.index.duplicated().any():
        raise ValueError('A comparação deve ter uma observação por semana.')
    function=np.nanmean if statistic=='mean' else np.nanmedian
    valid=s.notna().sum()
    if valid<12:
        return {'estimate':float(function(s)) if valid else np.nan,'lo':np.nan,'hi':np.nan,'n':int(valid),'status':'insufficient_weeks'}
    calendar=pd.date_range(s.index.min(),s.index.max(),freq='7D')
    values=s.reindex(calendar).to_numpy()
    b=spec['bootstrap']
    idx=block_indices(len(values),b['replicates'],b['block_calendar_weeks'],b['seed'])
    samples=function(values[idx],axis=1)
    finite=samples[np.isfinite(samples)]
    alpha=(1-b['confidence_level'])/2
    lo,hi=np.quantile(finite,[alpha,1-alpha])
    return {'estimate':float(function(values)),'lo':float(lo),'hi':float(hi),'n':int(valid),
            'calendar_weeks':len(calendar),'status':'exploratory_calendar_week_blocks'}


def paired_changes(weekends,spec):
    rows=[]
    for before,after in spec['paired']['comparisons']:
        valid=weekends.valid & weekends[[before,after]].notna().all(axis=1)
        change=(weekends[after].abs()-weekends[before].abs()).where(valid)
        out=calendar_interval(change,weekends.week,spec)
        med=calendar_interval(change,weekends.week,spec,'median')
        rows.append({'comparison':before+'_to_'+after,'before':before,'after':after,'paired_n':out['n'],
                     'mean_abs_change_bps':out['estimate'],'mean_lo':out['lo'],'mean_hi':out['hi'],
                     'median_within_week_change_bps':med['estimate'],'median_lo':med['lo'],'median_hi':med['hi'],
                     'fraction_abs_decreases':float(change.dropna().lt(0).mean()),
                     'inference':out['status'],'interpretation':'within_week_change_not_profit_not_causal'})
    table=pd.DataFrame(rows);save_csv(table,'T7_paired_changes.csv')
    return table


def forecast_dataset(hourly,weekends,spec):
    h=hourly.sort_values('bar_start').copy()
    log_price=np.log(h.S.where(h.valid))
    h['gold_r_bps']=(log_price.diff()*10000).where(h.bar_start.diff().eq(pd.Timedelta(hours=1)))
    c=spec['forecast'];rows=[]
    for w in weekends.itertuples():
        prior=h[(h.t<=w.t_0)&(h.t>w.t_0-pd.Timedelta(days=c['prior_volatility_calendar_days']))]
        returns=prior.gold_r_bps.dropna()
        vol=float(returns.std()) if len(returns)>=c['minimum_prior_volatility_returns'] else np.nan
        rows.append({'id':w.id,'week':w.week,'t_decision':w.t_0+pd.Timedelta(hours=1),
                     't_target':w.t_0+pd.Timedelta(hours=7),'last_vol_observation':prior.t.max() if len(prior) else pd.NaT,
                     'calendar_valid':bool(w.valid),'b_1h':w.b_1h,'g':w.g,'log_prior_gold_vol':np.log(vol) if vol>0 else np.nan,
                     'actual':w.b_7h})
    frame=pd.DataFrame(rows)
    cols=[*c['context_features'],'actual']
    frame['complete']=frame.calendar_valid & np.isfinite(frame[cols]).all(axis=1)
    return frame


def linear_prediction(train,test,features):
    """OLS with a training-only scaling; no model or hyperparameter selection."""
    x=train[features].to_numpy(dtype=float)
    means=x.mean(axis=0);scales=x.std(axis=0)
    scales=np.where(scales>1e-12,scales,1.)
    design=np.column_stack([np.ones(len(x)),(x-means)/scales])
    coef=np.linalg.lstsq(design,train.actual.to_numpy(dtype=float),rcond=None)[0]
    row=np.r_[1.,(test[features].to_numpy(dtype=float)-means)/scales]
    raw_coef=coef[1:]/scales
    parameters={'intercept':float(coef[0]-np.sum(raw_coef*means)),**dict(zip(features,map(float,raw_coef)))}
    return float(row@coef),parameters


def expanding_forecasts(frame,spec):
    c=spec['forecast'];rows=[];coefficients=[]
    frame=frame.sort_values('week').reset_index(drop=True)
    for position in range(c['initial_training_calendar_weeks'],len(frame)):
        test=frame.iloc[position]
        train=frame.iloc[:position]
        train=train[train.complete & train.t_target.lt(test.t_decision)]
        valid=bool(test.complete and len(train)>=c['minimum_training_observations'])
        for model in c['models']:
            prediction=np.nan
            if valid:
                if model=='persistence':prediction=float(test.b_1h)
                elif model=='zero_basis':prediction=0.
                elif model=='historical_mean':prediction=float(train.actual.mean())
                else:
                    features=c['linear_features'] if model=='linear_adjustment' else c['context_features']
                    prediction,params=linear_prediction(train,test,features)
                    coefficients.append({'id':test.id,'week':test.week,'model':model,'train_n':len(train),**params})
            error=float(test.actual-prediction) if valid else np.nan
            rows.append({'id':test.id,'week':test.week,'model':model,'t_decision':test.t_decision,'t_target':test.t_target,
                         'train_last_target':train.t_target.max() if len(train) else pd.NaT,
                         'train_n':len(train),'evaluated':valid,'actual':float(test.actual) if pd.notna(test.actual) else np.nan,
                         'prediction':prediction,'absolute_error_bps':abs(error),'squared_error':error**2,
                         'status':'retrospective_temporal_validation_not_untouched_prospective_holdout'})
    return pd.DataFrame(rows),pd.DataFrame(coefficients)


def forecast_summary(predictions,spec):
    pivot=predictions.pivot(index='week',columns='model',values='absolute_error_bps')
    common=pivot.notna().all(axis=1)
    rows=[]
    for model,g in predictions.groupby('model',sort=False):
        g=g.set_index('week').sort_index()
        good=g.evaluated & g.index.isin(pivot.index[common])
        losses=g.absolute_error_bps.where(good)
        delta=losses-pivot.persistence.reindex(g.index)
        ci=calendar_interval(delta,g.index,spec)
        persistence=float(pivot.loc[common,'persistence'].mean())
        rows.append({'model':model,'n_test':int(good.sum()),'mae_bps':float(losses.mean()),
                     'rmse_bps':float(np.sqrt(g.loc[good,'squared_error'].mean())),
                     'mae_skill_vs_persistence':1-float(losses.mean())/persistence,
                     'mae_difference_vs_persistence':ci['estimate'],'difference_lo':ci['lo'],'difference_hi':ci['hi'],
                     'first_test_week':str(g.index[good].min()),'last_test_week':str(g.index[good].max()),
                     'ci_status':ci['status'],'economic_profit_claim':False})
    return pd.DataFrame(rows)


def align_completed_fx(minutes,max_age_minutes):
    """A 1-minute window exactly reproduces the original minute match.

    Age counts from the source minute start. A 5-minute window can carry a
    completed FX close for at most four minutes, never a future close.
    Token and gold observations are not carried.
    """
    if max_age_minutes<1:raise ValueError('A janela deve conter pelo menos uma barra de minuto.')
    out=minutes.sort_values('bar_start').copy()
    observed=out.loc[out.fx_active.eq(True)&out.q_close.gt(0),['bar_start','q_close']]
    observed=observed.rename(columns={'bar_start':'fx_used_bar_start','q_close':'fx_used_close'})
    out=pd.merge_asof(out,observed,left_on='bar_start',right_on='fx_used_bar_start',
                      tolerance=pd.Timedelta(minutes=max_age_minutes-1),direction='backward')
    out['fx_original_active']=out.fx_active
    out['fx_used_available_at']=out.fx_used_bar_start+pd.Timedelta(minutes=1)
    out['fx_bar_age_minutes']=(out.bar_end-out.fx_used_bar_start).dt.total_seconds()/60
    out['fx_close_age_minutes']=(out.bar_end-out.fx_used_available_at).dt.total_seconds()/60
    out['q_close']=out.fx_used_close
    out['fx_active']=out.fx_used_close.notna()
    out['close_valid']=out.token_active.eq(True)&out.gold_active.eq(True)&out.fx_active
    out['basis_close_log_bps']=np.where(out.close_valid,basis(out.p_close,out.q_close,out.mid_close),np.nan)
    return out


def currency_sensitivity(config,minutes,weekends,spec):
    tables=[];ledgers=[]
    for age in spec['currency_age_sensitivity']['max_age_minutes']:
        aligned=align_completed_fx(minutes,age)
        trades=build_trades(config,aligned,weekends)
        for name,values in _pnl_for(trades,config['convergence']['baseline']).items():
            trades[name]=np.where(trades.path_valid,values,np.nan)
        lookup=aligned.set_index('bar_start')
        for event,column in [('signal','t_signal'),('entry','t_in'),('exit','t_out')]:
            idx=pd.DatetimeIndex(trades[column]-pd.Timedelta(minutes=1))
            for field in ['fx_used_bar_start','fx_used_available_at','fx_bar_age_minutes','fx_close_age_minutes']:
                trades[event+'_'+field]=lookup[field].reindex(idx).to_numpy()
        trades['fx_window_minutes']=age;ledgers.append(trades)
        for horizon,g in trades.groupby('horizon_hours'):
            good=g.evaluated_trade
            v=g.loc[good,'after_modeled_before_unknown_carry_bps']
            tables.append({'fx_window_minutes':age,'horizon_hours':horizon,'calendar_weeks':len(g),
                           'valid_paths':int(g.path_valid.sum()),'signals':int((g.calendar_valid&g.signal_eligible).sum()),
                           'evaluated_trades':int(good.sum()),'unassessed_signals':int((g.calendar_valid&g.signal_eligible&~g.path_valid).sum()),
                           'mean_gross_bps':float(g.loc[good,'gross_mid_bps'].mean()),'mean_model_bps':float(v.mean()),
                           'positive_fraction':float(v.gt(0).mean()),'max_completed_fx_carry_minutes':age-1,
                           'scope':'alignment_sensitivity_not_executable_prices_not_primary_replacement'})
    all_trades=pd.concat(ledgers,ignore_index=True)
    save_frame(all_trades,ROOT/'data/panel/trades_fx_sensitivity.parquet')
    # Contains provider quotes: local only, excluded from the delivery archive.
    save_csv(all_trades,'T9_fx_trade_ledger.csv')
    table=pd.DataFrame(tables);save_csv(table,'T9_fx_coverage.csv')
    common=[]
    for horizon in sorted(all_trades.horizon_hours.unique()):
        subset=all_trades[all_trades.horizon_hours.eq(horizon)]
        evaluated=[set(g.loc[g.evaluated_trade,'id']) for _,g in subset.groupby('fx_window_minutes')]
        ids=set.intersection(*evaluated)
        for age,g in subset.groupby('fx_window_minutes'):
            good=g[g.id.isin(ids)]
            common.append({'horizon_hours':horizon,'fx_window_minutes':age,'same_sample_n':len(good),
                           'mean_model_bps':float(good.after_modeled_before_unknown_carry_bps.mean()),
                           'mean_gross_bps':float(good.gross_mid_bps.mean())})
    save_csv(pd.DataFrame(common),'T9_fx_common_sample.csv')
    return table,all_trades


def missingness_sensitivity(trades,spec):
    rows=[];summary=[]
    for horizon,g in trades.groupby('horizon_hours'):
        evaluated=g[g.evaluated_trade]
        n=len(evaluated);missing=int((g.calendar_valid&g.signal_eligible&~g.path_valid).sum())
        total=float(evaluated.after_modeled_before_unknown_carry_bps.sum())
        required=-total/missing if missing else np.nan
        summary.append({'horizon_hours':horizon,'evaluated_trades':n,'unassessed_signals':missing,
                        'observed_mean_model_bps':total/n if n else np.nan,
                        'required_unassessed_mean_to_break_even_bps':required,
                        'scope':'only_observed_eligible_signals_not_weeks_with_missing_signal'})
        for assumed in spec['missingness']['assumed_unassessed_mean_bps']:
            rows.append({'horizon_hours':horizon,'assumed_unassessed_mean_bps':assumed,
                         'hypothetical_all_signals_mean_bps':(total+missing*assumed)/(n+missing) if n+missing else np.nan,
                         'evaluated_trades':n,'unassessed_signals':missing,'assumption_not_imputation':True})
    summary=pd.DataFrame(summary);save_csv(summary,'T9_missingness_summary.csv')
    save_csv(pd.DataFrame(rows),'T9_missingness_scenarios.csv')
    return summary


def economic_frontier(trades,spec):
    rows=[]
    for horizon,g in trades.groupby('horizon_hours'):
        g=g[g.evaluated_trade]
        gross=float(g.gross_mid_bps.mean())
        costs=float((g.gross_mid_bps-g.after_modeled_before_unknown_carry_bps).mean())
        ci=calendar_interval(g.gross_mid_bps,g.week,spec)
        rows.append({'horizon_hours':horizon,'n':len(g),'mean_gross_bps':gross,'gross_lo':ci['lo'],'gross_hi':ci['hi'],
                     'mean_modeled_cost_bps':costs,'mean_model_bps':gross-costs,
                     'accounting_cost_reduction_to_zero_fraction':1-gross/costs if costs>0 else np.nan,
                     'scope':'sample_mean_cost_budget_not_forecast_or_realizable_return'})
    table=pd.DataFrame(rows);save_csv(table,'T10_cost_budget.csv')
    grid=pd.read_csv(ROOT/'results/T2_convergencia.csv')
    summary=grid.groupby('horizon_hours').agg(configurations=('mean_model_bps','size'),
             positive_mean_configurations=('mean_model_bps',lambda s:int(s.gt(0).sum())),
             best_mean_model_bps=('mean_model_bps','max'),worst_mean_model_bps=('mean_model_bps','min'),
             evaluated_trades=('evaluated_trades','first')).reset_index()
    save_csv(summary,'T10_grid_summary.csv')
    return table,summary


def validate_refinement(original,forecasts,aligned,fx_table,spec):
    first=aligned[aligned.fx_window_minutes.eq(1)].sort_values(['id','horizon_hours'])
    original=original.sort_values(['id','horizon_hours'])
    present=forecasts[forecasts.evaluated]
    checks={
        'one_minute_ids_match_original':first[['id','horizon_hours']].reset_index(drop=True).equals(original[['id','horizon_hours']].reset_index(drop=True)),
        'one_minute_selection_matches_original':np.array_equal(first.evaluated_trade,original.evaluated_trade),
        'one_minute_pnl_matches_original':bool(np.allclose(first.after_modeled_before_unknown_carry_bps,original.after_modeled_before_unknown_carry_bps,equal_nan=True,atol=1e-8)),
        'forecast_train_targets_before_decision':bool((present.train_last_target<present.t_decision).all()),
        'forecast_target_after_decision':bool((present.t_target>present.t_decision).all()),
        'all_models_same_test_sample':bool(present.groupby('model').week.apply(tuple).map(hash).nunique()==1),
        'no_unknown_financing_replaced_by_zero':bool(aligned.net_if_residual_assumed_bps.isna().all()),
        'no_annual_gate_lowered':not spec['currency_age_sensitivity']['enables_annual_simulation'],
        'no_path_selected_on_profit':bool(aligned.evaluated_trade.eq(aligned.path_valid&aligned.signal_eligible).all()),
    }
    for event,clock in [('signal','t_signal'),('entry','t_in'),('exit','t_out')]:
        at=aligned[event+'_fx_used_available_at'];age=aligned[event+'_fx_bar_age_minutes']
        known=at.notna()
        checks[event+'_fx_never_future']=bool((at[known]<=aligned.loc[known,clock]).all())
        checks[event+'_fx_bounded_age']=bool(((age[known]>=1)&(age[known]<=aligned.loc[known,'fx_window_minutes'])).all())
    failed=[name for name,passed in checks.items() if not passed]
    report={'status':'passed' if not failed else 'failed','at_utc':utc_now(),'checks':checks,'failed':failed,
            'extension_status':spec['research_status'],'source_code_sha256':sha256(Path_this())}
    dump_json(ROOT/'results/QA_refinement.json',report)
    if failed:raise ValueError('Integridade da extensão: '+', '.join(failed))
    return report


def Path_this():
    from pathlib import Path
    return Path(__file__)


def append_claims(paired,models,fx,missing,budget,grid):
    claims=pd.read_csv(ROOT/'results/claims.csv')
    claims=claims[~claims.claim_id.str.startswith('refined_')]
    additions=[]
    def add(key,value,source,unit='bps',sample='retrospective_extension'):
        additions.append({'claim_id':'refined_'+key,'value':value,'unit':unit,'source_file':'results/'+source,
                          'sample':sample,'assumptions':'post_original_analysis; conditional; no causal or executable claim'})
    for name in ['b_0_to_b_1h','b_0_to_b_7h']:
        r=paired[paired.comparison.eq(name)].iloc[0]
        for col in ['mean_abs_change_bps','mean_lo','mean_hi','paired_n']:add(name+'_'+col,r[col],'T7_paired_changes.csv')
    for name in ['persistence','zero_basis','historical_mean','linear_adjustment','linear_adjustment_context']:
        r=models[models.model.eq(name)].iloc[0]
        for col in ['mae_bps','rmse_bps','mae_skill_vs_persistence','mae_difference_vs_persistence','difference_lo','difference_hi','n_test']:
            add(name+'_'+col,r[col],'T8_forecast_summary.csv')
    for age in [1,5]:
        r=fx[fx.fx_window_minutes.eq(age)&fx.horizon_hours.eq(6)].iloc[0]
        for col in ['valid_paths','signals','evaluated_trades','unassessed_signals','mean_model_bps','positive_fraction']:
            add('fx'+str(age)+'_'+col,r[col],'T9_fx_coverage.csv')
    r=missing[missing.horizon_hours.eq(6)].iloc[0]
    add('missing_tipping_mean_bps',r.required_unassessed_mean_to_break_even_bps,'T9_missingness_summary.csv')
    r=budget[budget.horizon_hours.eq(6)].iloc[0]
    add('cost_reduction_to_zero_fraction',r.accounting_cost_reduction_to_zero_fraction,'T10_cost_budget.csv','fraction')
    add('grid_configurations',int(grid.configurations.sum()),'T10_grid_summary.csv','count')
    add('grid_positive_means',int(grid.positive_mean_configurations.sum()),'T10_grid_summary.csv','count')
    add('grid_best_mean_bps',float(grid.best_mean_model_bps.max()),'T10_grid_summary.csv')
    result=pd.concat([claims,pd.DataFrame(additions)],ignore_index=True)
    save_csv(result,'claims.csv')
    summary=json.loads((ROOT/'results/summary.json').read_text(encoding='utf-8'))
    summary.update({r['claim_id']:r['value'] for r in additions})
    dump_json(ROOT/'results/summary.json',summary)
    result_path=ROOT/'results/RESULTS.md'
    base=result_path.read_text(encoding='utf-8').split('\n## Extensão v3')[0]
    heading='\n## Extensão v3 — retrospectiva\n\n| Indicador | Valor | Fonte |\n| --- | ---: | --- |\n'
    body='\n'.join(f"| {row['claim_id']} | {row['value']:.6g} | {row['source_file']} |" for row in additions)
    result_path.write_text(base+heading+body+'\n',encoding='utf-8')


def run_refinement(config):
    spec=load_refinement();signature=freeze_refinement(spec)
    w=pd.read_parquet(ROOT/'data/panel/panel_weekends.parquet')
    h=pd.read_parquet(ROOT/'data/panel/panel_hourly.parquet')
    m=pd.read_parquet(ROOT/'data/panel/panel_minutes.parquet')
    original=pd.read_parquet(ROOT/'data/panel/trades_A.parquet')
    paired=paired_changes(w,spec)
    dataset=forecast_dataset(h,w,spec)
    predictions,coefficients=expanding_forecasts(dataset,spec)
    save_csv(dataset,'T8_forecast_dataset.csv')
    save_csv(predictions,'T8_forecast_predictions.csv')
    save_csv(coefficients,'T8_forecast_coefficients.csv')
    models=forecast_summary(predictions,spec);save_csv(models,'T8_forecast_summary.csv')
    fx,aligned=currency_sensitivity(config,m,w,spec)
    missing=missingness_sensitivity(original,spec)
    budget,grid=economic_frontier(original,spec)
    validate_refinement(original,predictions,aligned,fx,spec)
    append_claims(paired,models,fx,missing,budget,grid)
    write_interpretation(paired,models,fx,missing,budget,grid)
    dump_json(ROOT/'results/refinement_status.json',{'status':'completed','at_utc':utc_now(),'config_hash':signature,
              'outputs':['T7_paired_changes.csv','T8_forecast_summary.csv','T9_fx_coverage.csv','T9_missingness_summary.csv','T10_cost_budget.csv'],
              'note':'Original parameters and original analytical tables retained; extensions are retrospective.'})
    print('Extensão: contrastes pareados, cinco previsões temporais, alinhamento cambial e sensibilidade econômica concluídos.',flush=True)


def write_interpretation(paired,models,fx,missing,budget,grid):
    rows=paired[['comparison','paired_n','mean_abs_change_bps','mean_lo','mean_hi']].to_string(index=False)
    model=models[['model','n_test','mae_bps','rmse_bps','mae_skill_vs_persistence','difference_lo','difference_hi']].to_string(index=False)
    coverage=fx[fx.horizon_hours.eq(6)][['fx_window_minutes','valid_paths','evaluated_trades','unassessed_signals','mean_model_bps']].to_string(index=False)
    tip=missing[missing.horizon_hours.eq(6)].iloc[0]
    primary=models[models.model.eq('linear_adjustment')].iloc[0]
    interpretation='melhora observada de MAE frente à persistência' if primary.mae_skill_vs_persistence>0 else 'ausência de melhora de MAE frente à persistência'
    content=f'''# Refinamento da tese e resultados v3

Extensão retrospectiva: os resultados originais já haviam sido examinados. Os parâmetros próprios foram congelados antes desta execução. A validação temporal não é um holdout prospectivo intocado. Ver auditoria/MODELAGEM_REVISAO.md.

## Problema e tese

O acesso 24/7 separa a possibilidade de negociar do custo de acompanhar e capturar uma referência. Medimos fidelidade, ajuste após a reabertura, previsibilidade temporal e condições econômicas. Previsibilidade não comprova execução, arbitragem sem risco ou a causa do comportamento dos preços.

## Contrastes dentro dos mesmos fins de semana

Valores negativos indicam queda do desvio absoluto. São médias de diferenças dentro de cada semana, não diferenças entre medianas independentes. Intervalos de 95% são exploratórios, em blocos de semanas do calendário, e não cobrem seleção por dados faltantes ou erro de mensuração.

```text
{rows}
```

## Modelo e validação

O alvo é o desvio em +7h, observado após a decisão em +1h. O treino começa com 104 semanas de calendário e cresce usando apenas alvos já concluídos. O modelo principal é um ajuste linear com b_1h; a alternativa com contexto acrescenta o salto do ouro e volatilidade anterior. Todas as cinco previsões usam a mesma amostra de teste. Resultado principal: {interpretation}. Uma diferença de MAE abaixo de zero favorece o modelo; o intervalo e as referências simples devem ser considerados em conjunto.

```text
{model}
```

## Alinhamento cambial e amostra

Janelas de busca de 1 e 5 minutos usam closes observados de câmbio já concluídos. A janela de cinco permite carregar um close concluído por até quatro minutos. Token e ouro permanecem no minuto exato de execução e com atividade. A janela de um minuto reproduz numericamente o resultado original. A alternativa não substitui o primário nem habilita cenários anuais. T9_fx_common_sample.csv separa o efeito sobre a mesma amostra do efeito de incluir novas trajetórias.

```text
{coverage}
```

## Ausências e economia

Para zerar a média agregada dos {int(tip.evaluated_trades+tip.unassessed_signals)} sinais observados elegíveis em 6h, os {int(tip.unassessed_signals)} não avaliados precisariam ter saldo médio de {tip.required_unassessed_mean_to_break_even_bps:.2f} bps. Não atribuímos esse saldo a eles. Esse exercício não cobre as semanas sem sinal observável, nem identifica o mecanismo das ausências.

A grade original tem {int(grid.configurations.sum())} combinações e {int(grid.positive_mean_configurations.sum())} médias positivas. A melhor média é {grid.best_mean_model_bps.max():.2f} bps, escolhida retrospectivamente da grade, e não uma estratégia validada para uso futuro. Orçamento de custo e reduções necessárias são identidades contábeis da média amostral; não previsões. Custos financeiros e acesso a empréstimo continuam desconhecidos.

## O que a extensão muda

O trabalho passa a distinguir ajuste observado, capacidade de prever e capacidade de executar. O modelo acrescenta uma comparação temporal verificável, inclusive quando não supera uma referência. O estudo permanece específico a PAXG e às fontes disponíveis. Não há conclusão causal sobre infraestrutura/competição, auditoria de reservas ou previsão de amadurecimento. Custos de manutenção e horizontes contra ETFs continuam condicionais à rota, às taxas e ao armazenamento.
'''
    (ROOT/'results/REFINAMENTO.md').write_text(content,encoding='utf-8')
