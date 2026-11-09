"""Testes da entrega v2: XAUT e regimes sem dado futuro (séries sintéticas declaradas, sem rede)."""
import numpy as np
import pandas as pd

from src.rotation import simulate
from src.v2_regimes import walk_forward_probs
from src.v2_xaut import daily_from_hourly


def _hourly(values, start='2024-01-01'):
    t = pd.date_range(start, periods=len(values), freq='h', tz='UTC')
    return pd.DataFrame({'t': t, 'basis_bps': np.asarray(values, dtype=float)})


def test_xaut_daily_mean_uses_only_session_bars_of_the_same_day():
    h = _hourly(np.arange(24 * 10))
    d1 = daily_from_hourly(h, min_bars=4)
    h2 = h.copy()
    h2.loc[h2.t >= pd.Timestamp('2024-01-06', tz='UTC'), 'basis_bps'] += 999  # muda só o futuro
    d2 = daily_from_hourly(h2, min_bars=4)
    early = d1.index < pd.Timestamp('2024-01-06')
    assert np.allclose(d1[early], d2[early])
    # 2024-01-01 é feriado da NYSE e fica fora; dia 02 usa as barras que fecham das 15h às 20h
    assert pd.Timestamp('2024-01-01') not in d1.index
    assert np.isclose(d1[pd.Timestamp('2024-01-02')], np.mean(np.arange(24 + 15, 24 + 21)))


def test_xaut_rule_decisions_before_change_do_not_move():
    rng = np.random.default_rng(1)
    b = pd.Series(rng.normal(0, 30, 260).cumsum() / 4, index=pd.bdate_range('2023-01-02', periods=260))
    changed = b.copy()
    changed.iloc[150:] -= 400
    _, r1, p1 = simulate(b, lambda i: -19, lambda i: 19, 9.5, 1)
    _, r2, p2 = simulate(changed, lambda i: -19, lambda i: 19, 9.5, 1)
    assert (p1.iloc[:150] == p2.iloc[:150]).all() and np.allclose(r1.iloc[:150], r2.iloc[:150])


def test_regime_probabilities_ignore_future_data_including_reestimation():
    rng = np.random.default_rng(5)
    levels = np.repeat([-60.0, 0.0, 60.0, -60.0, 60.0, 0.0], 50)
    b = pd.Series(levels + rng.normal(0, 8, len(levels)), index=pd.bdate_range('2022-01-03', periods=len(levels)))
    p1 = walk_forward_probs(b, min_obs=120)
    changed = b.copy()
    cut = 240
    changed.iloc[cut:] += 300
    p2 = walk_forward_probs(changed, min_obs=120)
    # filtro com parâmetros congelados: a probabilidade do dia t só usa dados até t, então nada antes do corte muda
    a, c = p1.iloc[:cut], p2.iloc[:cut]
    assert a.notna().any().any()
    assert np.allclose(a.fillna(-1).values, c.fillna(-1).values)
