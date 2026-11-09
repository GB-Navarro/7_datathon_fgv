"""Contabilidade de posições, cruzamentos de custo e bootstrap em semanas."""
from __future__ import annotations
import numpy as np
import pandas as pd


def block_indices(n, draws, block, seed):
    if n < 1 or block < 1:
        raise ValueError('Amostra e bloco devem ser positivos.')
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n,size=(draws,int(np.ceil(n/block))))
    return ((starts[:,:,None]+np.arange(block))%n).reshape(draws,-1)[:,:n]


def distribution(values):
    a=np.asarray(values,dtype=float)
    a=a[np.isfinite(a)]
    if not len(a):
        return {k:np.nan for k in ['mean_signed_bps','median_abs_bps','p95_abs_bps','max_abs_bps','above_25_fraction','above_50_fraction','above_100_fraction']}|{'n':0}
    absolute=np.abs(a)
    return {'n':len(a),'mean_signed_bps':float(a.mean()),'median_abs_bps':float(np.median(absolute)),
            'p95_abs_bps':float(np.quantile(absolute,.95)),'max_abs_bps':float(absolute.max()),
            **{f'above_{x}_fraction':float((absolute>x).mean()) for x in [25,50,100]}}


def weekly_intervals(values, weeks, config, *, signed=False, block=None):
    frame=pd.DataFrame({'v':np.asarray(values,dtype=float),'week':pd.to_datetime(weeks,utc=True)})
    frame=frame[frame.week.notna()]
    if frame.empty:
        return {}
    grid=pd.date_range(frame.week.min(),frame.week.max(),freq='7D',tz='UTC')
    groups={k:g.v.to_numpy() for k,g in frame.groupby('week')}
    arrays=[groups.get(w,np.array([np.nan])) for w in grid]
    counts=frame.loc[np.isfinite(frame.v),'week'].nunique()
    if counts<12:
        return {'n_weeks':int(counts),'ci_status':'insufficient_weeks'}
    cfg=config['analysis']
    indices=block_indices(len(grid),cfg['bootstrap_replicates'],block or cfg['bootstrap_block_weeks'],cfg['bootstrap_seed'])
    estimates=[]
    for idx in indices:
        a=np.concatenate([arrays[i] for i in idx])
        a=a[np.isfinite(a)]
        if not len(a):
            continue
        if signed:
            estimates.append([np.mean(a),np.median(a),np.mean(a>0)])
        else:
            estimates.append([np.median(np.abs(a)),np.quantile(np.abs(a),.95),np.mean(np.abs(a)>50)])
    alpha=(1-cfg['confidence_level'])/2
    ci=np.quantile(estimates,[alpha,1-alpha],axis=0)
    names=['mean_model_bps','median_model_bps','positive_fraction'] if signed else ['median_abs_bps','p95_abs_bps','above_50_fraction']
    out={'n_weeks':int(counts),'ci_status':'exploratory_circular_weekly_blocks'}
    for i,name in enumerate(names):
        if not signed and name=='p95_abs_bps' and counts<30:
            continue
        out[name+'_lo']=float(ci[0,i]);out[name+'_hi']=float(ci[1,i])
    return out


def holding_crossing(token_rt,etf_rt,token_annual,etf_annual):
    a=float(token_rt-etf_rt); b=float(token_annual-etf_annual)
    if abs(b)<1e-12:
        status='equal_all_horizons' if abs(a)<1e-12 else 'token_always_cheaper' if a<0 else 'token_always_more_expensive'
        crossing=np.nan
    elif b<0:
        status='token_always_cheaper' if a<=0 else 'token_cheaper_after_crossing'
        crossing=-12*a/b if a>0 else np.nan
    else:
        status='token_cheaper_before_crossing' if a<0 else 'token_always_more_expensive'
        crossing=-12*a/b if a<0 else np.nan
    return {'initial_difference_bps':a,'annual_difference_bps':b,'crossing_months':crossing,'status':status}


def pair_pnl(side,p_in,p_out,s_in,s_out,*,bid_in,ask_in,bid_out,ask_out,token_fee=10.,gold_fee=1.,token_spread=10.,conversion=2.,slippage=2.,residual_carry=None):
    """Uma onça em cada perna. Quotes do token são construídas, não observadas."""
    side=np.asarray(side,dtype=float)
    pin,pout,si,so=map(lambda x:np.asarray(x,dtype=float),(p_in,p_out,s_in,s_out))
    sign=side
    token_entry=pin*(1-sign*token_spread/20000)*(1-sign*slippage/10000)
    token_exit=pout*(1+sign*token_spread/20000)*(1+sign*slippage/10000)
    gold_entry=np.where(sign>0,ask_in,bid_in)*(1+sign*slippage/10000)
    gold_exit=np.where(sign>0,bid_out,ask_out)*(1-sign*slippage/10000)
    pnl_quote=sign*(token_entry-token_exit+gold_exit-gold_entry)
    fees=(token_entry+token_exit)*token_fee/10000+(gold_entry+gold_exit)*gold_fee/10000
    before_unknown=10000*(pnl_quote-fees)/si-conversion
    gross=10000*sign*(pin-pout+so-si)/si
    return {'gross_mid_bps':gross,'after_modeled_before_unknown_carry_bps':before_unknown,
            'explicit_fee_bps':10000*fees/si,
            'net_if_residual_assumed_bps':before_unknown-residual_carry if residual_carry is not None else np.full_like(before_unknown,np.nan)}
