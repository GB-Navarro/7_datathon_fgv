"""Temporal leakage, incomplete observations and accounting in the v3 extension."""
import numpy as np
import pandas as pd
import pytest

from src import refinement as r


@pytest.fixture
def spec():
    return r.load_refinement()


def test_calendar_bootstrap_preserves_missing_calendar_weeks(spec):
    weeks=pd.date_range('2022-01-02',periods=30,freq='7D',tz='UTC')
    values=np.full(30,-5.);values[8:14]=np.nan
    result=r.calendar_interval(values,weeks,spec)
    assert result['n']==24 and result['calendar_weeks']==30
    assert result['estimate']==result['lo']==result['hi']==-5.


def test_duplicate_week_is_rejected(spec):
    with pytest.raises(ValueError):r.calendar_interval([1.,2.],pd.to_datetime(['2022-01-02']*2,utc=True),spec)


def synthetic_forecast_frame():
    weeks=pd.date_range('2020-01-05',periods=40,freq='7D',tz='UTC')
    x=np.arange(40,dtype=float)-12
    return pd.DataFrame({'id':weeks.strftime('%F'),'week':weeks,'t_decision':weeks+pd.Timedelta(hours=23),
        't_target':weeks+pd.Timedelta(hours=29),'b_1h':x,'g':np.sin(x),'log_prior_gold_vol':np.cos(x),
        'actual':2*x+3,'complete':True})


def test_future_outcomes_do_not_change_earlier_forecasts(spec):
    spec['forecast'].update(initial_training_calendar_weeks=12,minimum_training_observations=8)
    first=synthetic_forecast_frame();second=first.copy();second.loc[30:,'actual']+=100000
    a,_=r.expanding_forecasts(first,spec);b,_=r.expanding_forecasts(second,spec)
    earlier=a.week<first.week.iloc[30]
    assert np.allclose(a.loc[earlier,'prediction'],b.loc[earlier,'prediction'])
    assert (a.train_last_target<a.t_decision).all()


def test_models_use_the_same_test_cohort(spec):
    spec['forecast'].update(initial_training_calendar_weeks=12,minimum_training_observations=8)
    data=synthetic_forecast_frame();data.loc[20,'complete']=False
    predictions,_=r.expanding_forecasts(data,spec)
    assert predictions[predictions.id.eq(data.id.iloc[20])].evaluated.eq(False).all()
    cohorts=predictions[predictions.evaluated].groupby('model').week.apply(tuple)
    assert len(set(cohorts))==1


def test_linear_scaling_uses_training_only():
    train=pd.DataFrame({'b_1h':[1.,2.,3.,4.],'actual':[5.,7.,9.,11.]})
    prediction,coefficients=r.linear_prediction(train,pd.Series({'b_1h':1000.}),['b_1h'])
    assert prediction==pytest.approx(2003.)
    assert coefficients['b_1h']==pytest.approx(2.)
    assert coefficients['intercept']==pytest.approx(3.)


def minute_frame():
    times=pd.date_range('2025-01-01',periods=8,freq='min',tz='UTC')
    return pd.DataFrame({'bar_start':times,'bar_end':times+pd.Timedelta(minutes=1),
        'q_close':[1.,1.,1.,1.,1.,1.01,1.01,1.01],
        'fx_active':[True,False,False,False,False,True,False,False],
        'p_close':2000.,'mid_close':2000.,'token_active':True,'gold_active':True})


def test_fx_alignment_bounded_backward_without_carrying_gold():
    data=minute_frame();data.loc[2,'gold_active']=False
    original=r.align_completed_fx(data,1);relaxed=r.align_completed_fx(data,5)
    assert original.fx_active.to_list()==data.fx_active.to_list()
    assert relaxed.loc[4,'q_close']==1.
    assert relaxed.loc[4,'fx_bar_age_minutes']==5.
    assert relaxed.loc[4,'fx_close_age_minutes']==4.
    assert not relaxed.loc[2,'close_valid']
    assert relaxed.p_close.equals(data.p_close)
    assert (relaxed.fx_used_available_at<=relaxed.bar_end).all()


def test_future_fx_is_never_used_and_expired_quote_is_missing():
    data=minute_frame();data.loc[:4,'fx_active']=False
    out=r.align_completed_fx(data,5)
    assert out.loc[:4,'q_close'].isna().all()
    data.loc[5:,'fx_active']=False;data.loc[0,'fx_active']=True
    out=r.align_completed_fx(data,5)
    assert pd.isna(out.loc[5,'q_close'])


def test_missingness_break_even_is_not_zero_imputation(spec,monkeypatch):
    monkeypatch.setattr(r,'save_csv',lambda *args:None)
    trades=pd.DataFrame({'horizon_hours':6,'evaluated_trade':[True]*44+[False]*16,
        'calendar_valid':True,'signal_eligible':True,'path_valid':[True]*44+[False]*16,
        'after_modeled_before_unknown_carry_bps':[-40.]*44+[np.nan]*16})
    result=r.missingness_sensitivity(trades,spec).iloc[0]
    assert result.unassessed_signals==16
    assert result.required_unassessed_mean_to_break_even_bps==110.
    assert trades.after_modeled_before_unknown_carry_bps.isna().sum()==16


def test_paired_effect_is_mean_of_individual_changes(spec,monkeypatch):
    monkeypatch.setattr(r,'save_csv',lambda *args:None)
    # Difference of medians differs from mean within-week change.
    w=pd.DataFrame({'valid':True,'week':pd.date_range('2021-01-03',periods=15,freq='7D',tz='UTC'),
        'b_c':[100.]*15,'b_0':[100.,1.,1.]*5,'b_1h':[1.,100.,100.]*5,'b_7h':[0.]*15})
    result=r.paired_changes(w,spec).set_index('comparison').loc['b_0_to_b_1h']
    assert result.mean_abs_change_bps==33.
    assert np.median(abs(w.b_1h))-np.median(abs(w.b_0))==99.


def test_prior_volatility_does_not_use_future_prices(spec):
    times=pd.date_range('2023-01-01',periods=240,freq='h',tz='UTC')
    h=pd.DataFrame({'bar_start':times,'t':times+pd.Timedelta(hours=1),'valid':True,
                    'S':2000*np.exp(np.sin(np.arange(240))*.001)})
    t0=times[180]
    w=pd.DataFrame({'id':['event'],'week':[t0.normalize()],'t_0':[t0],'valid':[True],
                    'b_1h':[10.],'g':[5.],'b_7h':[8.]})
    a=r.forecast_dataset(h,w,spec)
    h.loc[h.t>t0,'S']*=1000
    b=r.forecast_dataset(h,w,spec)
    assert a.log_prior_gold_vol.iloc[0]==b.log_prior_gold_vol.iloc[0]
    assert a.last_vol_observation.iloc[0]<=t0
