"""Entrega v2 · Fase 3: emissão e resgate do PAXG no Ethereum contra o desvio.

Uso: python -m src.v2_onchain            (usa o cache em data/raw/blockscout)
     python -m src.v2_onchain --baixar   (baixa os eventos pela API pública do Blockscout)
Saídas em results/v2/: T18_onchain_semanal.csv, T18_onchain_resumo.json

Pré-registro (PLANO_ENTREGA_V2.md, seção 3): eventos Transfer do contrato PAXG de/para o endereço zero;
emissão líquida semanal (onças) contra o desvio médio semanal; correlação do desvio da semana t com a emissão
das semanas t+1 a t+4; regressões com defasagens de 1 a 4 semanas nos dois sentidos, erros HAC; amostra
completa e até mai/2025 (antes da emissão nativa em Solana). Associação, não causa. A Paxos emite em lotes
para a tesouraria, então a data do evento não é a data da compra do cliente.
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .common import ROOT, dump_json

OUT = ROOT / 'results' / 'v2'
RAW = ROOT / 'data/raw/blockscout'
PAXG = '0x45804880De22913dAFE09f4980848ECE6EcbAf78'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO = '0x' + '0' * 64
# The legacy route is still available without the rate-limited API-key gate;
# it exposes the same Etherscan-compatible getLogs response used below.
API = 'https://eth.blockscout.com/api/legacy/logs/get-logs'


def fetch(side, first=8_000_000, last=26_380_000, step=100_000):
    import requests
    par = {'topic1': ZERO, 'topic0_1_opr': 'and'} if side == 'mint' else {'topic2': ZERO, 'topic0_2_opr': 'and'}
    out, queue = [], [(a, min(a + step - 1, last)) for a in range(first, last + 1, step)]
    while queue:
        a, z = queue.pop(0)
        for attempt in range(10):
            try:
                r = requests.get(API, params={'module': 'logs', 'action': 'getLogs', 'address': PAXG, 'topic0': TRANSFER,
                                              'fromBlock': a, 'toBlock': z, **par}, timeout=90)
                res = r.json().get('result')
                if isinstance(res, list):
                    break
            except Exception:
                res = None
            # Blockscout occasionally returns a transient 429/500 for a valid
            # range; waiting here is preferable to treating it as a data gap.
            time.sleep(2 + 2 * attempt)
        if res is None or not isinstance(res, list):
            if z - a > 2_000:
                mid = (a + z) // 2
                queue[:0] = [(a, mid), (mid + 1, z)]
                continue
            raise RuntimeError(f'falha em {side} {a}-{z}')
        if len(res) >= 1000:
            mid = (a + z) // 2
            queue[:0] = [(a, mid), (mid + 1, z)]
            continue
        out += [{'bloco': int(x['blockNumber'], 16), 'tempo': int(x['timeStamp'], 16), 'tx': x['transactionHash'],
                 'onças': int(x['data'], 16) / 1e18} for x in res]
        time.sleep(0.4)
    df = pd.DataFrame(out).drop_duplicates(['tx', 'bloco', 'onças'])
    RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW / f'paxg_{side}.csv', index=False)
    (RAW / f'paxg_{side}.csv.meta.json').write_text(json.dumps({'api': API, 'contrato': PAXG, 'evento': 'Transfer', 'lado': side,
                                                                 'blocos': [first, last], 'linhas': len(df),
                                                                 'baixado_utc': pd.Timestamp.now('UTC').isoformat()}, indent=1))
    return df


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    mint = pd.read_csv(RAW / 'paxg_mint.csv')
    burn = pd.read_csv(RAW / 'paxg_burn.csv')
    for d, s in [(mint, 1), (burn, -1)]:
        d['dia'] = pd.to_datetime(d.tempo, unit='s', utc=True).dt.tz_localize(None).dt.floor('D')
        d['liq'] = s * d['onças']
    ev = pd.concat([mint[['dia', 'liq']], burn[['dia', 'liq']]])
    supply = ev.sort_values('dia').set_index('dia').liq.cumsum()
    serie = pd.read_csv(ROOT / 'results/T15_componentes_serie.csv', parse_dates=['dia']).set_index('dia')
    wk = pd.DataFrame({'desvio_bps': serie.desvio_bps.resample('W-FRI').mean(),
                       'nivel_bps': serie.nivel_suavizado_bps.resample('W-FRI').mean()})
    flows = ev.set_index('dia').liq.resample('W-FRI').sum()
    gross_m = mint.set_index('dia')['onças'].resample('W-FRI').sum()
    gross_b = burn.set_index('dia')['onças'].resample('W-FRI').sum()
    sup = supply.resample('W-FRI').last().ffill()
    wk = wk.join(flows.rename('emissao_liquida_oz'), how='left').join(gross_m.rename('emissao_oz')).join(gross_b.rename('resgate_oz')).join(sup.rename('oferta_eth_oz'))
    wk[['emissao_liquida_oz', 'emissao_oz', 'resgate_oz']] = wk[['emissao_liquida_oz', 'emissao_oz', 'resgate_oz']].fillna(0)
    wk = wk.dropna(subset=['desvio_bps'])
    wk['oferta_eth_oz'] = wk.oferta_eth_oz.ffill()
    wk['emissao_liquida_pct'] = 100 * wk.emissao_liquida_oz / wk.oferta_eth_oz.shift(1)
    wk['emissao_prox_4s_pct'] = sum(wk.emissao_liquida_pct.shift(-j) for j in range(1, 5))
    wk.reset_index(names='semana').to_csv(OUT / 'T18_onchain_semanal.csv', index=False, encoding='utf-8-sig', float_format='%.10g')

    def tests(d, label):
        d = d.copy()
        res = {'amostra': label, 'semanas': int(len(d))}
        x = d.dropna(subset=['emissao_prox_4s_pct'])
        res['corr_desvio_t_emissao_t1_t4'] = float(x.desvio_bps.corr(x.emissao_prox_4s_pct))
        res['corr_desvio_t_emissao_t'] = float(d.desvio_bps.corr(d.emissao_liquida_pct))
        lags = pd.concat({f'desvio_l{j}': d.desvio_bps.shift(j) for j in range(1, 5)}, axis=1)
        y = d.emissao_liquida_pct
        z = pd.concat([y.rename('y'), lags], axis=1).dropna()
        r = sm.OLS(z.y, sm.add_constant(z.drop(columns='y'))).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
        res['emissao_em_desvio_defasado'] = {'coef': {k: float(v) for k, v in r.params.items()}, 'ep_hac': {k: float(v) for k, v in r.bse.items()},
                                             'soma_coef_lags': float(r.params.drop('const').sum()), 'r2': float(r.rsquared),
                                             'p_conjunto': float(r.f_test(' = '.join([]) or np.eye(len(r.params))[1:]).pvalue)}
        dz = pd.concat([d.desvio_bps.diff().rename('ddesvio'), *(d.emissao_liquida_pct.shift(j).rename(f'em_l{j}') for j in range(1, 5)),
                        d.desvio_bps.shift(1).rename('desvio_l1')], axis=1).dropna()
        r2 = sm.OLS(dz.ddesvio, sm.add_constant(dz.drop(columns='ddesvio'))).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
        res['variacao_desvio_em_emissao_defasada'] = {'coef': {k: float(v) for k, v in r2.params.items()}, 'ep_hac': {k: float(v) for k, v in r2.bse.items()},
                                                      'r2': float(r2.rsquared), 'p_conjunto_emissao': float(r2.f_test(np.eye(len(r2.params))[1:5]).pvalue)}
        prem, disc = d[d.desvio_bps > 25], d[d.desvio_bps < -25]
        res['emissao_prox_4s_media_pct_quando_premio_25'] = float(prem.emissao_prox_4s_pct.mean())
        res['emissao_prox_4s_media_pct_quando_desconto_25'] = float(disc.emissao_prox_4s_pct.mean())
        res['semanas_premio_25'], res['semanas_desconto_25'] = int(len(prem)), int(len(disc))
        return res

    full = tests(wk, 'completa')
    pre = tests(wk[wk.index < '2025-06-01'], 'até mai/2025')
    dump_json(OUT / 'T18_onchain_resumo.json', {
        'fonte': 'Blockscout (eth.blockscout.com), eventos Transfer do contrato PAXG de/para o endereço zero',
        'emissoes': int(len(mint)), 'resgates': int(len(burn)),
        'oferta_eth_inicio_oz': float(wk.oferta_eth_oz.dropna().iloc[0]), 'oferta_eth_fim_oz': float(wk.oferta_eth_oz.dropna().iloc[-1]),
        'testes': [full, pre],
        'ressalvas': ['emissão em lotes para a tesouraria: data do evento ≠ data da compra do cliente',
                      'desde jun/2025 o PAXG também é emitido em Solana; a oferta no Ethereum deixa de ser a oferta total',
                      'associação, não causa']})
    return full, pre


if __name__ == '__main__':
    if '--baixar' in sys.argv:
        for side in ('mint', 'burn'):
            d = fetch(side)
            print(side, len(d), d.onças.sum())
    f, p = run()
    print(json.dumps([f, p], indent=1, ensure_ascii=False, default=float)[:4000])
