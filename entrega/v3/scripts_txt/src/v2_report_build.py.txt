"""Entrega v2: monta e exporta os 10 slides e o material suplementar em arquivos próprios (slides/entrega_v2*).

Uso: python -m src.v2_report_build
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from .common import ROOT, dump_json, utc_now
from .report_v5 import CSS, fig, fig_placebo, num, page, pct
from .v2_report_pages import build_main, load

NAMES = {'persistence': 'Repetir o último valor', 'zero_basis': 'Assumir desvio zero', 'historical_mean': 'Média histórica',
         'linear_adjustment': 'Modelo linear', 'linear_adjustment_context': 'Linear com ouro e volatilidade'}


def count_tests():
    out = subprocess.run([sys.executable, '-m', 'pytest', '--collect-only', '-q'], cwd=ROOT, capture_output=True, text=True).stdout
    m = re.search(r'(\d+) tests? collected', out)
    return int(m.group(1)) if m else len(re.findall(r'^tests/.*::', out, flags=re.M))


def build_supp(D):
    S = D['S']
    pages = []
    total = 6
    # A1
    g, bud = D['grid'], D['budget'].set_index('horizon_hours')
    rows = ''.join(f'<tr><td>{int(r.horizon_hours)} h</td><td class="n">{int(r.configurations)}</td><td class="n">{int(r.evaluated_trades)}</td>'
                   f'<td class="n">{num(bud.loc[r.horizon_hours, "mean_gross_bps"], 1)} [{num(bud.loc[r.horizon_hours, "gross_lo"], 1)}; {num(bud.loc[r.horizon_hours, "gross_hi"], 1)}]</td>'
                   f'<td class="n">{num(r.best_mean_model_bps, 1)}</td><td class="n">{num(r.worst_mean_model_bps, 1)}</td></tr>' for _, r in g.iterrows())
    fc = D['fc']
    frows = ''.join(f'<tr><td>{NAMES[m]}</td><td class="n">{num(fc.loc[m, "mae_bps"], 2)}</td><td class="n">{num(fc.loc[m, "rmse_bps"], 2)}</td>'
                    f'<td class="n">{num(fc.loc[m, "mae_difference_vs_persistence"], 2)} [{num(fc.loc[m, "difference_lo"], 2)}; {num(fc.loc[m, "difference_hi"], 2)}]</td></tr>' for m in NAMES)
    conv = D['conv']
    srows = ''.join(f'<tr><td>{lab}</td><td class="n">{num(conv[k].mean_model_bps, 1)}</td><td class="n">{num(conv[k].median_model_bps, 1)}</td><td class="n">{num(conv[k].worst_model_bps, 1)}</td><td class="n">{pct(conv[k].positive_fraction)}</td></tr>'
                    for k, lab in [('orig', 'Original: taxa 10, spread 10, ouro 1, câmbio 2, deslizamento 2'), ('mid', 'Intermediário: taxa 5, spread 2, ouro 1, câmbio 2, deslizamento 2'), ('low', 'Mínimo: taxa 2, spread 2, ouro 1, câmbio 0, deslizamento 0')])
    body = f"""<div class="grid" style="grid-template-columns:1fr 1fr;gap:34px">
<div><div class="h">Grade de custos da operação de convergência</div>
<table><thead><tr><th>Prazo</th><th class="n">Combinações</th><th class="n">Operações</th><th class="n">Bruto [IC 95%]</th><th class="n">Melhor média</th><th class="n">Pior média</th></tr></thead><tbody>{rows}</tbody></table>
<p class="small" style="margin-top:8px">Em bps por operação. As combinações variam taxa do token (2, 5, 10), spread (2, 10, 25), comissão do ouro (1, 2), câmbio (0, 2, 10), deslizamento (0, 2, 5) e custo residual (0, 5, 25). Não são independentes; o melhor caso foi escolhido depois de ver o resultado.</p>
<div class="h" style="margin-top:14px">Três cenários, posição de 6 horas</div>
<table><thead><tr><th>Cenário</th><th class="n">Média</th><th class="n">Mediana</th><th class="n">Pior</th><th class="n">Positivas</th></tr></thead><tbody>{srows}</tbody></table></div>
<div><div class="h">Previsão do desvio em +7 h</div>
<table><thead><tr><th>Método</th><th class="n">Erro médio abs.</th><th class="n">Raiz do erro quad.</th><th class="n">Diferença vs. repetir [IC 95%]</th></tr></thead><tbody>{frows}</tbody></table>
<p class="small" style="margin-top:8px">Alvo: desvio 7 h depois da reabertura, com a informação de 1 h depois. Treino expansivo a partir de 104 semanas; {int(fc.loc['persistence', 'n_test'])} previsões de ago/2022 a nov/2026 na mesma amostra; intervalos por blocos de semanas. Sem busca de parâmetros. Análise posterior aos resultados originais, sem teste em dados novos.</p>
<div class="h" style="margin-top:14px">Sinais sem avaliação completa</div>
<p>Dos {int(S['trade_signals'])} sinais de 6 h, {int(S['signals_unassessed'])} não tinham preço de saída observável. Para que o saldo médio original dos 60 chegasse a zero, eles precisariam render em média {num(S['refined_missing_tipping_mean_bps'], 0)} bps. Isso é um limiar, não uma estimativa.</p></div></div>"""
    pages.append(page(1, 'Arbitragem em horas: grade de custos e modelos de previsão', body, supp=True, total=total))

    # A2
    t1 = D['t1'][D['t1'].period == 'full'].set_index('sample')
    lab = {'common_hours': 'Horas comuns', 'reopen': 'Reabertura', 'one_hour': '1 h depois', 'seven_hours': '7 h depois'}
    trows = ''.join(f'<tr><td>{lab[s]}</td><td class="n">{num(t1.loc[s, "n"], 0)}</td><td class="n">{num(t1.loc[s, "median_abs_bps"], 1)} [{num(t1.loc[s, "median_abs_bps_lo"], 1)}; {num(t1.loc[s, "median_abs_bps_hi"], 1)}]</td>'
                    f'<td class="n">{num(t1.loc[s, "p95_abs_bps"], 1)}</td><td class="n">{pct(t1.loc[s, "above_50_fraction"])}</td><td class="n">{num(t1.loc[s, "mean_signed_bps"], 1, True)}</td></tr>' for s in lab)
    pr = D['pair']
    plab = {'b_c_to_b_0': 'Sexta → reabertura', 'b_0_to_b_1h': 'Reabertura → 1 h', 'b_0_to_b_7h': 'Reabertura → 7 h'}
    prows = ''.join(f'<tr><td>{plab[c]}</td><td class="n">{int(pr.loc[c, "paired_n"])}</td><td class="n">{num(pr.loc[c, "mean_abs_change_bps"], 1, True)} [{num(pr.loc[c, "mean_lo"], 1)}; {num(pr.loc[c, "mean_hi"], 1)}]</td><td class="n">{pct(pr.loc[c, "fraction_abs_decreases"])}</td></tr>' for c in plab)
    fx = D['fx']
    fxrows = ''.join(f'<tr><td>{int(r.fx_window_minutes)} min</td><td class="n">{int(r.horizon_hours)} h</td><td class="n">{int(r.signals)}</td><td class="n">{int(r.evaluated_trades)}</td><td class="n">{int(r.unassessed_signals)}</td><td class="n">{num(r.mean_model_bps, 1)}</td></tr>' for _, r in fx.iterrows())
    t13 = D['t13']
    wrows = ''.join(f'<tr><td>{r.periodo}</td><td class="n">{int(r.fins_de_semana)}</td><td class="n">{num(r.beta_gap_ouro_em_mov_paxg, 2)} ({num(r.beta_ep, 2)})</td><td class="n">{num(r.r2, 2)}</td><td class="n">{num(r.premio_fds_media_bps, 1, True)}</td><td class="n">{num(r.premio_fds_mediana_bps, 1, True)}</td></tr>' for _, r in t13.iterrows())
    body = f"""<div class="grid" style="grid-template-columns:1fr 1fr;gap:34px">
<div><div class="h">Desvio absoluto em horas comuns e na reabertura</div>
<table><thead><tr><th>Amostra</th><th class="n">n</th><th class="n">Mediana [IC 95%]</th><th class="n">p95</th><th class="n">&gt; 50 bps</th><th class="n">Média c/ sinal</th></tr></thead><tbody>{trows}</tbody></table>
<div class="h" style="margin-top:14px">Mudança do desvio absoluto nos mesmos fins de semana</div>
<table><thead><tr><th>Comparação</th><th class="n">Pares</th><th class="n">Média [IC 95%]</th><th class="n">Semanas com queda</th></tr></thead><tbody>{prows}</tbody></table>
<p class="small" style="margin-top:8px">Intervalos por bootstrap em blocos de semanas do calendário, exploratórios. Mudança do desvio absoluto não é lucro de uma operação.</p></div>
<div><div class="h">Fim de semana por ano</div>
<table><thead><tr><th>Período</th><th class="n">Fins de semana</th><th class="n">β (ep HC1)</th><th class="n">R²</th><th class="n">Prêmio médio</th><th class="n">Mediana</th></tr></thead><tbody>{wrows}</tbody></table>
<p class="small" style="margin-top:6px">β e R² da regressão do salto de reabertura do ouro no movimento do PAXG de sexta à reabertura. Prêmio: variação do desvio de sexta à reabertura.</p>
<div class="h" style="margin-top:14px">Janela de busca do câmbio na operação de convergência</div>
<table><thead><tr><th>Janela</th><th class="n">Prazo</th><th class="n">Sinais</th><th class="n">Avaliados</th><th class="n">Sem avaliação</th><th class="n">Saldo médio</th></tr></thead><tbody>{fxrows}</tbody></table>
<p class="small" style="margin-top:6px">Custos originais. Com 5 minutos, usamos o último câmbio já fechado, de até 4 minutos antes; token e ouro seguem no minuto exato.</p></div></div>"""
    pages.append(page(2, 'Fidelidade, fim de semana e câmbio', body, supp=True, total=total))

    # A3
    rot = D['rot']
    rr = rot[rot.papel != 'referencia']
    grows = ''.join(f'<tr class="{"hl" if r.papel == "principal" else ""}"><td>{r.config}</td><td>{"intermediário" if r.cenario_custos == "intermediario" else "original"}</td><td class="n">{int(r.lag_pregoes)}</td><td class="n">{int(r.ciclos)}</td><td class="n">{pct(r.ciclos_positivos)}</td>'
                    f'<td class="n">{num(r.ganho_anual_vs_gldm_bps, 0, True)}</td><td class="n">[{num(r.ic90_lo, 0)}; {num(r.ic90_hi, 0)}]</td><td class="n">{num(r.razao_informacao, 2)}</td>'
                    f'<td class="n">{num(r.ganho_anual_1a_metade, 0, True)}</td><td class="n">{num(r.ganho_anual_2a_metade, 0, True)}</td><td class="n">{num(r.pior_queda_bps, 0)}</td></tr>' for _, r in rr.iterrows())
    plac = D['plac']
    body = f"""<div class="grid" style="grid-template-columns:1.65fr 1fr;gap:30px">
<div><div class="h">Rotação GLDM ↔ PAXG: todas as configurações testadas</div>
<table class="tight tighter"><thead><tr><th>Regra</th><th>Custos</th><th class="n">Atraso</th><th class="n">Ciclos</th><th class="n">Pos.</th><th class="n">bps/ano</th><th class="n">IC 90%</th><th class="n">RI</th><th class="n">1ª metade</th><th class="n">2ª metade</th><th class="n">Pior queda</th></tr></thead><tbody>{grows}</tbody></table>
</div>
<div>{fig(fig_placebo(D['sims'], plac['ganho_anual_bps']), 'S1', 'Nenhuma rotação sorteada chegou ao resultado da regra', f'{num(plac["simulacoes"], 0)} carteiras com o mesmo número de ciclos e as mesmas durações, em datas sorteadas. Percentil 95 dos sorteios: {num(plac["placebo_p95_bps"], 0)} bps por ano.')}
<p class="small" style="margin-top:10px">Tabela: atraso em pregões entre o sinal e a execução; metades antes e depois de 01/10/2023; IC por bootstrap circular em blocos de 6 meses (5.000 repetições). Sempre PAXG contra GLDM: {num(rot[(rot.config == 'sempre PAXG') & (rot.cenario_custos == 'intermediario')].ganho_anual_vs_gldm_bps.iloc[0], 1)} bps/ano.</p>
<div class="h" style="margin-top:14px">Leitura</div>
<p>Todas as faixas iguais ou maiores que o custo de um ciclo dão resultado positivo, nos dois cenários de custo e com atraso de 1 ou 2 pregões. A faixa de ±10 bps, menor que o custo do ciclo original, perde dinheiro com custos originais; a variante com nível móvel de 60 pregões também fica fraca nesse cenário. A regra principal não foi a melhor da grade: a faixa de ±30 rendeu mais.</p></div></div>"""
    pages.append(page(3, 'Rotação: grade completa e placebo', body, supp=True, total=total))

    # A4
    cyc = D['cyc']
    half = (len(cyc) + 1) // 2

    def ctab(df):
        return ''.join(f'<tr><td>{pd.Timestamp(r.entrada).date():%d/%m/%Y}</td><td>{pd.Timestamp(r.saida).date():%d/%m/%Y}</td><td class="n">{int(r.dias)}</td><td class="n">{num(r.desvio_entrada, 1)}</td><td class="n">{num(r.desvio_saida, 1, True)}</td><td class="n">{num(r.resultado_bps, 1, True)}</td></tr>' for _, r in df.iterrows())
    head = '<thead><tr><th>Entrada</th><th>Saída</th><th class="n">Dias</th><th class="n">Desvio na entrada</th><th class="n">Na saída</th><th class="n">Resultado</th></tr></thead>'
    t14 = D['t14']
    brows = ''.join(f'<tr><td>{r.horizonte}</td><td class="n">{int(r.n)}</td><td class="n">{num(r.desvio_padrao_bps, 1)}</td><td class="n">{num(r.p05_bps, 0)}</td><td class="n">{num(r.p95_bps, 0, True)}</td><td class="n">{num(r.taxa_gldm_no_horizonte_bps, 1)}</td></tr>' for _, r in t14.iterrows())
    t15, t16 = D['t15'], D['t16']
    body = f"""<div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:26px">
<div><div class="h">Ciclos da regra principal (1 de 2)</div><table style="font-size:11.5px">{head}<tbody>{ctab(cyc.iloc[:half])}</tbody></table></div>
<div><div class="h">Ciclos da regra principal (2 de 2)</div><table style="font-size:11.5px">{head}<tbody>{ctab(cyc.iloc[half:])}</tbody></table>
<p class="small" style="margin-top:6px">Resultado de cada ciclo contra o GLDM, em bps, já com o custo das duas trocas e a taxa do GLDM economizada.</p></div>
<div><div class="h">Risco de base por horizonte</div>
<table style="font-size:12px"><thead><tr><th>Horizonte</th><th class="n">n</th><th class="n">DP</th><th class="n">p5</th><th class="n">p95</th><th class="n">Taxa GLDM</th></tr></thead><tbody>{brows}</tbody></table>
<div class="h" style="margin-top:14px">Modelos do desvio</div>
<p class="small"><b>Componentes não observados</b> (n = {t15['n']}): φ = {num(t15['phi_ar1'], 3)}; meia-vida de {num(t15['meia_vida_transitorio_pregoes'])} pregões; choque do nível de {num(t15['dp_choque_nivel_bps_dia'], 2)} bps/dia; choque AR de {num(t15['dp_choque_ar_bps'], 1)} bps; ruído de {num(t15['dp_ruido_bps'], 1)} bps.</p>
<p class="small" style="margin-top:6px"><b>Correção de erro</b> (n = {t16['n']}, HAC): retorno do ouro {num(t16['coef']['ret_ouro'], 3)} ({num(t16['ep_hac']['ret_ouro'], 3)}); retorno da véspera {num(t16['coef']['ret_ouro_vespera'], 3)} ({num(t16['ep_hac']['ret_ouro_vespera'], 3)}); desvio da véspera {num(t16['coef']['desvio_vespera'], 3)} ({num(t16['ep_hac']['desvio_vespera'], 3)}); R² {num(t16['r2'], 3)}. Semanal: variação do desvio contra retorno do ouro, β {num(t16['semanal_var_desvio_em_ret_ouro']['beta'], 3)}, R² {num(t16['semanal_var_desvio_em_ret_ouro']['r2'], 3)}.</p></div></div>"""
    pages.append(page(4, 'Rotação ciclo a ciclo e modelos do desvio', body, supp=True, total=total))

    # A5
    body = """<div class="grid" style="grid-template-columns:1fr 1fr;gap:34px">
<div><div class="h">Fontes de dados</div><table><tbody>
<tr><td>Binance Public Data</td><td><a href="https://github.com/binance/binance-public-data">github.com/binance/binance-public-data</a> · PAXG/USDT, hora e minuto</td></tr>
<tr><td>Bitfinex</td><td><a href="https://docs.bitfinex.com/reference/rest-public-candles">docs.bitfinex.com</a> · USDT/USD</td></tr>
<tr><td>Coinbase</td><td><a href="https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles">docs.cdp.coinbase.com</a> · USDT/USD (checagem)</td></tr>
<tr><td>Dukascopy</td><td><a href="https://www.dukascopy.com/swiss/english/marketwatch/historical/">dukascopy.com</a> · XAUUSD compra e venda</td></tr>
<tr><td>Kraken</td><td><a href="https://docs.kraken.com/api/">docs.kraken.com</a> · PAXG/USD (checagem)</td></tr>
<tr><td>SPDR GLD e GLDM</td><td><a href="https://www.spdrgoldshares.com/usa/">spdrgoldshares.com</a> · taxas, spread, onças por cota</td></tr>
<tr><td>Paxos</td><td><a href="https://www.paxos.com/terms-and-conditions/pax-gold-terms-conditions">paxos.com</a> · termos, criação e resgate do PAXG</td></tr>
<tr><td>CME e Binance</td><td>avisos de ouro no fim de semana (jul/2026) e perpétuo XAUUSDT (jan/2026)</td></tr></tbody></table>
<div class="h" style="margin-top:14px">Como reproduzir</div>
<p>Python 3.11, Node ≥ 20 e Chrome. <b>python run_all.py --all</b> baixa os dados, monta os painéis, roda as análises e os testes. <b>python -m src.regime --kraken</b> e <b>python -m src.rotation</b> rodam a extensão v5; <b>python -m src.report_v5_build</b> gera este relatório. Parâmetros originais congelados por hash em config_frozen.json; os scripts também estão em TXT no pacote, como pede o regulamento.</p></div>
<div><div class="h">Referências</div>
<p class="small">Bailey, D., Borwein, J., López de Prado, M. e Zhu, Q. (2014). Pseudo-mathematics and financial charlatanism: the effects of backtest overfitting on out-of-sample performance. <i>Notices of the AMS</i> 61(5).</p>
<p class="small">Cong, L. W., Mayer, S. e Rabetti, D. (2026). Tokenizing Real-World Assets. Wharton WIFPR.</p>
<p class="small">Harvey, A. C. (1989). <i>Forecasting, Structural Time Series Models and the Kalman Filter</i>. Cambridge University Press.</p>
<p class="small">Hyndman, R. J. e Athanasopoulos, G. <i>Forecasting: Principles and Practice</i>, 3ª ed., validação em série temporal.</p>
<p class="small">Lo, A. e MacKinlay, A. C. (1990). An econometric analysis of nonsynchronous trading. <i>Journal of Econometrics</i> 45.</p>
<p class="small">Lyons, R. K. e Viswanath-Natraj, G. (2023). What keeps stablecoins stable? <i>Journal of International Money and Finance</i> 131.</p>
<p class="small">Makarov, I. e Schoar, A. (2020). Trading and arbitrage in cryptocurrency markets. <i>Journal of Financial Economics</i> 135(2).</p>
<p class="small">Petajisto, A. (2017). Inefficiencies in the pricing of exchange-traded funds. <i>Financial Analysts Journal</i> 73(1).</p>
<p class="small">Politis, D. N. e Romano, J. P. (1992). A circular block-resampling procedure for stationary data. Em <i>Exploring the Limits of Bootstrap</i>, Wiley.</p>
<p class="small">Shleifer, A. e Vishny, R. W. (1997). The limits of arbitrage. <i>Journal of Finance</i> 52(1).</p>
<div class="box" style="margin-top:14px"><p><b>Ordem das análises.</b> O núcleo (fidelidade, convergência, custos contra ETFs) foi feito com parâmetros congelados antes dos resultados. A previsão, a janela de câmbio, a decomposição do desvio, o fim de semana, o risco de base e a rotação vieram depois e estão marcados assim no texto.</p></div></div></div>"""
    pages.append(page(5, 'Fontes, reprodução e referências', body, supp=True, total=total))
    has_t18 = (ROOT / 'results' / 'v2' / 'T18_onchain_resumo.json').exists()
    v2_title = 'Entrega v2: XAUT, emissão on-chain e regimes' if has_t18 else 'Entrega v2: XAUT e regimes; on-chain reservado'
    v2_source = ('results/v2: T17 (XAUT), T18 (emissão on-chain), T19 (regimes). Regras pré-registradas em PLANO_ENTREGA_V2.md antes do download.'
                 if has_t18 else
                 'results/v2: T17 (XAUT) e T19 (regimes). A coleta T18 ficou reservada para a final por instabilidade do endpoint histórico; v1 preservada.')
    pages.append(page(6, v2_title, supp_v2_body(D), supp=True, total=total, source=v2_source))
    return pages


def supp_v2_body(D):
    import json as _json
    from .common import ROOT as _R
    v2 = _R / 'results' / 'v2'
    parts = []
    if (v2 / 'T17_xaut_resumo.csv').exists():
        t = pd.read_csv(v2 / 'T17_xaut_resumo.csv')
        t = t[t.ciclos > 0]
        lab = {'intermediario': 'intermediário', 'original': 'original', 'bitfinex_atual': 'Bitfinex hoje'}
        rows = ''.join(f'<tr class="{"hl" if r.papel == "principal" else ""}"><td>{r.par}</td><td class="n">≥{int(r.min_barras)}</td><td>{lab[r.cenario_custos]}</td><td class="n">±{int(r.k_bps)}</td><td class="n">{int(r.lag_pregoes)}</td>'
                       f'<td class="n">{int(r.ciclos)}</td><td class="n">{pct(r.ciclos_positivos)}</td><td class="n">{num(r.ganho_anual_vs_gldm_bps, 0, True)}</td><td class="n">[{num(r.ic90_lo, 0)}; {num(r.ic90_hi, 0)}]</td></tr>' for _, r in t.iterrows())
        j = _json.loads((v2 / 'T17_xaut_resumo.json').read_text(encoding='utf-8'))
        parts.append(f"""<div><div class="h">XAUT: a mesma regra, sem reestimar</div>
<table class="tight tighter"><thead><tr><th>Par</th><th class="n">Barras</th><th>Custos</th><th class="n">Faixa</th><th class="n">Atraso</th><th class="n">Ciclos</th><th class="n">Pos.</th><th class="n">bps/ano</th><th class="n">IC 90%</th></tr></thead><tbody>{rows}</tbody></table>
<p class="small" style="margin-top:6px">Bitfinex, candles de 1 h; {num(j['dias_validos'], 0)} pregões válidos ({pct(j['cobertura_dias'])} dos possíveis). Desvio mediano absoluto de {num(j['desvio_mediano_abs_bps'], 1)} bps; correlação diária com o desvio do PAXG de {num(j['correlacao_diaria_com_paxg'], 2)}. Placebo da regra principal: {num(j['fracao_placebos_acima'] * 1000, 0)} de 1.000 acima. "Bitfinex hoje": taxa zero e spread de 2,2 bps vistos em 08/11/2026, condição atual e não histórica. Teste fora da amostra entre ativos, no mesmo período.</p></div>""")
    right = []
    if (v2 / 'T19_regimes_resumo.csv').exists():
        r19 = pd.read_csv(v2 / 'T19_regimes_resumo.csv')
        j19 = _json.loads((v2 / 'T19_regimes_resumo.json').read_text(encoding='utf-8'))
        rows = ''.join(f'<tr><td>{r.config}</td><td>{"intermediário" if r.cenario_custos == "intermediario" else "original"}</td><td class="n">{int(r.lag_pregoes)}</td><td class="n">{int(r.ciclos)}</td><td class="n">{num(r.ganho_anual_vs_gldm_bps, 0, True)}</td><td class="n">[{num(r.ic90_lo, 0)}; {num(r.ic90_hi, 0)}]</td></tr>' for _, r in r19.iterrows())
        right.append(f"""<div class="h">Regimes (Markov, 3 estados, probabilidades filtradas)</div>
<table class="tight tighter"><thead><tr><th>Regra</th><th>Custos</th><th class="n">Atraso</th><th class="n">Ciclos</th><th class="n">bps/ano</th><th class="n">IC 90%</th></tr></thead><tbody>{rows}</tbody></table>
<p class="small" style="margin-top:6px">Reestimado no primeiro pregão de cada mês só com dados anteriores (mínimo de 500 pregões); regra a partir de {j19['inicio_regra']}, {j19['pregoes']} pregões. A faixa fixa é recalculada no mesmo período para comparação.</p>""")
    if (v2 / 'T18_onchain_resumo.json').exists():
        j18 = _json.loads((v2 / 'T18_onchain_resumo.json').read_text(encoding='utf-8'))
        lines = ''.join(f"<tr><td>{t['amostra']}</td><td class='n'>{t['semanas']}</td><td class='n'>{num(t['corr_desvio_t_emissao_t1_t4'], 2)}</td><td class='n'>{num(t['emissao_prox_4s_media_pct_quando_premio_25'], 2, True)}</td><td class='n'>{num(t['emissao_prox_4s_media_pct_quando_desconto_25'], 2, True)}</td><td class='n'>{num(t['variacao_desvio_em_emissao_defasada']['p_conjunto_emissao'], 2)}</td></tr>" for t in j18['testes'])
        right.append(f"""<div class="h" style="margin-top:14px">Emissão e resgate do PAXG no Ethereum</div>
<table class="tight tighter"><thead><tr><th>Amostra</th><th class="n">Semanas</th><th class="n">Corr. desvio × emissão +1 a +4</th><th class="n">Emissão 4 s após prêmio</th><th class="n">Após desconto</th><th class="n">p (emissão → desvio)</th></tr></thead><tbody>{lines}</tbody></table>
<p class="small" style="margin-top:6px">{j18['emissoes']} emissões e {j18['resgates']} resgates (eventos Transfer de/para o endereço zero, via Blockscout). Emissão em % da oferta no Ethereum; prêmio e desconto: desvio semanal acima de +25 ou abaixo de −25 bps. Ressalvas: a Paxos emite em lotes para a tesouraria; desde jun/2025 há emissão em Solana; associação, não causa.</p>""")
    else:
        right.append('<div class="box" style="margin-top:14px"><p><b>On-chain reservado para a final.</b> A consulta histórica de resgates no Blockscout ficou instável no prazo desta entrega; nenhum número incompleto entra no deck. A v1 permanece congelada.</p></div>')
    return f'<div class="grid" style="grid-template-columns:1.05fr 1fr;gap:30px">{"".join(parts)}<div>{"".join(right)}</div></div>'



def export(html_path: Path, pdf_path: Path, pages: int):
    from playwright.sync_api import sync_playwright
    cands = [os.getenv('CHROME_PATH', ''), r'C:\Program Files\Google\Chrome\Application\chrome.exe',
             r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', shutil.which('google-chrome') or '', shutil.which('chromium') or '']
    exe = next((p for p in cands if p and Path(p).is_file()), None)
    JS = '''()=>[...document.querySelectorAll('.page,.cover')].map((s,i)=>{const sb=s.getBoundingClientRect();const bad=[];
      s.querySelectorAll('p,td,th,h1,h3,.card,.st,.fig,.risk,.call,.box,.sheet,.roadrow,svg,table').forEach(e=>{if(e.closest('.ft'))return;const r=e.getBoundingClientRect();
      if(r.bottom-sb.top>850||r.right-sb.left>1600-30)bad.push([e.tagName,(e.className||'').toString().slice(0,20),Math.round(r.bottom-sb.top),Math.round(r.right-sb.left)])});return {page:i+1,overflow:bad}})'''
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=exe, headless=True)
        page_ = browser.new_page(viewport={'width': 1600, 'height': 900})
        page_.goto(html_path.as_uri())
        page_.evaluate('document.fonts.ready')
        page_.wait_for_timeout(300)
        qa = page_.evaluate(JS)
        page_.pdf(path=str(pdf_path), width='1600px', height='900px', print_background=True, prefer_css_page_size=True)
        browser.close()
    import pymupdf
    with pymupdf.open(pdf_path) as doc:
        assert len(doc) == pages, (pdf_path, len(doc))
        doc.set_metadata({'title': 'PAXG × Ouro: desvio, custos e rotação, 2020–2026', 'author': 'BitFlow: Gabriel Navarro, Lorenzo Cavalcante e Rodrigo Menin',
                          'subject': '7º Datathon de Moedas Digitais FGV EESP'})
        doc.saveIncr()
    return qa


def main():
    """Gera a entrega v2 em caminhos próprios. Nunca escreve em slides/entrega.*, relatorio_final.* ou results/*.json da v1."""
    D = load()
    main_pages = build_main(D)
    supp_pages = build_supp(D)
    out = ROOT / 'slides'
    v2 = ROOT / 'results' / 'v2'
    v2.mkdir(parents=True, exist_ok=True)
    head = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=1600"><title>{t}</title><style>' + CSS + '</style></head><body>'
    files = {'main_html': out / 'entrega_v2.html', 'main_pdf': out / 'entrega_v2.pdf',
             'supp_html': out / 'entrega_v2_suplementar.html', 'supp_pdf': out / 'entrega_v2_suplementar.pdf'}
    protected = {out / 'entrega.pdf', out / 'entrega.html', out / 'entrega_suplementar.pdf', out / 'relatorio_final.pdf', out / 'relatorio_final.html',
                 out / 'material_suplementar.pdf', out / 'material_suplementar.html'}
    assert not protected & set(files.values())
    files['main_html'].write_text(head.replace('{t}', 'PAXG × Ouro · entrega v2 · BitFlow') + ''.join(main_pages) + '</body></html>', encoding='utf-8')
    files['supp_html'].write_text(head.replace('{t}', 'PAXG × Ouro · material suplementar v2 · BitFlow') + ''.join(supp_pages) + '</body></html>', encoding='utf-8')
    qa1 = export(files['main_html'], files['main_pdf'], len(main_pages))
    qa2 = export(files['supp_html'], files['supp_pdf'], len(supp_pages))
    bad = [p for p in qa1 + qa2 if p['overflow']]
    dump_json(v2 / 'QA_presentation_v2.json', {'at_utc': utc_now(), 'design': 'entrega-v2', 'main_pages': len(main_pages),
                                               'supplementary_pages': len(supp_pages), 'max_main_pages_allowed': 10,
                                               'main': qa1, 'supplementary': qa2, 'status': 'passed' if not bad else 'needs_review'})
    dump_json(v2 / 'presentation_status_v2.json', {'pages': len(main_pages) + len(supp_pages), 'main_pages': len(main_pages),
              'appendix_pages': len(supp_pages), 'design': 'entrega-v2', 'pdf': 'slides/entrega_v2.pdf',
              'supplementary_pdf': 'slides/entrega_v2_suplementar.pdf', 'generated_at_utc': utc_now()})
    if bad:
        raise ValueError('Entrega v2 com conteúdo fora da página: results/v2/QA_presentation_v2.json')
    print('páginas', len(main_pages), len(supp_pages), 'estouros', bad)


if __name__ == '__main__':
    main()
