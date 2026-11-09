"""Painéis de preços, calendário explícito e sinais disponíveis no passado."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from .common import ROOT, basis, dump_json, finite_or_none, save_csv, save_frame, week_start


def gold_open_mask(times):
    ny = pd.DatetimeIndex(times).tz_convert('America/New_York')
    day, hour = ny.weekday, ny.hour
    return ((day < 4) & (hour != 17)) | ((day == 4) & (hour < 17)) | ((day == 6) & (hour >= 18))


def gold_active(frame):
    return frame.quote_active & frame.valid_quotes & gold_open_mask(frame.bar_start)


def scheduled_reopen(date):
    date = pd.Timestamp(date)
    return pd.Timestamp(f'{date:%Y-%m-%d} 18:00', tz='America/New_York').tz_convert('UTC')


def _read(name):
    return pd.read_parquet(ROOT / 'data/interim' / name)


def build_hourly(token, gold, fx, config):
    start, end = pd.Timestamp(config['data']['start_utc']), pd.Timestamp(config['data']['end_exclusive_utc'])
    grid = pd.date_range(start, end, inclusive='left', freq='h')
    grid = grid[gold_open_mask(grid)]
    out = pd.DataFrame({'bar_start': grid})
    t = token[['bar_start', 'close', 'quote_volume_quote_ccy', 'has_trade']].rename(columns={'close': 'p_usdt', 'has_trade': 'token_has_trade'})
    g = gold[['bar_start', 'mid_close', 'spread_close_bps', 'quote_active', 'valid_quotes']].rename(columns={'mid_close': 'S'})
    q = fx[['bar_start', 'close', 'has_trade']].rename(columns={'close': 'q', 'has_trade': 'fx_has_trade'})
    for frame in (t, g, q):
        out = out.merge(frame, on='bar_start', how='left', validate='one_to_one')
    out['t'] = out.bar_start + pd.Timedelta(hours=1)
    out['valid'] = out.token_has_trade.eq(True) & out.fx_has_trade.eq(True) & out.quote_active.eq(True) & out.valid_quotes.eq(True)
    out['p_usd'] = out.p_usdt * out.q
    out['basis_log_bps'] = np.where(out.valid, basis(out.p_usdt, out.q, out.S), np.nan)
    out['vol_token_usd'] = out.quote_volume_quote_ccy * out.q
    out['currency_method'] = 'observed_bitfinex_usdt_usd'
    out['source'] = 'Binance|Bitfinex|Dukascopy'
    out['resolution'] = '1h'
    out['download_id'] = 'data/raw/manifest.jsonl'
    out['alignment_gap_seconds'] = 0
    out['price_age_status'] = 'unknown_within_one_hour_bar'
    out['week'] = week_start(out.t)
    out['exclusion_reason'] = np.select([
        ~out.token_has_trade.eq(True), ~out.fx_has_trade.eq(True), ~out.quote_active.eq(True), ~out.valid_quotes.eq(True)
    ], ['token_missing_or_no_trade', 'fx_missing_or_no_trade', 'gold_missing_or_inactive', 'invalid_gold_quotes'], default='')
    return out


def build_weekends(token, gold, fx, config):
    t, q = token.set_index('bar_start'), fx.set_index('bar_start')
    g = gold.loc[gold_active(gold)].set_index('bar_start').sort_index()
    index = g.index
    dates = pd.date_range(config['data']['first_candidate_reopen_date'], config['data']['last_candidate_reopen_date'], freq='W-SUN', tz='UTC')

    def row(frame, at):
        return frame.loc[at] if at in frame.index else None

    def token_price(at):
        r = row(t, at)
        return float(r.close) if r is not None and r.has_trade else np.nan

    def fx_price(at):
        r = row(q, at)
        return float(r.close) if r is not None and r.has_trade else np.nan

    def point(at):
        # Closes da hora anterior, sem preencher barras ausentes.
        r = row(g, at - pd.Timedelta(hours=1))
        s = float(r.mid_close) if r is not None else np.nan
        return float(basis(token_price(at-pd.Timedelta(hours=1)), fx_price(at-pd.Timedelta(hours=1)), s))

    result = []
    for date in dates:
        expected_open = scheduled_reopen(date)
        fri = date - pd.Timedelta(days=2)
        expected_close = pd.Timestamp(f'{fri:%Y-%m-%d} 17:00', tz='America/New_York').tz_convert('UTC')
        pos = index.searchsorted(expected_open)
        available = pos < len(index) and pos > 0
        t0 = index[pos] if available else pd.NaT
        tc = index[pos-1] + pd.Timedelta(hours=1) if available else pd.NaT
        regular = available and t0 == expected_open and tc == expected_close
        gap = (t0-tc).total_seconds()/3600 if available else np.nan
        if not available:
            status = 'missing_reopen'
        elif regular:
            status = 'regular_calendar'
        elif t0 != expected_open:
            status = 'reopen_delayed_or_holiday_unverified'
        else:
            status = 'early_close_or_holiday_unverified'
        valid_gap = available and config['alignment']['candidate_gap_min_hours'] < gap <= config['alignment']['candidate_gap_max_hours']
        if available:
            sc = float(g.iloc[pos-1].mid_close)
            s0 = float(g.iloc[pos].mid_open)
            pc, qc = token_price(tc-pd.Timedelta(hours=1)), fx_price(tc-pd.Timedelta(hours=1))
            p0, q0 = token_price(t0-pd.Timedelta(hours=1)), fx_price(t0-pd.Timedelta(hours=1))
        else:
            sc=s0=pc=qc=p0=q0=np.nan
        bc, b0 = float(basis(pc,qc,sc)), float(basis(p0,q0,s0))
        gw = 10000*np.log(s0/sc) if sc>0 and s0>0 else np.nan
        mw = 10000*np.log((p0*q0)/(pc*qc)) if min(pc,qc,p0,q0)>0 else np.nan
        valid = bool(regular and valid_gap and np.isfinite([bc,b0,gw,mw]).all())
        result.append({'id': f'{date:%Y-%m-%d}', 'week': date, 'expected_t_0': expected_open,
                       't_c': tc, 't_0': t0, 't_e': t0+pd.Timedelta(hours=1) if available else pd.NaT,
                       'S_c':sc,'S_0':s0,'p_c':pc,'p_0':p0,'q_c':qc,'q_0':q0,
                       'b_c':bc,'b_0':b0,'g':gw,'m':mw,
                       'b_1h':point(t0+pd.Timedelta(hours=1)) if available else np.nan,
                       'b_7h':point(t0+pd.Timedelta(hours=7)) if available else np.nan,
                       'gap_hours':gap,'calendar_status':status,'valid':valid,
                       'identity_residual_bps':b0-bc-mw+gw,
                       'currency_method':'observed_bitfinex_usdt_usd','source':'Binance|Bitfinex|Dukascopy',
                       'resolution':'1h','download_id':'data/raw/manifest.jsonl'})
    out = pd.DataFrame(result)
    historical = out.g.where(out.valid).abs()
    out['stress_threshold'] = historical.shift(1).rolling(config['analysis']['stress_lookback_weekends'], min_periods=config['analysis']['stress_min_history_weekends']).quantile(config['analysis']['stress_threshold_quantile'])
    out['stress_flag'] = np.where(out.stress_threshold.notna() & out.valid, out.g.abs()>out.stress_threshold, None)
    out['exclusion_reason'] = np.where(out.valid, '', np.where(out.calendar_status.ne('regular_calendar'), out.calendar_status, 'missing_price_or_conversion'))
    return out


def coverage_table(token, gold, fx, hourly, config):
    rows=[]
    end=pd.Timestamp(config['data']['end_exclusive_utc'])
    start=pd.Timestamp(config['data']['start_utc'])
    for name,frame,active in [('Binance PAXGUSDT',token,token.has_trade),('Bitfinex USDTUSD',fx,fx.has_trade),('Dukascopy XAUUSD',gold,gold_active(gold))]:
        for month in pd.date_range(start.normalize().replace(day=1),end,freq='MS',tz='UTC'):
            a=max(month,start); b=min(month+pd.offsets.MonthBegin(1),end)
            expected=pd.date_range(a,b,freq='h',inclusive='left')
            if name.startswith('Dukascopy'):
                expected=expected[gold_open_mask(expected)]
            take=(frame.bar_start>=a)&(frame.bar_start<b)
            rows.append({'source':name,'month':f'{month:%Y-%m}','expected_scheduled_upper_bound':len(expected),'received':int(take.sum()),'active':int((take&active).sum()),'inactive_or_no_trade':int((take&~active).sum())})
    cov=pd.DataFrame(rows)
    cov['coverage_active_fraction']=cov.active/cov.expected_scheduled_upper_bound.replace(0,np.nan)
    return cov


def manual_audit(weekends, token, gold, fx, config):
    valid=weekends[weekends.valid]
    if len(valid)<3:
        raise ValueError('Menos de três fins de semana válidos.')
    chosen=[valid.b_0.abs().idxmax(),valid.index[-1],valid.sample(n=1,random_state=config['analysis']['bootstrap_seed']).index[0]]
    rows=[]
    for idx in chosen:
        r=weekends.loc[idx]
        independent=10000*math.log(float(r.p_0)*float(r.q_0)/float(r.S_0))
        rows.append({'id':r.id,'t_c':r.t_c,'t_0':r.t_0,'S_c':r.S_c,'S_0':r.S_0,'p_0':r.p_0,'q_0':r.q_0,'basis_recalculated':independent,'basis_panel':r.b_0,'difference_bps':independent-r.b_0,'identity_residual_bps':r.identity_residual_bps,'selection':''})
    for r,label in zip(rows,['largest_dislocation','latest_DST_case','seeded_sample']):
        r['selection']=label
    audit=pd.DataFrame(rows)
    if audit.difference_bps.abs().max()>1e-8 or audit.identity_residual_bps.abs().max()>1e-8:
        raise ValueError('Auditoria aritmética do painel falhou.')
    save_csv(audit,'QA_three_weekends.csv')


def build_panels(config):
    token,gold,fx=_read('token_1h.parquet'),_read('gold_1h.parquet'),_read('fx_1h.parquet')
    hourly=build_hourly(token,gold,fx,config)
    weekends=build_weekends(token,gold,fx,config)
    save_frame(hourly,ROOT/'data/panel/panel_hourly.parquet')
    save_frame(weekends,ROOT/'data/panel/panel_weekends.parquet')
    save_csv(coverage_table(token,gold,fx,hourly,config),'coverage.csv')
    excluded=hourly.loc[~hourly.valid,['t','exclusion_reason']].rename(columns={'t':'row_id'})
    excluded['analysis']='hourly'
    w=weekends.loc[~weekends.valid,['id','exclusion_reason']].rename(columns={'id':'row_id'})
    w['analysis']='weekends'
    save_csv(pd.concat([excluded,w],ignore_index=True),'exclusions.csv')
    comparison=_read('fx_coinbase_validation.parquet').merge(fx[['bar_start','close']],on='bar_start',suffixes=('_coinbase','_bitfinex'))
    comparison['difference_log_bps']=10000*np.log(comparison.close_bitfinex/comparison.close_coinbase)
    save_csv(comparison[['bar_start','close_coinbase','close_bitfinex','difference_log_bps']],'QA_fx_source_comparison.csv')
    manual_audit(weekends,token,gold,fx,config)
    dump_json(ROOT/'results/panel_status.json',{'calendar_candidates':len(weekends),'valid_weekends':int(weekends.valid.sum()),'scheduled_hourly_rows':len(hourly),'valid_hourly_rows':int(hourly.valid.sum()),'fx_comparison_hours':len(comparison),'fx_median_abs_difference_bps':finite_or_none(comparison.difference_log_bps.abs().median()),'calendar_note':'Horário regular NY 18h domingo/17h sexta; exceções sem calendário documental completo excluídas do primário.'})
    print(f'Painéis: {int(hourly.valid.sum()):,} horas válidas; {int(weekends.valid.sum())}/{len(weekends)} fins de semana válidos',flush=True)
    return hourly,weekends


def build_minute_panels(config):
    token,gold,fx=_read('token_1m.parquet'),_read('gold_1m.parquet'),_read('fx_1m.parquet')
    gold['calendar_open']=gold_open_mask(gold.bar_start)
    out=token[['bar_start','bar_end','open','close','has_trade','quote_volume_quote_ccy']].rename(columns={'open':'p_open','close':'p_close','has_trade':'token_active'})
    out=out.merge(gold[['bar_start','bid_open','bid_close','ask_open','ask_close','mid_open','mid_close','quote_active','valid_quotes','calendar_open','spread_open_bps']],on='bar_start',how='outer',validate='one_to_one')
    out=out.merge(fx[['bar_start','open','close','has_trade']].rename(columns={'open':'q_open','close':'q_close','has_trade':'fx_active'}),on='bar_start',how='outer',validate='one_to_one')
    weekends=pd.read_parquet(ROOT/'data/panel/panel_weekends.parquet').tail(config['convergence']['recent_window_weeks'])
    keep=np.zeros(len(out),dtype=bool)
    for r in weekends.itertuples():
        keep|=(out.bar_start>=r.t_0-pd.Timedelta(minutes=6))&(out.bar_start<=r.t_0+pd.Timedelta(hours=25,minutes=6))
    out=out.loc[keep].sort_values('bar_start').reset_index(drop=True)
    out['bar_end']=out.bar_start+pd.Timedelta(minutes=1)
    out['gold_active']=out.quote_active.eq(True)&out.valid_quotes.eq(True)&out.calendar_open.eq(True)
    out['close_valid']=out.token_active.eq(True)&out.fx_active.eq(True)&out.gold_active
    out['basis_close_log_bps']=np.where(out.close_valid,basis(out.p_close,out.q_close,out.mid_close),np.nan)
    out['source']='Binance|Bitfinex|Dukascopy'
    out['resolution']='1min'
    out['download_id']='data/raw/manifest.jsonl'
    out['price_age_status']='OHLC_proxy_within_one_minute_not_ticks'
    save_frame(out,ROOT/'data/panel/panel_minutes.parquet')
    print(f'Painel de minutos: {len(out):,} linhas; {int(out.close_valid.sum()):,} closes conjuntos válidos',flush=True)
    return out
