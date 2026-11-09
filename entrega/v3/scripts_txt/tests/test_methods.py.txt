import hashlib
import io
import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from src.common import basis,load_config,normalize_times
from src.fetch import download,read_kline
from src.panel import build_hourly,build_weekends,gold_open_mask,scheduled_reopen
from src.statistics import block_indices,holding_crossing,pair_pnl,weekly_intervals
from src.trades import build_trades,signal_at


@pytest.mark.parametrize('scale',[1,1000,1000000])
def test_timestamp_units(scale):
    assert normalize_times([1598616000*scale])[0]==pd.Timestamp('2020-08-28T12:00:00Z')


def test_mixed_units_rejected():
    with pytest.raises((ValueError,OverflowError)):
        normalize_times([1598616000000,1790812800000000])


def test_log_identity_large_moves_and_fx():
    pc,qc,sc=1990,1.001,2000
    p0,q0,s0=2120,.998,2100
    actual=basis(p0,q0,s0)-basis(pc,qc,sc)
    expected=10000*np.log(p0*q0/(pc*qc))-10000*np.log(s0/sc)
    assert actual==pytest.approx(expected,abs=1e-9)


def test_missing_currency_not_parity():
    assert np.isnan(basis(2000,np.nan,2000))
    assert np.isnan(basis(2000,0,2000))


def test_dst_and_gold_break():
    assert scheduled_reopen('2026-10-25')==pd.Timestamp('2026-10-25T22:00:00Z')
    assert scheduled_reopen('2026-11-01')==pd.Timestamp('2026-11-01T23:00:00Z')
    t=pd.to_datetime(['2026-10-31T12:00Z','2026-11-01T22:00Z','2026-11-01T23:00Z','2026-11-02T22:00Z','2026-11-02T23:00Z'],utc=True)
    assert gold_open_mask(t).tolist()==[False,False,True,False,True]


def frames():
    times=pd.to_datetime(['2020-08-28T20:00:00Z','2020-08-30T21:00:00Z','2020-08-30T22:00:00Z','2020-08-31T04:00:00Z'],utc=True)
    t=pd.DataFrame({'bar_start':times,'close':[2000.,2020.,2010.,2002.],'quote_volume_quote_ccy':10000.,'has_trade':True})
    q=pd.DataFrame({'bar_start':times,'close':1.,'has_trade':True})
    g=pd.DataFrame({'bar_start':times[[0,2,3]],'mid_open':[2000.,2005.,2005.], 'mid_close':[2000.,2005.,2005.],
                    'spread_close_bps':2.,'quote_active':True,'valid_quotes':True})
    return t,g,q


def test_hourly_missing_fx_never_filled():
    t,g,q=frames();q=q[q.bar_start!=pd.Timestamp('2020-08-30T22:00Z')]
    cfg=load_config();cfg['data']['end_exclusive_utc']='2020-09-01T00:00:00Z'
    h=build_hourly(t,g,q,cfg)
    r=h[h.bar_start==pd.Timestamp('2020-08-30T22:00Z')].iloc[0]
    assert not r.valid and np.isnan(r.basis_log_bps)
    assert r.exclusion_reason=='fx_missing_or_no_trade'


def test_weekend_observed_vs_calendar_and_identity():
    t,g,q=frames();cfg=load_config();cfg['data']['last_candidate_reopen_date']='2020-08-30'
    w=build_weekends(t,g,q,cfg).iloc[0]
    assert w.valid and w.calendar_status=='regular_calendar'
    assert w.identity_residual_bps==pytest.approx(0,abs=1e-9)
    assert w.b_0==pytest.approx(10000*np.log(2020/2005))


def test_zero_volume_weekend_bars_do_not_hide_reopen():
    t,g,q=frames();cfg=load_config();cfg['data']['last_candidate_reopen_date']='2020-08-30'
    inactive=g.iloc[[0]].copy();inactive['bar_start']=pd.Timestamp('2020-08-29T12:00Z');inactive['quote_active']=False
    w=build_weekends(t,pd.concat([g,inactive]),q,cfg).iloc[0]
    assert w.t_0==pd.Timestamp('2020-08-30T22:00Z')
    assert w.valid


def test_missing_first_reopen_hour_not_shifted_silently():
    t,g,q=frames();cfg=load_config();cfg['data']['last_candidate_reopen_date']='2020-08-30'
    g=g[g.bar_start!=pd.Timestamp('2020-08-30T22:00Z')]
    w=build_weekends(t,g,q,cfg).iloc[0]
    assert not w.valid
    assert 'delayed' in w.calendar_status


@pytest.mark.parametrize('side,pin,pout,expected',[(1,101,100,100),(-1,99,100,100),(1,101,102,-100),(1,101,99.5,150)])
def test_exact_pnl_and_losses(side,pin,pout,expected):
    r=pair_pnl(side,pin,pout,100,100,bid_in=100,ask_in=100,bid_out=100,ask_out=100,
               token_fee=0,gold_fee=0,token_spread=0,conversion=0,slippage=0)
    assert r['after_modeled_before_unknown_carry_bps']==pytest.approx(expected)
    assert np.isnan(r['net_if_residual_assumed_bps'])


def test_spread_not_double_counted():
    r=pair_pnl(1,100,100,100,100,bid_in=99.97,ask_in=100.03,bid_out=99.97,ask_out=100.03,
               token_fee=0,gold_fee=0,token_spread=4,conversion=0,slippage=0)
    assert r['after_modeled_before_unknown_carry_bps']==pytest.approx(-10)


def test_larger_costs_reduce_pnl_fixed_positions():
    kw=dict(side=1,p_in=101,p_out=100,s_in=100,s_out=100,bid_in=99.99,ask_in=100.01,bid_out=99.99,ask_out=100.01)
    low=pair_pnl(**kw,token_fee=2)
    high=pair_pnl(**kw,token_fee=10)
    assert low['after_modeled_before_unknown_carry_bps']>high['after_modeled_before_unknown_carry_bps']


@pytest.mark.parametrize('a,b,expected',[(22,-40,'token_cheaper_after_crossing'),(-2,-40,'token_always_cheaper'),(0,-40,'token_always_cheaper'),(22,0,'token_always_more_expensive'),(-2,0,'token_always_cheaper'),(0,0,'equal_all_horizons'),(-2,10,'token_cheaper_before_crossing'),(22,10,'token_always_more_expensive')])
def test_crossing_classification(a,b,expected):
    r=holding_crossing(a,0,b,0)
    assert r['status']==expected


def test_crossing_gld_gldm_and_reverse():
    assert holding_crossing(25,3,0,40)['crossing_months']==pytest.approx(6.6)
    assert holding_crossing(25,3,0,10)['crossing_months']==pytest.approx(26.4)
    assert holding_crossing(1,3,20,10)['crossing_months']==pytest.approx(2.4)


def minute_fixture():
    times=pd.date_range('2026-11-01T23:00:00Z',periods=500,freq='min')
    m=pd.DataFrame({'bar_start':times,'bar_end':times+pd.Timedelta(minutes=1),'p_open':101.,'p_close':101.,'q_close':1.,'mid_open':100.,'mid_close':100.,
                    'bid_open':100.,'ask_open':100.,'token_active':True,'fx_active':True,'gold_active':True,'close_valid':True,'quote_volume_quote_ccy':1000.})
    return m


def test_signal_no_lookahead_and_missing_signal():
    m=minute_fixture().set_index('bar_start');at=pd.Timestamp('2026-11-02T00:00Z')
    full=signal_at(m,at,10)
    prefix=signal_at(m[m.index+pd.Timedelta(minutes=1)<=at],at,10)
    assert full==prefix
    changed=m.copy();changed.loc[changed.index>=at,'p_close']=10**6
    assert signal_at(changed,at,10)==full
    m.loc[m.index==at-pd.Timedelta(minutes=1),'close_valid']=False
    assert not signal_at(m,at,10)['signal_available']


def test_trade_exit_missing_is_not_zero():
    config=load_config();m=minute_fixture();at=pd.Timestamp('2026-11-02T06:01Z')
    m=m[m.bar_start!=at]
    w=pd.DataFrame([{'id':'2026-11-01','week':pd.Timestamp('2026-11-01T00:00Z'),'t_0':pd.Timestamp('2026-11-01T23:00Z'),'valid':True,'b_0':100.,'stress_flag':False}])
    trades=build_trades(config,m,w)
    r=trades[trades.horizon_hours==6].iloc[0]
    assert r.signal_eligible and r.entry_observed and not r.exit_observed
    assert not r.path_valid and not r.evaluated_trade
    assert r.exclusion_reason=='exit_missing_or_no_trade'


def test_future_volume_does_not_change_sizing():
    config=load_config();m=minute_fixture();w=pd.DataFrame([{'id':'2026-11-01','week':pd.Timestamp('2026-11-01T00:00Z'),'t_0':pd.Timestamp('2026-11-01T23:00Z'),'valid':True,'b_0':100.,'stress_flag':False}])
    initial=build_trades(config,m,w)
    m.loc[m.bar_start>=pd.Timestamp('2026-11-02T00:01Z'),'quote_volume_quote_ccy']=1e12
    changed=build_trades(config,m,w)
    np.testing.assert_allclose(initial.capacity_5pct_usd,changed.capacity_5pct_usd)


def test_joint_bootstrap_preserves_blocks_and_seed():
    idx=block_indices(12,3,4,19)
    np.testing.assert_array_equal(idx,block_indices(12,3,4,19))
    for row in idx:
        for i in range(0,12,4):
            assert np.all(np.diff(row[i:i+4])%12==1)


def test_offline_never_network_and_cache_integrity(tmp_path,monkeypatch):
    def no_network(*a,**kw):raise AssertionError('Rede proibida')
    monkeypatch.setattr('requests.get',no_network)
    path=tmp_path/'cache.json'
    with pytest.raises(FileNotFoundError):download('https://example.invalid',path,offline=True)
    path.write_bytes(b'[]')
    meta={'url':'https://example.invalid','sha256':hashlib.sha256(b'[]').hexdigest()}
    path.with_name(path.name+'.meta.json').write_text(json.dumps(meta))
    assert download(meta['url'],path,offline=True)==path
    path.write_bytes(b'[1]')
    with pytest.raises(ValueError):download(meta['url'],path,offline=True)


def test_binance_microsecond_parser(tmp_path):
    path=tmp_path/'data.zip'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('data.csv','1790812800000000,100,101,99,100,1,1790816399999999,100,1,0.5,50,0\n')
    r=read_kline(path,'1h').iloc[0]
    assert r.bar_start==pd.Timestamp('2026-10-01T00:00Z')
    assert r.bar_end==pd.Timestamp('2026-10-01T01:00Z')
    assert r.has_trade


def test_stochastic_scenario_branch_and_deterministic_gate(monkeypatch):
    from src.analysis import scenarios
    config=load_config()
    n=104;si=np.full(n,2000.);so=si*1.001
    bin_=np.full(n,30.);bout=np.full(n,10.)
    frame=pd.DataFrame({'horizon_hours':6,'path_valid':True,'signal_basis_bps':30.,'b_in':bin_,'b_out':bout,
                        'P_in':si*np.exp(bin_/10000),'P_out':so*np.exp(bout/10000),'S_in':si,'S_out':so,
                        'bid_in':si-.1,'ask_in':si+.1,'bid_out':so-.1,'ask_out':so+.1,
                        'weekend_basis_bps':np.linspace(-100,100,n),'calendar_valid':True,'capacity_5pct_usd':1000.})
    monkeypatch.setattr('src.analysis.save_csv',lambda *a,**k:None)
    result=scenarios(config,frame,None)
    assert result.method.str.contains('paired_joint').all()
    assert 'mean_trade_model_bps_lo' in result
    assert result.loc[result.scenario.eq('lower_friction'),'mean_trade_model_before_unknown_carry_bps'].iloc[0]>result.loc[result.scenario.eq('baseline'),'mean_trade_model_before_unknown_carry_bps'].iloc[0]
    sparse=frame.copy();sparse.loc[50:,'path_valid']=False
    reduced=scenarios(config,sparse,None)
    assert reduced.method.str.contains('deterministic').all()
