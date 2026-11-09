"""Entrega v2 · Fase 2: a mesma regra de rotação aplicada ao XAUT (Tether Gold), sem reestimar nada.

Uso: python -m src.v2_xaut
Saídas em results/v2/: T17_xaut_resumo.csv, T17_xaut_curva.csv, T17_xaut_ciclos.csv, T17_xaut_resumo.json

Pré-registro (PLANO_ENTREGA_V2.md, seção 3), fixado antes do download:
- Bitfinex tXAUT:USD, candles de 1 h; checagem com tXAUT:UST × USDT/USD da Bitfinex.
- Ouro: XAUUSD Dukascopy (média de compra e venda no fechamento da barra), só com cotação ativa.
- Sessão: dias úteis da NYSE, barras com fechamento 15–20 UTC; dia válido com ≥4 barras (sensibilidade: ≥2).
- Regra idêntica à do PAXG: faixa ±19, atraso de 1 pregão, custos intermediários, GLDM como referência.
- Cenários adicionais: custos originais (±37) e custos atuais da Bitfinex (taxa zero na página oficial em 08/11/2026;
  spread de 2,2 bps no livro de 08/11/2026; faixa = custo do ciclo). Desvio do pré-registro: o spread vem do livro
  atual, e não da amplitude alta−baixa da hora, porque a amplitude mede variação de preço, não spread.
É um teste fora da amostra entre ativos, no mesmo período, e não em datas novas.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .common import ROOT, dump_json
from .rotation import GLDM_FEE, NYSE_HOLIDAYS, SESSION_HOURS, YEAR_D, metrics, placebo, simulate

OUT = ROOT / 'results' / 'v2'
CUTOFF = pd.Timestamp('2026-11-08', tz='UTC')
SPREAD_BITFINEX_ATUAL = 2.2  # bps, livro tXAUT:USD em 08/11/2026 (bid 4051,1; ask 4052,0)
SCENARIOS_XAUT = {
    'intermediario': {'token_fee': 5, 'token_spread': 2, 'conversion_rt': 2, 'slippage': 2, 'etf_spread': 1},
    'original': {'token_fee': 10, 'token_spread': 10, 'conversion_rt': 2, 'slippage': 2, 'etf_spread': 1},
    'bitfinex_atual': {'token_fee': 0, 'token_spread': SPREAD_BITFINEX_ATUAL, 'conversion_rt': 0, 'slippage': 2, 'etf_spread': 1},
}


def side_cost(s):
    return s['token_fee'] + s['token_spread'] / 2 + s['conversion_rt'] / 2 + s['slippage'] + s['etf_spread'] / 2


def load_candles(name):
    raw = json.loads((ROOT / f'data/raw/bitfinex_xaut/{name}-1h-2020-08-28-2026-11-08.json').read_text())
    c = pd.DataFrame(raw, columns=['mts', 'open', 'close', 'high', 'low', 'volume'])
    c['t'] = pd.to_datetime(c.mts, unit='ms', utc=True) + pd.Timedelta(hours=1)  # candle marcado na abertura
    return c[(c.volume > 0) & (c.t <= CUTOFF)][['t', 'close', 'volume']]


def hourly_basis(pair='USD'):
    gold = pd.read_parquet(ROOT / 'data/interim/gold_1h.parquet')
    gold = gold[gold.quote_active & gold.valid_quotes][['bar_end', 'mid_close']].rename(columns={'bar_end': 't', 'mid_close': 'S'})
    c = load_candles('XAUTUSD' if pair == 'USD' else 'XAUTUST')
    m = c.merge(gold, on='t', how='inner')
    if pair == 'UST':
        q = pd.read_parquet(ROOT / 'data/panel/panel_hourly.parquet')[['t', 'q', 'fx_has_trade']]
        q = q[q.fx_has_trade & q.q.notna()]
        m = m.merge(q[['t', 'q']], on='t', how='inner')
        m['close'] = m.close * m.q
    m['basis_bps'] = 1e4 * np.log(m.close / m.S)
    return m


def daily_from_hourly(h, min_bars=4):
    """Média diária do desvio nas horas de pregão comuns; usa só barras do próprio dia."""
    s = h[(h.t.dt.dayofweek < 5) & (h.t.dt.hour.isin(SESSION_HOURS))].copy()
    s['dia'] = s.t.dt.tz_localize(None).dt.floor('D')
    g = s.groupby('dia').basis_bps.agg(['mean', 'count'])
    g = g[(g['count'] >= min_bars) & (~g.index.isin(NYSE_HOLIDAYS))]
    return g['mean']


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, keep = [], {}
    paxg = pd.read_csv(ROOT / 'results/T12_rotacao_curva.csv', parse_dates=['dia']).set_index('dia').desvio_bps
    series = {}
    for pair in ('USD', 'UST'):
        h = hourly_basis(pair)
        for min_bars in (4, 2):
            b = daily_from_hourly(h, min_bars)
            series[(pair, min_bars)] = b
            for scen, s in SCENARIOS_XAUT.items():
                cs = side_cost(s)
                k = int(round(2 * cs))
                for lag in (1, 2):
                    if lag == 2 and not (pair == 'USD' and min_bars == 4):
                        continue
                    cyc, rel, pos = simulate(b, lambda i, k=k: -k, lambda i, k=k: k, cs, lag)
                    if len(cyc) == 0:
                        rows.append({'par': f'XAUT/{pair}', 'min_barras': min_bars, 'cenario_custos': scen, 'k_bps': k, 'lag_pregoes': lag, 'ciclos': 0})
                        continue
                    tag = 'principal' if (pair == 'USD' and min_bars == 4 and scen == 'intermediario' and lag == 1) else 'sensibilidade'
                    rows.append(metrics(f'XAUT/{pair} ±{k}', cyc, rel, pos, {'par': f'XAUT/{pair}', 'min_barras': min_bars, 'cenario_custos': scen,
                                                                            'custo_ciclo_bps': 2 * cs, 'k_bps': k, 'lag_pregoes': lag, 'papel': tag,
                                                                            'dias_validos': len(b)}))
                    if tag == 'principal':
                        keep = {'cyc': cyc, 'rel': rel, 'pos': pos, 'b': b, 'cs': cs, 'k': k}
    table = pd.DataFrame(rows)
    table.to_csv(OUT / 'T17_xaut_resumo.csv', index=False, encoding='utf-8-sig', float_format='%.10g')
    cyc, rel, pos, b, cs, k = keep['cyc'], keep['rel'], keep['pos'], keep['b'], keep['cs'], keep['k']
    cyc.to_csv(OUT / 'T17_xaut_ciclos.csv', index=False, encoding='utf-8-sig', float_format='%.10g')
    pd.DataFrame({'dia': rel.index, 'desvio_bps': b.values, 'em_xaut': pos.values, 'ganho_acumulado_bps': rel.cumsum().values}).to_csv(
        OUT / 'T17_xaut_curva.csv', index=False, encoding='utf-8-sig', float_format='%.10g')
    years = (b.index[-1] - b.index[0]).days / YEAR_D
    sims = placebo(b, len(cyc), cyc.dias.tolist(), cs)
    actual = rel.sum() / years
    both = pd.concat([b.rename('xaut'), paxg.rename('paxg')], axis=1, join='inner')
    month = b.groupby(b.index.to_period('M')).transform('mean')
    possible = pd.bdate_range(b.index.min(), b.index.max())
    possible = possible[~possible.isin(NYSE_HOLIDAYS)]
    dump_json(OUT / 'T17_xaut_resumo.json', {
        'regra': f'faixa fixa ±{k} bps, atraso de 1 pregão, custos intermediários (idêntica ao PAXG)',
        'fonte': 'Bitfinex tXAUT:USD 1h; ouro Dukascopy XAUUSD',
        'dias_validos': int(len(b)), 'dias_uteis_possiveis': int(len(possible)), 'cobertura_dias': float(len(b) / len(possible)),
        'inicio': str(b.index[0].date()), 'fim': str(b.index[-1].date()),
        'desvio_mediano_abs_bps': float(b.abs().median()), 'desvio_medio_bps': float(b.mean()),
        'variancia_explicada_nivel_mes': float(1 - ((b - month) ** 2).sum() / ((b - b.mean()) ** 2).sum()),
        'correlacao_diaria_com_paxg': float(both.xaut.corr(both.paxg)), 'dias_em_comum_com_paxg': int(len(both)),
        'ganho_anual_bps': float(actual), 'placebo_media_bps': float(sims.mean()), 'placebo_p95_bps': float(np.percentile(sims, 95)),
        'fracao_placebos_acima': float((sims >= actual).mean()), 'simulacoes': int(len(sims)),
        'ganho_por_ano_calendario_bps': {int(y): float(v) for y, v in rel.groupby(rel.index.year).sum().items()},
        'spread_bitfinex_atual_bps': SPREAD_BITFINEX_ATUAL,
        'desvio_do_pre_registro': 'spread do cenário Bitfinex medido no livro de 08/11/2026, não pela amplitude da hora',
        'escopo': 'fora da amostra entre ativos, mesmo período; não é teste em datas novas'})
    return table


if __name__ == '__main__':
    t = run()
    cols = ['par', 'min_barras', 'cenario_custos', 'k_bps', 'lag_pregoes', 'dias_validos', 'ciclos', 'ciclos_positivos', 'ganho_anual_vs_gldm_bps', 'ic90_lo', 'ic90_hi', 'razao_informacao', 'pior_queda_bps', 'ganho_anual_1a_metade', 'ganho_anual_2a_metade']
    print(t[[c for c in cols if c in t.columns]].round(2).to_string())
    print(json.dumps(json.loads((OUT / 'T17_xaut_resumo.json').read_text(encoding='utf-8')), indent=1, ensure_ascii=False))
