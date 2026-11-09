"""Entrega v2 · Fase 4: regra de rotação por regimes (Markov com 3 regimes), sem dado futuro.

Uso: python -m src.v2_regimes
Saídas em results/v2/: T19_regimes_resumo.csv, T19_regimes_probabilidades.csv, T19_regimes_resumo.json

Pré-registro (PLANO_ENTREGA_V2.md, seção 3): MarkovRegression com 3 regimes de média e variância no desvio
diário; reestimação no primeiro pregão de cada mês só com dados anteriores (mínimo de 500 pregões); filtro do mês
com os parâmetros congelados (probabilidade do dia t usa só dados até t); regimes ordenados pela média
(desconto < neutro < prêmio). Regra: vai ao PAXG se P(desconto) > 50%; volta ao GLDM se P(prêmio) > 50%.
Custos intermediários, atraso de 1 pregão. Comparação com a faixa ±19 no mesmo período.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .common import ROOT, dump_json
from .rotation import SCENARIOS, daily_basis, metrics, side_cost, simulate

OUT = ROOT / 'results' / 'v2'
MIN_OBS = 500


def _fit(y, start_params=None):
    """Ajusta o modelo; se a otimização falhar, devolve None e o mês usa os últimos parâmetros (só passado)."""
    mod = sm.tsa.MarkovRegression(y, k_regimes=3, trend='c', switching_variance=True)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        if start_params is not None:
            try:
                return mod.fit(start_params=start_params, disp=False)
            except Exception:
                pass
        try:
            np.random.seed(20261108)  # search_reps sorteia pontos de partida: semente fixa para reproduzir
            return mod.fit(disp=False, search_reps=5)
        except Exception:
            return None


def walk_forward_probs(b: pd.Series, min_obs: int = MIN_OBS) -> pd.DataFrame:
    """Probabilidades filtradas (desconto, neutro, prêmio) com reestimação mensal só com o passado."""
    v = b.values
    months = pd.Series(b.index).dt.to_period('M')
    first_idx = months.drop_duplicates().index.tolist()
    probs = np.full((len(v), 3), np.nan)
    params, names = None, None
    for j, i0 in enumerate(first_idx):
        if i0 < min_obs:
            continue
        i1 = first_idx[j + 1] if j + 1 < len(first_idx) else len(v)
        res = _fit(v[:i0], params)
        if res is None and params is None:
            continue
        if res is not None:
            params, names = res.params, res.model.param_names
        const = np.array([params[names.index(f'const[{r}]')] for r in range(3)])
        order = np.argsort(const)  # desconto, neutro, prêmio
        mod = sm.tsa.MarkovRegression(v[:i1], k_regimes=3, trend='c', switching_variance=True)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            filt = mod.filter(params).filtered_marginal_probabilities
        filt = np.asarray(filt)
        probs[i0:i1] = filt[i0:i1][:, order]
    return pd.DataFrame(probs, index=b.index, columns=['p_desconto', 'p_neutro', 'p_premio'])


def regime_rule(b, probs, cs, lag=1):
    pd_, pp = probs.p_desconto.values, probs.p_premio.values
    enter = lambda i: 1e9 if (not np.isnan(pd_[i]) and pd_[i] > .5) else -1e9
    exit_ = lambda i: -1e9 if (not np.isnan(pp[i]) and pp[i] > .5) else 1e9
    return simulate(b, enter, exit_, cs, lag)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    b = daily_basis()
    probs = walk_forward_probs(b)
    probs.reset_index(names='dia').to_csv(OUT / 'T19_regimes_probabilidades.csv', index=False, encoding='utf-8-sig', float_format='%.6g')
    start = probs.p_desconto.first_valid_index()
    bb, pp = b[b.index >= start], probs[probs.index >= start]
    rows = []
    for scen in ('intermediario', 'original'):
        cs = side_cost(SCENARIOS[scen])
        k = int(round(2 * cs))
        for lag in (1, 2):
            cyc, rel, pos = regime_rule(bb, pp, cs, lag)
            rows.append(metrics('regimes (HMM filtrado)', cyc, rel, pos, {'cenario_custos': scen, 'lag_pregoes': lag, 'regra': 'hmm_filtrado'}))
            cyc, rel, pos = simulate(bb, lambda i, k=k: -k, lambda i, k=k: k, cs, lag)
            rows.append(metrics(f'faixa fixa ±{k} (mesmo período)', cyc, rel, pos, {'cenario_custos': scen, 'lag_pregoes': lag, 'regra': 'faixa_fixa'}))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / 'T19_regimes_resumo.csv', index=False, encoding='utf-8-sig', float_format='%.10g')
    dump_json(OUT / 'T19_regimes_resumo.json', {
        'inicio_regra': str(start.date()), 'pregoes': int(len(bb)), 'reestimacoes_mensais': int(pd.Series(bb.index).dt.to_period('M').nunique()),
        'fracao_dias_desconto_dominante': float((pp.p_desconto > .5).mean()), 'fracao_dias_premio_dominante': float((pp.p_premio > .5).mean()),
        'nota': 'probabilidades filtradas com parâmetros reestimados todo mês só com dados anteriores'})
    return t


if __name__ == '__main__':
    t = run()
    print(t[['config', 'cenario_custos', 'lag_pregoes', 'ciclos', 'ciclos_positivos', 'ganho_anual_vs_gldm_bps', 'ic90_lo', 'ic90_hi', 'razao_informacao', 'pior_queda_bps']].round(2).to_string())
