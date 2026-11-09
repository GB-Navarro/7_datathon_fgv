"""Extensão v5: rotação GLDM <-> PAXG, fim de semana, risco de base e modelo de dois componentes.

Uso: python -m src.rotation
Saídas em results/: T12_* (rotação), T13_* (fim de semana), T14_* (risco de base), T15_* (componentes).

Desenho (definido depois dos resultados originais, sem alterar config/params.json):
- Investidor que já quer ouro em dólares escolhe o veículo: GLDM (taxa 0,10% a.a.) ou PAXG (sem taxa de guarda).
- Sinal diário: média do desvio nas horas 15-20 UTC de um dia útil da NYSE (sessão comum nos dois horários de verão).
- Execução: média do desvio nas mesmas horas do pregão seguinte (lag=1) ou do segundo pregão (lag=2). Sem dado futuro.
- Regra principal: entra no PAXG quando o desvio <= -k e volta ao GLDM quando o desvio >= +k, com k = custo de um ciclo.
- Custos por lado do ciclo: token (taxa + meio spread + meia conversão + deslizamento) + meio spread do ETF.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .common import ROOT, dump_json, save_csv

YEAR_D = 365.25
GLDM_FEE = 10.0  # bps ao ano
SESSION_HOURS = range(15, 21)  # fechamento das barras 15:00..20:00 UTC, dentro do pregão da NYSE o ano inteiro
NYSE_HOLIDAYS = pd.to_datetime([
    '2020-09-07', '2020-11-26', '2020-12-25',
    '2021-01-01', '2021-01-18', '2021-02-15', '2021-04-02', '2021-05-31', '2021-07-05', '2021-09-06', '2021-11-25', '2021-12-24',
    '2022-01-17', '2022-02-21', '2022-04-15', '2022-05-30', '2022-06-20', '2022-07-04', '2022-09-05', '2022-11-24', '2022-12-26',
    '2023-01-02', '2023-01-16', '2023-02-20', '2023-04-07', '2023-05-29', '2023-06-19', '2023-07-04', '2023-09-04', '2023-11-23', '2023-12-25',
    '2024-01-01', '2024-01-15', '2024-02-19', '2024-03-29', '2024-05-27', '2024-06-19', '2024-07-04', '2024-09-02', '2024-11-28', '2024-12-25',
    '2025-01-01', '2025-01-09', '2025-01-20', '2025-02-17', '2025-04-18', '2025-05-26', '2025-06-19', '2025-07-04', '2025-09-01', '2025-11-27', '2025-12-25',
    '2026-01-01', '2026-01-19', '2026-02-16', '2026-04-03', '2026-05-25', '2026-06-19', '2026-07-03', '2026-09-07'])

# custos (bps) — mesmos valores da grade original; ver T2_convergencia.csv / T3_custos_etfs.csv
SCENARIOS = {
    'intermediario': {'token_fee': 5, 'token_spread': 2, 'conversion_rt': 2, 'slippage': 2, 'etf_spread': 1},
    'original': {'token_fee': 10, 'token_spread': 10, 'conversion_rt': 2, 'slippage': 2, 'etf_spread': 1},
}


def side_cost(s):
    """Custo de um lado da troca (vender um veículo e comprar o outro)."""
    return s['token_fee'] + s['token_spread'] / 2 + s['conversion_rt'] / 2 + s['slippage'] + s['etf_spread'] / 2


def daily_basis() -> pd.Series:
    p = pd.read_parquet(ROOT / 'data/panel/panel_hourly.parquet')
    p = p[p.valid]
    p = p[(p.t.dt.dayofweek < 5) & (p.t.dt.hour.isin(SESSION_HOURS))]
    g = p.groupby(p.t.dt.tz_localize(None).dt.floor('D')).basis_log_bps.agg(['mean', 'count'])
    g = g[(g['count'] >= 4) & (~g.index.isin(NYSE_HOLIDAYS))]
    return g['mean']


def simulate(b: pd.Series, enter, exit_, cost_side: float, lag: int = 1, fee: float = GLDM_FEE):
    """Rotação sem dado futuro. enter/exit_ recebem o índice i e usam apenas b[:i+1].
    Retorna ciclos, série diária do resultado relativo ao GLDM (bps) e o estado final."""
    v, days = b.values, b.index
    state, pending, entry = 0, None, None
    rel = np.zeros(len(v))
    pos = np.zeros(len(v), dtype=int)
    cycles = []
    for i in range(len(v)):
        if state == 1 and i > 0:  # carrega o PAXG até o preço de execução de hoje
            dt = (days[i] - days[i - 1]).days / YEAR_D
            rel[i] += v[i] - v[i - 1] + fee * dt
        if pending is not None and i == pending[0]:
            if pending[1] == 1 and state == 0:
                state, entry = 1, i
                rel[i] -= cost_side
            elif pending[1] == 0 and state == 1:
                hold = (days[i] - days[entry]).days
                cycles.append({'entrada': days[entry], 'saida': days[i], 'dias': hold, 'desvio_entrada': v[entry], 'desvio_saida': v[i],
                               'resultado_bps': v[i] - v[entry] + fee * hold / YEAR_D - 2 * cost_side})
                state = 0
                rel[i] -= cost_side
            pending = None
        pos[i] = state
        if pending is None and i + lag < len(v):
            if state == 0 and v[i] <= enter(i):
                pending = (i + lag, 1)
            elif state == 1 and v[i] >= exit_(i):
                pending = (i + lag, 0)
    if state == 1:  # posição aberta no fim: marca a mercado e cobra a saída
        rel[-1] -= cost_side
    return pd.DataFrame(cycles), pd.Series(rel, index=days), pd.Series(pos, index=days)


def block_bootstrap_annual(monthly: pd.Series, reps=5000, block=6, seed=7):
    rng = np.random.default_rng(seed)
    x = monthly.values
    n = len(x)
    out = np.empty(reps)
    for r in range(reps):
        idx = []
        while len(idx) < n:
            s = rng.integers(0, n)
            idx.extend([(s + j) % n for j in range(block)])
        out[r] = x[np.array(idx[:n])].mean() * 12
    return np.percentile(out, [5, 95])


def metrics(name, cyc, rel, pos, extra):
    years = (rel.index[-1] - rel.index[0]).days / YEAR_D
    monthly = rel.resample('ME').sum()
    cum = rel.cumsum()
    lo, hi = block_bootstrap_annual(monthly)
    half = pd.Timestamp('2023-10-01')
    h1y = (half - rel.index[0]).days / YEAR_D
    h2y = (rel.index[-1] - half).days / YEAR_D
    return {'config': name, **extra,
            'ciclos': len(cyc), 'ciclos_positivos': float((cyc.resultado_bps > 0).mean()) if len(cyc) else np.nan,
            'resultado_medio_ciclo_bps': float(cyc.resultado_bps.mean()) if len(cyc) else np.nan,
            'ganho_anual_vs_gldm_bps': float(rel.sum() / years), 'ic90_lo': float(lo), 'ic90_hi': float(hi),
            'razao_informacao': float(monthly.mean() / monthly.std() * np.sqrt(12)),
            'pior_queda_bps': float((cum - cum.cummax()).min()),
            'fracao_dias_em_paxg': float(pos.mean()),
            'ganho_anual_1a_metade': float(rel[rel.index < half].sum() / h1y),
            'ganho_anual_2a_metade': float(rel[rel.index >= half].sum() / h2y)}


def placebo(b, n_cycles, durations, cost_side, sims=1000, seed=11):
    """Mesmo número de ciclos e as mesmas durações, em datas sorteadas."""
    rng = np.random.default_rng(seed)
    v, days = b.values, b.index
    years = (days[-1] - days[0]).days / YEAR_D
    out = []
    pos_len = np.array(durations)
    for _ in range(sims):
        total, used = 0.0, np.zeros(len(v), dtype=bool)
        for d in rng.permutation(pos_len):
            for _try in range(50):
                s = rng.integers(0, len(v) - 1)
                e = np.searchsorted(days, days[s] + pd.Timedelta(days=int(d)))
                if e < len(v) and not used[s:e + 1].any():
                    used[s:e + 1] = True
                    total += v[e] - v[s] + GLDM_FEE * (days[e] - days[s]).days / YEAR_D - 2 * cost_side
                    break
        out.append(total / years)
    return np.array(out)


def run_rotation():
    b = daily_basis()
    rows, primary = [], {}
    for scen, s in SCENARIOS.items():
        cs = side_cost(s)
        k0 = round(2 * cs)  # custo de um ciclo completo
        for k in sorted({k0, 10, 20, 30, 40, 50}):
            for lag in (1, 2):
                cyc, rel, pos = simulate(b, lambda i, k=k: -k, lambda i, k=k: k, cs, lag)
                tag = 'principal' if (k == k0 and lag == 1) else 'sensibilidade'
                rows.append(metrics(f'faixa fixa ±{k}', cyc, rel, pos, {'cenario_custos': scen, 'custo_ciclo_bps': 2 * cs, 'k_bps': k, 'lag_pregoes': lag, 'regra': 'faixa_fixa', 'papel': tag}))
                if tag == 'principal':
                    primary[scen] = (cyc, rel, pos, k, cs)
        # variante walk-forward: faixa em torno da mediana dos 60 pregões anteriores
        lvl = b.rolling(60, min_periods=40).median().shift(1).values
        for k in (20, 30, 40):
            cyc, rel, pos = simulate(b, lambda i, k=k: lvl[i] - k if not np.isnan(lvl[i]) else -1e9,
                                     lambda i, k=k: lvl[i] + k if not np.isnan(lvl[i]) else 1e9, cs, 1)
            rows.append(metrics(f'nível móvel 60d ±{k}', cyc, rel, pos, {'cenario_custos': scen, 'custo_ciclo_bps': 2 * cs, 'k_bps': k, 'lag_pregoes': 1, 'regra': 'nivel_movel_60d', 'papel': 'sensibilidade'}))
    years = (b.index[-1] - b.index[0]).days / YEAR_D
    for scen, s in SCENARIOS.items():
        cs = side_cost(s)
        rows.append({'config': 'sempre PAXG', 'cenario_custos': scen, 'regra': 'referencia', 'papel': 'referencia',
                     'ganho_anual_vs_gldm_bps': float((b.iloc[-1] - b.iloc[0] + GLDM_FEE * years - 2 * cs) / years), 'ciclos': 1})
    table = pd.DataFrame(rows)
    save_csv(table, 'T12_rotacao_resumo.csv')

    cyc, rel, pos, k, cs = primary['intermediario']
    save_csv(cyc, 'T12_rotacao_ciclos.csv')
    curve = pd.DataFrame({'dia': rel.index, 'desvio_bps': b.values, 'em_paxg': pos.values,
                          'ganho_acumulado_bps': rel.cumsum().values,
                          'ganho_acumulado_original_bps': primary['original'][1].cumsum().values})
    save_csv(curve, 'T12_rotacao_curva.csv')
    sims = placebo(b, len(cyc), cyc.dias.tolist(), cs)
    save_csv(pd.DataFrame({'ganho_anual_bps': sims}), 'T12_rotacao_placebo_dist.csv')
    actual = rel.sum() / years
    yearly = rel.groupby(rel.index.year).sum()
    dump_json(ROOT / 'results/T12_rotacao_placebo.json', {
        'regra': f'faixa fixa ±{k} bps, lag 1 pregão, cenário intermediário', 'ganho_anual_bps': float(actual),
        'placebo_media_bps': float(sims.mean()), 'placebo_p95_bps': float(np.percentile(sims, 95)),
        'fracao_placebos_acima': float((sims >= actual).mean()), 'simulacoes': int(len(sims)),
        'ganho_por_ano_calendario_bps': {int(y): float(v) for y, v in yearly.items()},
        'dias_uteis': int(len(b)), 'inicio': str(b.index[0].date()), 'fim': str(b.index[-1].date())})
    return table


def run_weekend():
    w = pd.read_parquet(ROOT / 'data/panel/panel_weekends.parquet')
    w = w[w.valid].copy()
    w['ano'] = pd.to_datetime(w.week).dt.year
    rows = []
    for name, d in [('todos', w), *[(str(y), g) for y, g in w.groupby('ano')]]:
        r = sm.OLS(d.g, sm.add_constant(d.m)).fit(cov_type='HC1')
        prem = d.b_0 - d.b_c
        rows.append({'periodo': name, 'fins_de_semana': len(d), 'beta_gap_ouro_em_mov_paxg': float(r.params.iloc[1]),
                     'beta_ep': float(r.bse.iloc[1]), 'r2': float(r.rsquared),
                     'premio_fds_media_bps': float(prem.mean()), 'premio_fds_mediana_bps': float(prem.median())})
    save_csv(pd.DataFrame(rows), 'T13_fim_de_semana.csv')
    prem = (w.b_0 - w.b_c).values
    rng = np.random.default_rng(3)
    boots = np.array([np.median(rng.choice(prem, len(prem))) for _ in range(5000)])
    dump_json(ROOT / 'results/T13_fim_de_semana_resumo.json', {
        'premio_fds_media_bps': float(prem.mean()), 'premio_fds_media_ep': float(prem.std(ddof=1) / np.sqrt(len(prem))),
        'premio_fds_mediana_bps': float(np.median(prem)), 'premio_fds_mediana_ic90': [float(x) for x in np.percentile(boots, [5, 95])],
        'fracao_positiva': float((prem > 0).mean()),
        'variacao_media_ate_1h_bps': float((w.b_1h - w.b_c).mean()), 'variacao_media_ate_7h_bps': float((w.b_7h - w.b_c).mean()),
        'desvio_padrao_gap_ouro_bps': float(w.g.std()), 'desvio_padrao_mov_paxg_bps': float(w.m.std()),
        'r2_reabertura_em_sexta': float(np.corrcoef(w.b_c, w.b_0)[0, 1] ** 2),
        'r2_7h_em_sexta': float(np.corrcoef(w.b_c, w.b_7h)[0, 1] ** 2),
        'mesmo_sinal_sexta_reabertura': float((np.sign(w.b_c) == np.sign(w.b_0)).mean())})


def run_basis_risk():
    b = daily_basis()
    rows = []
    for h, label in [(5, '1 semana'), (21, '1 mês'), (63, '3 meses'), (126, '6 meses'), (252, '12 meses')]:
        ch = (b.shift(-h) - b).dropna()
        rows.append({'horizonte': label, 'pregoes': h, 'n': len(ch), 'desvio_padrao_bps': float(ch.std()),
                     'p05_bps': float(ch.quantile(.05)), 'p95_bps': float(ch.quantile(.95)), 'media_abs_bps': float(ch.abs().mean()),
                     'taxa_gldm_no_horizonte_bps': GLDM_FEE * h / 252, 'taxa_gld_no_horizonte_bps': 40 * h / 252})
    save_csv(pd.DataFrame(rows), 'T14_risco_de_base.csv')


def run_components():
    b = daily_basis()
    m = sm.tsa.UnobservedComponents(b.values, level='llevel', autoregressive=1).fit(disp=False)
    par = dict(zip(m.param_names, m.params))
    phi = par['ar.L1']
    level = m.smoothed_state[0]
    save_csv(pd.DataFrame({'dia': b.index, 'desvio_bps': b.values, 'nivel_suavizado_bps': level}), 'T15_componentes_serie.csv')
    dump_json(ROOT / 'results/T15_componentes.json', {
        'modelo': 'nível local (passeio aleatório) + componente AR(1) + ruído; dias úteis, média 15-20 UTC',
        'phi_ar1': float(phi), 'meia_vida_transitorio_pregoes': float(np.log(.5) / np.log(phi)),
        'dp_choque_nivel_bps_dia': float(np.sqrt(par['sigma2.level'])), 'dp_choque_nivel_bps_ano': float(np.sqrt(252 * par['sigma2.level'])),
        'dp_choque_ar_bps': float(np.sqrt(par['sigma2.ar'])), 'dp_ruido_bps': float(np.sqrt(par['sigma2.irregular'])),
        'parametros': {k: float(v) for k, v in par.items()}, 'loglik': float(m.llf), 'n': int(len(b))})


def run_error_correction():
    """Retorno diário do PAXG contra o retorno do ouro e o desvio da véspera (erros robustos HAC)."""
    p = pd.read_parquet(ROOT / 'data/panel/panel_hourly.parquet')
    p = p[p.valid]
    s = p[(p.t.dt.dayofweek < 5) & (p.t.dt.hour.isin(SESSION_HOURS))].copy()
    s['d'] = s.t.dt.tz_localize(None).dt.floor('D')
    d = s.groupby('d').agg(b=('basis_log_bps', 'mean'), S=('S', 'mean'), P=('p_usd', 'mean'), vol=('vol_token_usd', 'sum'), n=('S', 'size'))
    d = d[(d.n >= 4) & (~d.index.isin(NYSE_HOLIDAYS))]
    d['ret_ouro'] = 1e4 * np.log(d.S).diff()
    d['ret_paxg'] = 1e4 * np.log(d.P).diff()
    d['desvio_vespera'] = d.b.shift(1)
    d['ret_ouro_vespera'] = d.ret_ouro.shift(1)
    x = d.dropna()
    r = sm.OLS(x.ret_paxg, sm.add_constant(x[['ret_ouro', 'ret_ouro_vespera', 'desvio_vespera']])).fit(cov_type='HAC', cov_kwds={'maxlags': 5})
    w = d.resample('W-FRI').last()
    w['ret_ouro_sem'] = 1e4 * np.log(w.S).diff()
    w['var_desvio_sem'] = w.b.diff()
    w = w.dropna()
    rw = sm.OLS(w.var_desvio_sem, sm.add_constant(w.ret_ouro_sem)).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
    gamma = -float(r.params['desvio_vespera'])
    vol = d.vol.groupby(d.index.year).median()
    dump_json(ROOT / 'results/T16_correcao_de_erro.json', {
        'modelo': 'ret_paxg_t = a + b0 ret_ouro_t + b1 ret_ouro_{t-1} - g desvio_{t-1}; dias úteis NYSE, média 15-20 UTC, bps',
        'n': int(len(x)), 'r2': float(r.rsquared),
        'coef': {k: float(v) for k, v in r.params.items()}, 'ep_hac': {k: float(v) for k, v in r.bse.items()},
        'correcao_diaria': gamma, 'meia_vida_pregoes': float(np.log(.5) / np.log(1 - gamma)),
        'semanal_var_desvio_em_ret_ouro': {'beta': float(rw.params['ret_ouro_sem']), 'ep_hac': float(rw.bse['ret_ouro_sem']), 'r2': float(rw.rsquared)},
        'volume_binance_sessao_mediana_usd_por_ano': {int(k): float(v) for k, v in vol.items()},
        'capacidade_5pct_sessao_usd_por_ano': {int(k): float(v * .05) for k, v in vol.items()}})


def run_all_v5():
    run_rotation()
    run_weekend()
    run_basis_risk()
    run_components()
    run_error_correction()


if __name__ == '__main__':
    run_all_v5()
    t = pd.read_csv(ROOT / 'results/T12_rotacao_resumo.csv')
    print(t.round(2).to_string())
