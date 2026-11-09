"""Sinais e trajetórias de minuto; nenhuma seleção por resultado futuro."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .common import ROOT,basis,save_frame,save_csv


def minute_close(frame,at,tolerance=1):
    """Último close de barra concluída, com idade máxima explícita."""
    at=pd.Timestamp(at)
    candidates=frame.loc[(frame.index+pd.Timedelta(minutes=1)<=at)&(frame.index>=at-pd.Timedelta(minutes=tolerance))]
    valid=candidates[candidates.close_valid]
    return valid.iloc[-1] if len(valid) else None


def signal_at(frame,at,threshold,tolerance=1):
    r=minute_close(frame,at,tolerance)
    if r is None:
        return {'signal_available':False,'signal_basis_bps':np.nan,'side':np.nan,'signal_eligible':False,'signal_price_at':pd.NaT}
    b=float(basis(r.p_close,r.q_close,r.mid_close))
    return {'signal_available':True,'signal_basis_bps':b,'side':float(np.sign(b)),
            'signal_eligible':bool(abs(b)>=threshold),'signal_price_at':r.bar_end}


def execution_at(frame,at):
    # Open do minuto seguinte: proxy predeterminada. Q é sempre da barra concluída anterior.
    if at not in frame.index:
        return None
    r=frame.loc[at]
    prior=frame.loc[at-pd.Timedelta(minutes=1)] if at-pd.Timedelta(minutes=1) in frame.index else None
    if not (r.token_active==True and r.gold_active==True and prior is not None and prior.fx_active==True):
        return None
    return {'P':float(r.p_open*prior.q_close),'S':float(r.mid_open),'bid':float(r.bid_open),
            'ask':float(r.ask_open),'q':float(prior.q_close)}


def build_trades(config,minutes,weekends):
    m=minutes.set_index('bar_start').sort_index()
    cfg=config['convergence']
    rows=[]
    for w in weekends.tail(cfg['recent_window_weeks']).itertuples():
        ts=w.t_0+pd.Timedelta(minutes=cfg['signal_delay_from_reopen_minutes'])
        tin=ts+pd.Timedelta(minutes=cfg['entry_delay_from_signal_minutes'])
        signal=signal_at(m,ts,cfg['signal_abs_basis_min_log_bps'])
        entry=execution_at(m,tin)
        prior=m.loc[(m.index>=tin-pd.Timedelta(hours=1))&(m.index<tin)]
        trail=float(prior.quote_volume_quote_ccy.sum())*entry['q'] if entry and len(prior)==60 else np.nan
        for horizon in [cfg['exit_after_entry_hours'],*cfg['sensitivity_exit_hours']]:
            tout=tin+pd.Timedelta(hours=horizon)
            exit=execution_at(m,tout)
            row={'id':w.id,'week':w.week,'t_0':w.t_0,'t_signal':ts,'t_in':tin,'t_out':tout,'horizon_hours':horizon,
                 'calendar_valid':bool(w.valid),'weekend_basis_bps':w.b_0,'stress_flag':w.stress_flag,
                 **signal,'entry_observed':entry is not None,'exit_observed':exit is not None,
                 'trailing_volume_usd':trail,'capacity_1pct_usd':trail*.01,'capacity_5pct_usd':trail*.05,
                 'capacity_status':'hypothetical_trailing_volume_not_depth','short_access_status':'not_verified',
                 'cost_completeness':'borrow_and_financing_unknown','execution_status':'minute_OHLC_proxy_not_executable_claim'}
            for prefix,value in [('in',entry),('out',exit)]:
                for name in ['P','S','bid','ask','q']:
                    row[f'{name}_{prefix}']=value[name] if value else np.nan
            row['path_valid']=bool(w.valid and signal['signal_available'] and entry and exit)
            row['evaluated_trade']=row['path_valid'] and signal['signal_eligible']
            if not w.valid: reason='invalid_hourly_calendar_or_currency'
            elif not signal['signal_available']: reason='signal_price_missing_or_stale'
            elif entry is None: reason='entry_missing_or_no_trade'
            elif exit is None: reason='exit_missing_or_no_trade'
            else: reason=''
            row['exclusion_reason']=reason
            row['b_in']=float(basis(row['P_in'],1,row['S_in']))
            row['b_out']=float(basis(row['P_out'],1,row['S_out']))
            row['gold_return']=row['S_out']/row['S_in']-1 if entry and exit else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def minute_robustness(config,minutes,weekends):
    m=minutes.set_index('bar_start').sort_index()
    rows=[]
    for w in weekends[weekends.valid].tail(config['alignment']['minute_robustness_recent_weekends']).itertuples():
        for tolerance in config['alignment']['utc_price_tolerances_minutes']:
            for point,hour,hourly_b in [('reopen',0,w.b_0),('one_hour',1,w.b_1h),('seven_hours',7,w.b_7h)]:
                at=w.t_0+pd.Timedelta(hours=hour)
                before=minute_close(m,at,tolerance)
                if hour==0:
                    # O ouro está fechado antes de t0; só token e FX são buscados para trás.
                    prev=m.loc[(m.index>=at-pd.Timedelta(minutes=tolerance))&(m.index+pd.Timedelta(minutes=1)<=at)]
                    prev=prev[prev.token_active.eq(True)&prev.fx_active.eq(True)]
                    g=m.loc[at] if at in m.index else None
                    b=float(basis(prev.iloc[-1].p_close,prev.iloc[-1].q_close,g.mid_open)) if len(prev) and g is not None and g.gold_active else np.nan
                else:
                    b=float(basis(before.p_close,before.q_close,before.mid_close)) if before is not None else np.nan
                rows.append({'id':w.id,'week':w.week,'point':point,'tolerance_minutes':tolerance,'hourly_basis_bps':hourly_b,'minute_basis_bps':b,'difference_bps':b-hourly_b})
    return pd.DataFrame(rows)
