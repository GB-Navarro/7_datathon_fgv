"""Testes da rotação GLDM <-> PAXG (extensão v5), sem rede e com séries sintéticas declaradas."""
import numpy as np
import pandas as pd

from src.rotation import SCENARIOS, side_cost, simulate


def _series(values):
    days = pd.bdate_range('2024-01-01', periods=len(values))
    return pd.Series(np.asarray(values, dtype=float), index=days)


def test_side_cost_matches_cycle_costs():
    assert 2 * side_cost(SCENARIOS['intermediario']) == 19
    assert 2 * side_cost(SCENARIOS['original']) == 37


def test_no_lookahead_decisions_before_change_are_identical():
    rng = np.random.default_rng(0)
    base = rng.normal(0, 40, 300).cumsum() / 5
    b1 = _series(base)
    changed = base.copy()
    changed[200:] += 500  # altera só o futuro a partir do dia 200
    b2 = _series(changed)
    _, rel1, pos1 = simulate(b1, lambda i: -10, lambda i: 10, 9.5, lag=1)
    _, rel2, pos2 = simulate(b2, lambda i: -10, lambda i: 10, 9.5, lag=1)
    assert (pos1.iloc[:200] == pos2.iloc[:200]).all()
    assert np.allclose(rel1.iloc[:200], rel2.iloc[:200])


def test_execution_happens_on_next_session_at_next_price():
    b = _series([0, -30, -50, 0, 40, 60, 60])
    cyc, rel, pos = simulate(b, lambda i: -20, lambda i: 20, 5.0, lag=1, fee=0.0)
    # sinal no dia 1 (-30) -> entra no dia 2 a -50; sinal de saída no dia 4 (40) -> sai no dia 5 a 60
    assert list(pos) == [0, 0, 1, 1, 1, 0, 0]
    assert len(cyc) == 1
    assert cyc.desvio_entrada.iloc[0] == -50 and cyc.desvio_saida.iloc[0] == 60
    assert np.isclose(cyc.resultado_bps.iloc[0], 110 - 10)
    assert np.isclose(rel.sum(), cyc.resultado_bps.sum())


def test_open_position_is_charged_exit_cost():
    b = _series([0, -30, -40, -45])
    cyc, rel, _ = simulate(b, lambda i: -20, lambda i: 20, 5.0, lag=1, fee=0.0)
    assert len(cyc) == 0
    assert np.isclose(rel.sum(), (-45 - -40) - 5 - 5)
