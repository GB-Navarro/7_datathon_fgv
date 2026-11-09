"""Caderno de números, gráficos e tabelas da entrega v3, para conferir e ajustar.

Uso: python -m src.v3_numeros
Saídas: entrega/v3/numeros_graficos_tabelas_v3.pdf (e .html), results/v3/numeros_v3.csv

Cada número do deck aparece com: valor no slide, valor exato, arquivo e campo de origem, tipo
(lido de arquivo, calculado no deck ou escrito à mão no texto), linha de src/v3_deck.py onde ele entra
e o script que gera o arquivo de origem. A coluna "no PDF" confere se o valor aparece no texto da página.
Não escreve em nenhum arquivo da v1 ou da v2.
"""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import pandas as pd

from . import v3_deck as V  # importa a paleta da v3 antes dos gráficos
from .common import ROOT
from .report_v5 import fig_level, fig_placebo, fig_rotation, fig_waterfall, fig_weekend, num, pct
from .v2_figs import fig_xaut_vs_paxg
from .v2_report_pages import facts, load, rot_row

DECK_SRC = (ROOT / 'src' / 'v3_deck.py').read_text(encoding='utf-8').splitlines()
GEN = {
    'summary.json': 'src/analysis.py',
    'T11_regime_resumo.json': 'src/regime.py', 'T11_regime_anual.csv': 'src/regime.py', 'T11_regime_mensal.csv': 'src/regime.py',
    'T11_kraken_extremos.csv': 'src/regime.py (--kraken)',
    'T12_rotacao_resumo.csv': 'src/rotation.py', 'T12_rotacao_placebo.json': 'src/rotation.py', 'T12_rotacao_ciclos.csv': 'src/rotation.py',
    'T12_rotacao_curva.csv': 'src/rotation.py', 'T12_rotacao_placebo_dist.csv': 'src/rotation.py',
    'T13_fim_de_semana_resumo.json': 'src/rotation.py', 'T14_risco_de_base.csv': 'src/rotation.py',
    'T15_componentes.json': 'src/rotation.py', 'T15_componentes_serie.csv': 'src/rotation.py', 'T16_correcao_de_erro.json': 'src/rotation.py',
    'T10_cost_budget.csv': 'src/refinement.py', 'T10_grid_summary.csv': 'src/refinement.py', 'T7_paired_changes.csv': 'src/refinement.py',
    'T2_convergencia.csv': 'src/analysis.py', 'T2_trade_ledger.csv': 'src/analysis.py', 'T13_fim_de_semana.csv': 'src/rotation.py', 'T4_trend.csv': 'src/analysis.py', 'T3_custos_etfs.csv': 'src/analysis.py', 'QA_gold_reference_summary.json': 'src/quality.py',
    'v2/T17_xaut_resumo.json': 'src/v2_xaut.py', 'v2/T17_xaut_resumo.csv': 'src/v2_xaut.py', 'v2/T17_xaut_curva.csv': 'src/v2_xaut.py',
    'v2/T19_regimes_resumo.json': 'src/v2_regimes.py', 'v2/T19_regimes_resumo.csv': 'src/v2_regimes.py', 'v2/T19_regimes_probabilidades.csv': 'src/v2_regimes.py',
}
KIND = {'L': 'lido de arquivo', 'C': 'calculado no deck', 'M': 'escrito à mão', 'E': 'fato externo'}


def line_of(snippet):
    hits = [i + 1 for i, s in enumerate(DECK_SRC) if snippet in s]
    return f'v3_deck.py:{hits[0]}' if hits else '?'


def collect(D):
    """Lista de números do deck: (slide, item, mostrado, exato, origem, tipo, trecho do código)."""
    S, Rg = D['S'], D['R']
    t15, t16, t13r = D['t15'], D['t16'], D['t13r']
    F = facts(D)
    prim, prim_o, k = F['prim'], F['prim_o'], F['k']
    gross, mid_net, mid_cost = F['gross'], F['mid_net'], F['mid_cost']
    orig, low = D['conv']['orig'], D['conv']['low']
    rot, jx, r19, j19 = D['rot'], D['x17j'], D['r19'], D['r19j']
    hm = r19[(r19.regra == 'hmm_filtrado') & (r19.cenario_custos == 'intermediario') & (r19.lag_pregoes == 1)].iloc[0]
    hb = r19[(r19.regra == 'faixa_fixa') & (r19.cenario_custos == 'intermediario') & (r19.lag_pregoes == 1)].iloc[0]
    x17 = D['x17']
    xa = x17[(x17.par == 'XAUT/USD') & (x17.min_barras == 4) & (x17.cenario_custos == 'intermediario') & (x17.lag_pregoes == 1)].iloc[0]
    alw = rot[(rot.config == 'sempre PAXG') & (rot.cenario_custos == 'intermediario')].iloc[0]
    t14b = D['t14'].set_index('horizonte')
    budget = D['budget'].set_index('horizon_hours')
    p1 = D['pair'].loc['b_0_to_b_1h']
    ex = F['ex']
    yr = D['plac']['ganho_por_ano_calendario_bps']
    cap = F['cap']
    rotf = 'T12_rotacao_resumo.csv'
    P = "papel=principal, cenário intermediário"
    R = []

    def add(sl, item, shown, exact, src, kind, snip):
        R.append(dict(slide=sl, item=item, mostrado=shown, exato=exact, origem=src, tipo=KIND[kind], linha=line_of(snip),
                      gera=GEN.get(src.split(' → ')[0], '—') if kind in 'LC' else '—'))

    # 01 capa
    add(1, 'Horas medidas', num(S['valid_hours'], 0), S['valid_hours'], 'summary.json → valid_hours', 'L', "Medimos o desvio entre o PAXG e o ouro em")
    add(1, 'Meia-vida do ruído (arredondada)', num(t15['meia_vida_transitorio_pregoes'], 0), t15['meia_vida_transitorio_pregoes'], 'T15_componentes.json → meia_vida_transitorio_pregoes', 'L', "um ruído que some em cerca de")
    add(1, 'Saldo por operação na reabertura (intermediário)', num(mid_net, 0), mid_net, 'T2_convergencia.csv → mean_model_bps (taxa 5, spread 2, ouro 1, câmbio 2, desliz. 2)', 'C', "A arbitragem na reabertura do fim de semana não cobre os custos")
    add(1, 'Ganho da rotação, bps/ano', num(prim.ganho_anual_vs_gldm_bps, 0, True), prim.ganho_anual_vs_gldm_bps, f'{rotf} → ganho_anual_vs_gldm_bps ({P})', 'L', "Quem já quer ouro captura o nível trocando")
    add(1, 'IC 90% da rotação', f'{num(prim.ic90_lo, 0)} a {num(prim.ic90_hi, 0)}', f'{prim.ic90_lo:.2f} a {prim.ic90_hi:.2f}', f'{rotf} → ic90_lo, ic90_hi', 'L', "Quem já quer ouro captura o nível trocando")
    add(1, 'XAUT, bps/ano', num(jx['ganho_anual_bps'], 0, True), jx['ganho_anual_bps'], 'v2/T17_xaut_resumo.json → ganho_anual_bps', 'L', "e a mesma regra rende")
    # 02 motivação
    add(2, 'Jan/2021: 90% das horas acima de', num(F['j21_p10'], 0) + ' bps', F['j21_p10'], 'T11_regime_mensal.csv → p10_bps (2021-01)', 'L', "em janeiro de 2021, 90% das horas")
    add(2, 'Mar/2024: desconto mínimo e máximo', f"{num(F['m24_lo'], 1)}% a {num(F['m24_hi'], 1)}%", f"{F['m24_lo']:.4f}% a {F['m24_hi']:.4f}% ({F['m24_n']} pregões)", 'T15_componentes_serie.csv → desvio_bps (mar/2024, ≤ −200)', 'C', "em março de 2024, ficou de")
    add(2, 'Volume Binance 2026', f"US$ {num(F['y26'].usd_volume_millions / 1000, 0)} bi", F['y26'].usd_volume_millions, 'T11_regime_anual.csv → usd_volume_millions (2026), em milhões', 'C', "negociados na Binance em 2026")
    add(2, 'Desvio mediano em hora comum', '36 bps', S['common_hours_median_abs_bps'], 'summary.json → common_hours_median_abs_bps', 'M', '36 bps</div>')
    add(2, 'Operações avaliadas (H2)', '44 operações', S['evaluated_trades'], 'summary.json → evaluated_trades', 'M', "Teste: 44 operações")
    add(2, 'Combinações de custo e prazo', '1.458', F['n_grid'], 'T10_grid_summary.csv → soma de configurations', 'M', "Teste: 44 operações")
    add(2, 'Correlação diária PAXG × ouro', '0,99', 0.99, 'Cong, Mayer e Rabetti (2026), apêndice A.2, citando Harvey et al. (2025)', 'E', "correlação diária de 0,99")
    # 03 dados
    add(3, 'Horas com ouro e token ativos', num(S['valid_hours'], 0), S['valid_hours'], 'summary.json → valid_hours', 'L', "horas com ouro e token ativos")
    add(3, 'Fins de semana válidos', f"{int(S['valid_weekends'])}", S['valid_weekends'], 'summary.json → valid_weekends', 'L', "fins de semana válidos de")
    add(3, 'Fins de semana candidatos', f"{int(S['candidate_weekends'])}", S['candidate_weekends'], 'summary.json → candidate_weekends', 'L', "fins de semana válidos de")
    add(3, 'Pregões da NYSE (base diária)', num(D['plac']['dias_uteis'], 0), D['plac']['dias_uteis'], 'T12_rotacao_placebo.json → dias_uteis', 'L', "pregões da NYSE (base diária)")
    add(3, 'Pregões de XAUT', num(jx['dias_validos'], 0), jx['dias_validos'], 'v2/T17_xaut_resumo.json → dias_validos', 'L', "pregões de XAUT")
    add(3, 'Exemplo: PAXG em USDT', num(ex.p_usdt, 2), ex.p_usdt, 'T11_kraken_extremos.csv → p_usdt (04/03/2024 16h)', 'L', "PAXG {num(ex.p_usdt, 2)}")
    add(3, 'Exemplo: USDT/USD', num(ex.q, 4), ex.q, 'T11_kraken_extremos.csv → q', 'L', "PAXG {num(ex.p_usdt, 2)}")
    add(3, 'Exemplo: PAXG em US$', num(ex.p_usdt * ex.q, 2), ex.p_usdt * ex.q, 'p_usdt × q', 'C', "PAXG {num(ex.p_usdt, 2)}")
    add(3, 'Exemplo: ouro Dukascopy', num(ex.S, 2), ex.S, 'T11_kraken_extremos.csv → S', 'L', "ouro (Dukascopy) = US$")
    add(3, 'Exemplo: desvio', num(ex.basis_log_bps, 1), ex.basis_log_bps, 'T11_kraken_extremos.csv → basis_log_bps', 'L', "desvio = 10.000 × ln(PAXG em US$ ÷ ouro) =")
    add(3, 'Exemplo: Kraken na mesma hora', num(ex.kraken_bps, 1), ex.kraken_bps, 'T11_kraken_extremos.csv → kraken_bps', 'L', "Na mesma hora, a Kraken dá")
    add(3, 'Nosso ouro × GLD por onça', num(D['gld']['median_abs_level_difference_bps']) + ' bps', D['gld']['median_abs_level_difference_bps'], 'QA_gold_reference_summary.json → median_abs_level_difference_bps', 'L', "Nosso ouro × GLD por onça")
    add(3, 'USDT/USD Bitfinex × Coinbase', num(S['fx_source_median_abs_difference_bps']) + ' bps', S['fx_source_median_abs_difference_bps'], 'summary.json → fx_source_median_abs_difference_bps', 'L', "USDT/USD: Bitfinex × Coinbase")
    add(3, 'PAXG Binance × Kraken nos extremos', num(F['kx_diff'], 0) + ' bps', F['kx_diff'], 'T11_kraken_extremos.csv → mediana |kraken_bps − basis_log_bps|', 'C', "PAXG: Binance × Kraken nos extremos")
    # 04 metodologia I
    add(4, 'Dias da série diária', '1.552', D['plac']['dias_uteis'], 'T12_rotacao_placebo.json → dias_uteis', 'M', "Média das 15h às 20h UTC de cada pregão da NYSE: 1.552 dias")
    add(4, 'Faixa da rotação (texto)', '−19 / +19', k, f'{rotf} → k_bps ({P})', 'M', "vai ao PAXG se o desvio ≤ −19 bps")
    add(4, 'Limiar da arbitragem', '10 bps', 10, 'config/params.json (convergence)', 'M', "se o desvio absoluto passa de 10 bps")
    add(4, 'Placebo: carteiras sorteadas', '1.000', D['plac']['simulacoes'], 'T12_rotacao_placebo.json → simulacoes', 'M', "placebo com 1.000 carteiras")
    # 05 metodologia II
    add(5, 'Custo da arbitragem (4 execuções)', num(mid_cost, 1), mid_cost, 'summary.json mean_gross_mid_bps − saldo intermediário', 'C', "Quatro execuções: {num(mid_cost, 1)}")
    add(5, 'Custo de um ciclo da rotação', num(float(prim.custo_ciclo_bps), 0), prim.custo_ciclo_bps, f'{rotf} → custo_ciclo_bps ({P})', 'L', "Duas trocas por ciclo")
    add(5, 'Custos intermediários (5, 2, 1, 2, 2)', '5 / 2 / 1 / 2 / 2', '5, 2, 1, 2, 2', 'src/v2_report_pages.py load(): conv mid = (5, 2, 1, 2, 2)', 'M', "<b>Intermediário:</b> taxa do token 5 bps")
    add(5, 'Custos originais (taxa, spread)', '10 / 10', f"{S['assumption_token_fee_bps_per_fill']}, {S['assumption_token_full_spread_bps']}", 'summary.json → assumption_token_fee_bps_per_fill, assumption_token_full_spread_bps', 'M', "<b>Original</b> (fixado antes dos resultados)")
    add(5, 'HMM: mínimo de pregões', '500', 500, 'src/v2_regimes.py → MIN_OBS', 'M', "estima o modelo (mín. 500 pregões)")
    # 06 resultado 1
    add(6, 'Meia-vida do ruído', num(t15['meia_vida_transitorio_pregoes']), t15['meia_vida_transitorio_pregoes'], 'T15_componentes.json → meia_vida_transitorio_pregoes', 'L', "<div class=\"lab\">Ruído</div>")
    add(6, 'Parte da variação vinda do nível do mês', pct(Rg['variance_share_monthly_level']), Rg['variance_share_monthly_level'], 'T11_regime_resumo.json → variance_share_monthly_level', 'L', "<div class=\"lab\">Nível</div>")
    add(6, 'Segue o ouro no dia (b0)', pct(t16['coef']['ret_ouro']), t16['coef']['ret_ouro'], 'T16_correcao_de_erro.json → coef.ret_ouro', 'L', "<div class=\"lab\">Segue o ouro</div>")
    add(6, 'Correção diária (γ)', pct(t16['correcao_diaria']), t16['correcao_diaria'], 'T16_correcao_de_erro.json → correcao_diaria', 'L', "<div class=\"lab\">Corrige</div>")
    add(6, 'Meia-vida na correção de erro', num(t16['meia_vida_pregoes']), t16['meia_vida_pregoes'], 'T16_correcao_de_erro.json → meia_vida_pregoes', 'L', "<div class=\"lab\">Corrige</div>")
    add(6, 'Nível mínimo', num(F['lvl_min'], 0), F['lvl_min'], 'T15_componentes_serie.csv → mín. nivel_suavizado_bps', 'C', "carrega um nível próprio, de")
    add(6, 'Nível máximo', num(F['lvl_max'], 0, True), F['lvl_max'], 'T15_componentes_serie.csv → máx. nivel_suavizado_bps', 'C', "carrega um nível próprio, de")
    add(6, 'Taxa de resgate Paxos', '0,125% a 0,5%', '0,125%; 0,25%; 0,35%; 0,5%', 'support.paxos.com, PAX Gold (PAXG) Overview (faixas vigentes desde 01/09/2026)', 'E', "resgatar PAXG na Paxos custa")
    add(6, 'R² semanal do ouro sobre o desvio', pct(t16['semanal_var_desvio_em_ret_ouro']['r2']), t16['semanal_var_desvio_em_ret_ouro']['r2'], 'T16_correcao_de_erro.json → semanal_var_desvio_em_ret_ouro.r2', 'L', "o retorno do ouro explica só")
    add(6, 'Dias com regime de desconto (HMM)', pct(j19['fracao_dias_desconto_dominante']), j19['fracao_dias_desconto_dominante'], 'v2/T19_regimes_resumo.json → fracao_dias_desconto_dominante', 'L', "o regime de desconto domina")
    add(6, 'Dias com regime de prêmio (HMM)', pct(j19['fracao_dias_premio_dominante']), j19['fracao_dias_premio_dominante'], 'v2/T19_regimes_resumo.json → fracao_dias_premio_dominante', 'L', "o regime de desconto domina")
    add(6, 'Início do HMM filtrado', 'set/2022', j19['inicio_regra'], 'v2/T19_regimes_resumo.json → inicio_regra', 'L', "ini_txt = ")
    add(6, 'Horas a até 25 bps em 2026', pct(F['y26'].within_25_bps), F['y26'].within_25_bps, 'T11_regime_anual.csv → within_25_bps (2026)', 'L', "Em 2026, {pct(F['y26'].within_25_bps)}")
    add(6, 'Horas a até 25 bps em 2020', pct(F['y20'].within_25_bps), F['y20'].within_25_bps, 'T11_regime_anual.csv → within_25_bps (2020)', 'L', "Em 2026, {pct(F['y26'].within_25_bps)}")
    add(6, 'Kraken no dia mínimo (rodapé)', F['kx_ext'], F['kx_ext'], 'T11_kraken_extremos.csv → kraken_bps em 01/03/2024 (máx. e mín.)', 'C', "Mínimo do dia: mar/2024 (Kraken:")
    # 07 resultado 2
    add(7, 'R² sexta → reabertura', num(t13r['r2_reabertura_em_sexta'], 2), t13r['r2_reabertura_em_sexta'], 'T13_fim_de_semana_resumo.json → r2_reabertura_em_sexta', 'L', "O desvio de sexta explica o desvio da reabertura")
    add(7, 'R² sexta → 7 h depois', num(t13r['r2_7h_em_sexta'], 2), t13r['r2_7h_em_sexta'], 'T13_fim_de_semana_resumo.json → r2_7h_em_sexta', 'L', "O desvio de sexta explica o desvio da reabertura")
    add(7, 'Mesmo sinal sexta e reabertura', pct(t13r['mesmo_sinal_sexta_reabertura']), t13r['mesmo_sinal_sexta_reabertura'], 'T13_fim_de_semana_resumo.json → mesmo_sinal_sexta_reabertura', 'L', "o sinal se mantém em")
    add(7, 'Queda do desvio absoluto em 1 h', num(-p1.mean_abs_change_bps, 1), -p1.mean_abs_change_bps, 'T7_paired_changes.csv → mean_abs_change_bps (b_0_to_b_1h)', 'L', "O desvio absoluto cai em média")
    add(7, 'Ganho bruto médio (6 h)', num(gross), gross, 'summary.json → mean_gross_mid_bps', 'L', "O ganho bruto em 6 h é de")
    add(7, 'IC 95% do ganho bruto', f"{num(budget.loc[6, 'gross_lo'], 1)} a {num(budget.loc[6, 'gross_hi'], 1)}", f"{budget.loc[6, 'gross_lo']:.3f} a {budget.loc[6, 'gross_hi']:.3f}", 'T10_cost_budget.csv → gross_lo, gross_hi (6 h)', 'L', "O ganho bruto em 6 h é de")
    add(7, 'Saldo, cenário original', num(orig.mean_model_bps, 1), orig.mean_model_bps, 'T2_convergencia.csv → mean_model_bps (10, 10, 1, 2, 2)', 'L', "Original (taxa 10, spread 10)")
    add(7, 'Saldo, cenário intermediário', num(mid_net, 1), mid_net, 'T2_convergencia.csv → mean_model_bps (5, 2, 1, 2, 2)', 'L', "Intermediário (taxa 5, spread 2)")
    add(7, 'Saldo, mínimo da grade', num(low.mean_model_bps, 1), low.mean_model_bps, 'T2_convergencia.csv → mean_model_bps (2, 2, 1, 0, 0)', 'L', "Mínimo da grade")
    add(7, 'Positivas (original / intermediário)', f"{F['orig_pos']} de {F['n_eval']} / {F['mid_pos']} de {F['n_eval']}", f"{F['orig_pos']}, {F['mid_pos']} de {F['n_eval']}", 'T2_convergencia.csv → positive_fraction × evaluated_trades', 'C', "Original (taxa 10, spread 10)")
    add(7, 'Sinais sem preço', f"{int(S['signals_unassessed'])}", S['signals_unassessed'], 'summary.json → signals_unassessed', 'L', "Faltaram preços para")
    add(7, 'Ganho necessário dos sinais sem preço', num(F['tip_mid'], 0), F['tip_mid'], '−(avaliadas × saldo) ÷ (sinais − avaliadas), cenário intermediário', 'C', "eles precisariam render")
    add(7, 'Custo usado na cascata', num(mid_cost, 1), mid_cost, 'ganho bruto − saldo intermediário', 'C', "fig_waterfall(gross, mid_cost, mid_net)")
    # 08 resultado 3
    add(8, 'Faixa da rotação', f'±{k}', prim.k_bps, f'{rotf} → k_bps ({P})', 'L', "Desvio ≤ −{k} bps")
    add(8, 'Custo de uma troca', num(float(prim.custo_ciclo_bps) / 2, 1), float(prim.custo_ciclo_bps) / 2, f'{rotf} → custo_ciclo_bps ÷ 2', 'C', "no pregão seguinte · {num(cs, 1)} bps")
    add(8, 'Ganho, bps/ano', num(prim.ganho_anual_vs_gldm_bps, 0, True), prim.ganho_anual_vs_gldm_bps, f'{rotf} → ganho_anual_vs_gldm_bps ({P})', 'L', "<div class=\"lab\">Ganho</div>")
    add(8, 'Ciclos', f'{int(prim.ciclos)}', prim.ciclos, f'{rotf} → ciclos', 'L', "<div class=\"lab\">Ciclos</div>")
    add(8, 'Ciclos positivos', pct(prim.ciclos_positivos), prim.ciclos_positivos, f'{rotf} → ciclos_positivos', 'L', "<div class=\"lab\">Ciclos</div>")
    add(8, 'Parte do ganho em ciclos > 7 dias', pct(F['share_week']), F['share_week'], 'T12_rotacao_ciclos.csv → soma resultado_bps (dias > 7) ÷ soma total', 'C', "<div class=\"lab\">De onde vem</div>")
    add(8, 'Sempre em PAXG, bps/ano', num(alw.ganho_anual_vs_gldm_bps, 0), alw.ganho_anual_vs_gldm_bps, f'{rotf} → config = sempre PAXG, intermediário', 'L', "<div class=\"lab\">Sem a regra</div>")
    add(8, 'Ida e volta no PAXG', num(F['rt_mid'], 0) + ' bps', F['rt_mid'], 'T3_custos_etfs.csv → token_cost_bps (GLD, US$ 10 mil, 12 meses, taxa 5, spread 2)', 'L', "Entrar e sair do PAXG custa")
    add(8, 'Meses até empatar com o GLD', num(F['gld_m']), F['gld_m'], 'T3_custos_etfs.csv → crossing_months (GLD, taxa 5, spread 2)', 'L', "ele fica mais barato depois de")
    add(8, 'Meses até empatar com o GLDM', num(F['gldm_m']), F['gldm_m'], 'T3_custos_etfs.csv → crossing_months (GLDM, taxa 5, spread 2)', 'L', "ele fica mais barato depois de")
    add(8, 'Taxa anual do GLD', '0,40%', '40 bps', 'config/params.json gld_fee_bps_per_year; spdrgoldshares.com/usa/gld', 'E', "contra o GLD (0,40% ao ano)")
    add(8, 'Taxa anual do GLDM', '0,10%', '10 bps', 'config/params.json gldm_fee_bps_per_year; ssga.com (GLDM)', 'E', "contra o GLDM (0,10%)")
    add(8, 'DP da variação do desvio em 12 meses', num(t14b.loc['12 meses', 'desvio_padrao_bps'], 0) + ' bps', t14b.loc['12 meses', 'desvio_padrao_bps'], 'T14_risco_de_base.csv → desvio_padrao_bps (12 meses)', 'L', "a variação do desvio tem desvio-padrão de")
    add(8, 'Taxa do GLDM em 12 meses', num(t14b.loc['12 meses', 'taxa_gldm_no_horizonte_bps'], 0) + ' bps', t14b.loc['12 meses', 'taxa_gldm_no_horizonte_bps'], 'T14_risco_de_base.csv → taxa_gldm_no_horizonte_bps', 'L', "a variação do desvio tem desvio-padrão de")
    add(8, 'Taxa do GLD em 12 meses', num(t14b.loc['12 meses', 'taxa_gld_no_horizonte_bps'], 0), t14b.loc['12 meses', 'taxa_gld_no_horizonte_bps'], 'T14_risco_de_base.csv → taxa_gld_no_horizonte_bps', 'L', "a variação do desvio tem desvio-padrão de")
    for y in ['2022', '2023', '2024', '2025', '2026']:
        add(8, f'Ganho em {y} (rodapé)', num(yr[y], 0, True), yr[y], f'T12_rotacao_placebo.json → ganho_por_ano_calendario_bps.{y}', 'L', "Por ano: 2022")
    add(8, 'Pregões e período (rodapé)', '1.552; 28/08/2020 a 06/11/2026', f"{D['plac']['dias_uteis']}; {D['plac']['inicio']} a {D['plac']['fim']}", 'T12_rotacao_placebo.json → dias_uteis, inicio, fim', 'M', "f'1.552 pregões da NYSE")
    # 09 robustez
    rows = [(f'PAXG, regra principal (±{k})', prim, rotf), ('Execução dois pregões depois', rot_row(rot, f'faixa fixa ±{k}', 'intermediario', 2), rotf),
            (f'Custos originais (±{int(prim_o.k_bps)})', prim_o, rotf), ('Faixa de ±30 bps', rot_row(rot, 'faixa fixa ±30', 'intermediario', 1), rotf),
            ('Faixa em torno do nível móvel de 60 pregões, custos originais', rot_row(rot, 'nível móvel 60d ±30', 'original', 1), rotf),
            ('Regimes de Markov (desde set/2022)', hm, 'v2/T19_regimes_resumo.csv'), (f'Faixa ±{k} no mesmo período do HMM', hb, 'v2/T19_regimes_resumo.csv'),
            ('XAUT, mesma regra, sem ajuste', xa, 'v2/T17_xaut_resumo.csv')]
    for name, r, f in rows:
        add(9, f'Tabela (a): {name}', f"{int(r.ciclos)} · {num(r.ganho_anual_vs_gldm_bps, 0, True)} · [{num(r.ic90_lo, 0)}; {num(r.ic90_hi, 0)}]",
            f"{int(r.ciclos)} · {r.ganho_anual_vs_gldm_bps:.2f} · [{r.ic90_lo:.2f}; {r.ic90_hi:.2f}]", f'{f} → ciclos, ganho_anual_vs_gldm_bps, ic90_lo, ic90_hi', 'L', "table = ''.join([row(")
    add(9, 'Correlação diária XAUT × PAXG', num(jx['correlacao_diaria_com_paxg'], 2), jx['correlacao_diaria_com_paxg'], 'v2/T17_xaut_resumo.json → correlacao_diaria_com_paxg', 'L', "correlação diária com o desvio do PAXG")
    add(9, 'Placebo: média das 1.000 rotações', num(D['plac']['placebo_media_bps'], 0), D['plac']['placebo_media_bps'], 'T12_rotacao_placebo.json → placebo_media_bps', 'L', "fig_placebo(D['sims']")
    add(9, 'Placebo: acima da regra (PAXG)', 'nenhuma chegou ao resultado da regra', D['plac']['fracao_placebos_acima'], 'T12_rotacao_placebo.json → fracao_placebos_acima', 'L', "nenhuma chegou ao resultado da regra")
    add(9, 'Placebo: acima da regra (XAUT)', f"{num(jx['fracao_placebos_acima'] * 1000, 0)} de 1.000", jx['fracao_placebos_acima'], 'v2/T17_xaut_resumo.json → fracao_placebos_acima', 'L', "nenhuma chegou ao resultado da regra")
    add(9, 'Pior queda contra o GLDM', num(prim.pior_queda_bps, 0) + ' bps', prim.pior_queda_bps, f'{rotf} → pior_queda_bps ({P})', 'L', "'O desconto pode piorar'")
    add(9, 'Capacidade por pregão (2023–2026)', f'US$ {num(cap["2023"] / 1e3, 0)}–{num(cap["2026"] / 1e3, 0)} mil', f'{cap["2023"]:.0f} – {cap["2026"]:.0f}', 'T16_correcao_de_erro.json → capacidade_5pct_sessao_usd_por_ano', 'L', "'Capacidade pequena'")
    # 10 conclusões
    add(10, 'Conclusão 2: bruto contra custo', f"{num(gross, 1, True)} contra {num(mid_cost, 1)}", f'{gross:.3f} contra {mid_cost:.3f}', 'summary.json → mean_gross_mid_bps; custo = bruto − saldo', 'C', "A arbitragem na reabertura não paga:</b>")
    add(10, 'Conclusão 5: risco de base 12 meses', num(F['r12'].desvio_padrao_bps, 0) + ' bps', F['r12'].desvio_padrao_bps, 'T14_risco_de_base.csv → desvio_padrao_bps (12 meses)', 'L', "Para quem só carrega")
    an = D['annual'].set_index('year')
    wk = D['t13'].set_index('periodo')
    led = pd.read_csv(ROOT / 'results/T2_trade_ledger.csv')
    led = led[(led.horizon_hours == 6) & (led.evaluated_trade == True)].copy()
    led['ano'] = pd.to_datetime(led.t_0, utc=True).dt.year
    arb = led.groupby('ano').gross_mid_bps.agg(['mean', 'count'])
    for y in [2021, 2023, 2025, 2026]:
        add(10, f'Tabela por ano {y}: desvio mediano', num(an.loc[y, 'median_abs_bps'], 0), an.loc[y, 'median_abs_bps'], f'T11_regime_anual.csv → median_abs_bps ({y})', 'L', "ev_row('Desvio mediano, bps'")
        add(10, f'Tabela por ano {y}: horas a até 25 bps', pct(an.loc[y, 'within_25_bps']), an.loc[y, 'within_25_bps'], f'T11_regime_anual.csv → within_25_bps ({y})', 'L', "ev_row('Horas a até 25 bps do ouro'")
        add(10, f'Tabela por ano {y}: volume Binance, US$ bi', num(an.loc[y, 'usd_volume_millions'] / 1000, 1), an.loc[y, 'usd_volume_millions'], f'T11_regime_anual.csv → usd_volume_millions ({y})', 'C', "ev_row('Volume na Binance, US$ bi'")
        add(10, f'Tabela por ano {y}: R² salto do ouro × token', num(wk.loc[str(y), 'r2'], 2), wk.loc[str(y), 'r2'], f'T13_fim_de_semana.csv → r2 (periodo {y}; OLS do salto do ouro sobre o movimento do token, HC1)', 'L', "ev_row('Salto do ouro explicado pelo token (R²)'")
        yv = D['plac']['ganho_por_ano_calendario_bps'][str(y)]
        add(10, f'Tabela por ano {y}: ganho da rotação', num(yv, 0, True) if yv else '0', yv, f'T12_rotacao_placebo.json → ganho_por_ano_calendario_bps.{y}', 'L', "ev_row('Rotação: ganho no ano, bps'")
    for y in [2025, 2026]:
        add(10, f'Tabela por ano {y}: arbitragem, bruto em 6 h', num(arb.loc[y, 'mean'], 1, True), f"{arb.loc[y, 'mean']:.3f} ({int(arb.loc[y, 'count'])} operações)", 'T2_trade_ledger.csv → média de gross_mid_bps (6 h, avaliadas)', 'C', "ev_row('Arbitragem: ganho bruto em 6 h, bps'")
    add(10, 'p-valor da tendência trimestral', num(D['t4']['p_value_exploratory'], 2), D['t4']['p_value_exploratory'], 'T4_trend.csv → p_value_exploratory', 'L', "a tendência trimestral do desvio ainda não é significativa")
    return pd.DataFrame(R)


def check_pdf(df):
    import pymupdf
    with pymupdf.open(ROOT / 'slides' / 'entrega_v3.pdf') as d:
        pages = [re.sub(r'\s+', ' ', p.get_text()) for p in d]
    ok = []
    for _, r in df.iterrows():
        txt = pages[r.slide - 1]
        parts = [x.strip() for x in re.split(r' / | · |; | a | contra |–|\[|\]', r.mostrado) if x.strip() and x.strip() not in ('de', 'bps')]
        parts = [p.replace(' bps', '').replace('US$ ', '').replace(' mil', '').replace(' bi', '').replace(' operações', '') for p in parts]
        parts = [p for p in parts if p]
        ok.append('sim' if all(p in txt for p in parts) else 'conferir')
    df['no_pdf'] = ok
    return df


CSS = """
@font-face{font-family:Slab;src:url("../../slides/design-systems/assets/fonts/AlfaSlabOne-Regular.ttf")}
@font-face{font-family:Manrope;src:url("../../slides/design-systems/assets/fonts/Manrope.ttf");font-weight:200 800}
@font-face{font-family:PlexMono;src:url("../../slides/design-systems/assets/fonts/IBMPlexMono-Regular.ttf")}
@page{size:A4 landscape;margin:14mm 12mm}
body{font-family:Manrope,Arial,sans-serif;font-variant-ligatures:none;font-feature-settings:"liga" 0,"calt" 0;color:#1C1A17;font-size:10.5px;line-height:1.4;background:#fff}
h1{font-family:Slab,serif;font-weight:400;font-size:30px;margin:0 0 6px}
h2{font-family:Slab,serif;font-weight:400;font-size:19px;margin:18px 0 6px;border-bottom:3px solid #1C1A17;padding-bottom:3px;break-after:avoid}
h3{font-size:12.5px;margin:12px 0 4px;break-after:avoid}
.k{font-family:PlexMono,monospace;color:#B23A1E;letter-spacing:.12em;font-size:10px;text-transform:uppercase}
p{margin:4px 0}
table{border-collapse:collapse;width:100%;margin:4px 0 8px}
th{background:#1C1A17;color:#F2EADB;text-align:left;padding:4px 6px;font-size:9.5px}
td{border-bottom:1px solid #CFC5AE;padding:3px 6px;vertical-align:top;font-size:9.5px}
td.m,th.m{font-family:PlexMono,monospace;white-space:nowrap}
tr{break-inside:avoid}
.fig{border:2px solid #1C1A17;background:#F4ECDB;padding:6px 8px;break-inside:avoid;margin:4px 0}
.fig svg{width:100%;height:auto;max-height:118mm}
.figbox{break-inside:avoid;margin-bottom:10px}
.tag{display:inline-block;padding:0 5px;border-radius:2px;font-size:9px}
.t-L{background:#E6EEDC}.t-C{background:#E9DFC6}.t-M{background:#F3D3C8}.t-E{background:#D6E3F0}
.box{border:2px solid #1C1A17;background:#F4ECDB;padding:8px 10px;margin:6px 0}
.no{color:#B23A1E;font-weight:800}
.pb{break-before:page}
"""


def table_html(df):
    head = '<tr><th>Item</th><th class="m">No slide</th><th class="m">Valor exato</th><th>Origem (arquivo → campo)</th><th>Tipo</th><th class="m">Onde entra</th><th>Script que gera</th><th>No PDF</th></tr>'
    kinds = {v: k for k, v in KIND.items()}

    def fmt(v):
        if isinstance(v, float):
            return f'{v:.6g}'
        return str(v)
    body = ''.join(
        f'<tr><td>{html.escape(r.item)}</td><td class="m">{html.escape(r.mostrado)}</td><td class="m">{html.escape(fmt(r.exato))}</td>'
        f'<td>{html.escape(r.origem)}</td><td><span class="tag t-{kinds[r.tipo]}">{r.tipo}</span></td><td class="m">{r.linha}</td>'
        f'<td class="m">{html.escape(r.gera)}</td><td class="{"" if r.no_pdf == "sim" else "no"}">{r.no_pdf}</td></tr>' for r in df.itertuples())
    return f'<table>{head}{body}</table>'


def build_doc(D, df):
    F = facts(D)
    k = F['prim']['k_bps']
    probs = pd.read_csv(ROOT / 'results/v2/T19_regimes_probabilidades.csv')
    budget = D['budget']
    gross, mid_net, mid_cost = F['gross'], F['mid_net'], F['mid_cost']
    titles = {1: 'Capa', 2: 'I · Motivação e hipóteses', 3: 'II · Dados', 4: 'III · Metodologia I', 5: 'III · Metodologia II', 6: 'IV · Resultado 1 (H1)',
              7: 'IV · Resultado 2 (H2)', 8: 'IV · Resultado 3 (H3)', 9: 'IV · Resultado 4 (robustez)', 10: 'V · Conclusões'}
    n_manual = int((df.tipo == KIND['M']).sum())
    n_check = int((df.no_pdf != 'sim').sum())
    out = [f"""<div class="k">7º Datathon de Moedas Digitais · FGV EESP · entrega v3</div>
<h1>PAXG contra o ouro: números, gráficos e tabelas</h1>
<p>Este caderno lista tudo o que aparece com número no deck <b>slides/entrega_v3.pdf</b>: {len(df)} valores, 7 gráficos e 5 tabelas. Para cada valor, ele mostra o arquivo e o campo de origem, a linha de <b>src/v3_deck.py</b> onde o valor entra no slide e o script que gera o arquivo. A coluna <b>No PDF</b> confere automaticamente se o valor aparece no texto da página ({n_check} a conferir à mão).</p>
<div class="box"><b>Como ajustar</b>
<p><b>Mudar um texto ou um número escrito à mão</b> (<span class="tag t-M">escrito à mão</span>, {n_manual} casos): editar a linha indicada em src/v3_deck.py e rodar <code>python -m src.v3_deck</code>. Esses números não se atualizam sozinhos; se a análise mudar, eles precisam ser trocados.</p>
<p><b>Mudar um resultado</b> (<span class="tag t-L">lido de arquivo</span> ou <span class="tag t-C">calculado no deck</span>): rodar de novo o script indicado na coluna "Script que gera" e depois <code>python -m src.v3_deck</code>. Não rodar <code>python run_all.py</code> com --all, --figures, --v5 ou --package, porque eles reescrevem a v1.</p>
<p><b>Mudar um gráfico</b>: a seção de gráficos indica a função e a linha da chamada. As cores da v3 são trocadas só na memória, no topo de src/v3_deck.py.</p>
<p><b>Fato externo</b> (<span class="tag t-E">fato externo</span>): número tirado de uma fonte pública; a fonte está na coluna de origem e no relatório de fontes.</p>
<p>Depois de qualquer ajuste: <code>python -m src.v3_numeros</code> (refaz este caderno e a conferência), <code>python -m src.v3_package</code> e <code>python entrega/v1_final_2026-11-08/conferir_hashes.py</code>.</p></div>
<p>A mesma tabela, em formato editável, está em <b>results/v3/numeros_v3.csv</b>.</p>"""]
    out.append('<h2 class="pb">1 · Números por slide</h2>')
    for sl in range(1, 11):
        sub = df[df.slide == sl]
        if len(sub):
            out.append(f'<h3>Slide {sl} · {titles[sl]}</h3>' + table_html(sub))

    def fig(title, svg, data, func, call, note=''):
        return (f'<div class="figbox"><h3>{title}</h3><div class="fig">{svg}</div><p><b>Dados:</b> {data}. <b>Função:</b> {func}. '
                f'<b>Chamada no deck:</b> {call}.{" " + note if note else ""}</p></div>')
    out.append('<h2 class="pb">2 · Gráficos</h2>')
    out.append(fig('Slide 6 (a) · Desvio diário e nível estimado', fig_level(D['serie'], F['kx_ext']), 'results/T15_componentes_serie.csv (desvio_bps, nivel_suavizado_bps); rótulo de mar/2024 de T11_kraken_extremos.csv',
                   'fig_level, src/report_v5.py:74', line_of("fig_level(D['serie']")))
    out.append(fig('Slide 6 (b) · Regimes de Markov filtrados', V.fig_hmm(D['serie'], probs), 'results/T15_componentes_serie.csv e results/v2/T19_regimes_probabilidades.csv (p_desconto, p_neutro, p_premio)',
                   'fig_hmm, src/v3_deck.py:' + str(next(i + 1 for i, s in enumerate(DECK_SRC) if s.startswith('def fig_hmm'))), line_of("fig_hmm(D['serie'], probs)"),
                   'Regime dominante = probabilidade acima de 50%. Em set/2022, primeira janela, o estado de maior média cobriu dias de desvio negativo.'))
    out.append(fig('Slide 7 (a) · Variação do desvio no fim de semana', fig_weekend(D['t13r']), 'results/T13_fim_de_semana_resumo.json', 'fig_weekend, src/report_v5.py:124', line_of("fig_weekend(t13r)")))
    out.append(fig('Slide 7 (b) · Cascata: ganho bruto, custo e saldo', fig_waterfall(gross, mid_cost, mid_net), f'summary.json mean_gross_mid_bps = {gross:.3f}; custo = {mid_cost:.3f}; saldo = {mid_net:.3f} (T2_convergencia.csv, cenário 5, 2, 1, 2, 2)',
                   'fig_waterfall, src/report_v5.py:163', line_of("fig_waterfall(gross, mid_cost, mid_net)")))
    out.append(fig('Slide 8 (a) · Ganho acumulado da rotação e desvio diário', V.shift_label(fig_rotation(D['curve'], k), 'custos originais:', 14), 'results/T12_rotacao_curva.csv', 'fig_rotation, src/report_v5.py:182',
                   line_of("shift_label(fig_rotation(D['curve'], k)"), 'No deck, o rótulo interno do painel de baixo é removido e vai para a nota.'))
    out.append(fig('Slide 9 (b) · A mesma regra no XAUT', V.shift_label(fig_xaut_vs_paxg(D['curve'], D['x17c']), 'XAUT:', 30), 'results/T12_rotacao_curva.csv e results/v2/T17_xaut_curva.csv', 'fig_xaut_vs_paxg, src/v2_figs.py:10',
                   line_of("fig_xaut_vs_paxg(D['curve'], D['x17c'])")))
    out.append(fig('Slide 9 (c) · Placebo com 1.000 datas sorteadas', fig_placebo(D['sims'], D['plac']['ganho_anual_bps']), 'results/T12_rotacao_placebo_dist.csv (ganho_anual_bps) e T12_rotacao_placebo.json', 'fig_placebo, src/report_v5.py:225',
                   line_of("fig_placebo(D['sims']")))

    out.append('<h2 class="pb">3 · Tabelas</h2>')
    S = D['S']
    out.append(f"""<h3>Slide 3 · Checagens em outras fontes</h3><table><tr><th>Checagem</th><th class="m">Valor exato</th><th>Origem</th></tr>
<tr><td>Nosso ouro × GLD por onça (diferença mediana)</td><td class="m">{D['gld']['median_abs_level_difference_bps']:.4f} bps</td><td>results/QA_gold_reference_summary.json</td></tr>
<tr><td>USDT/USD: Bitfinex × Coinbase</td><td class="m">{S['fx_source_median_abs_difference_bps']:.4f} bps em {S['fx_source_comparison_hours']} horas</td><td>results/summary.json</td></tr>
<tr><td>PAXG: Binance × Kraken nos extremos</td><td class="m">{F['kx_diff']:.4f} bps</td><td>results/T11_kraken_extremos.csv</td></tr></table>""")
    conv = D['conv']
    out.append(f"""<h3>Slide 7 (c) · Cenários de custo da arbitragem (6 h)</h3><table><tr><th>Cenário</th><th class="m">Saldo médio, bps</th><th class="m">Positivas</th><th class="m">Avaliadas</th><th>Origem</th></tr>
<tr><td>Original (taxa 10, spread 10, ouro 1, câmbio 2, desliz. 2)</td><td class="m">{conv['orig'].mean_model_bps:.3f}</td><td class="m">{F['orig_pos']}</td><td class="m">{int(conv['orig'].evaluated_trades)}</td><td>results/T2_convergencia.csv</td></tr>
<tr><td>Intermediário (5, 2, 1, 2, 2)</td><td class="m">{conv['mid'].mean_model_bps:.3f}</td><td class="m">{F['mid_pos']}</td><td class="m">{int(conv['mid'].evaluated_trades)}</td><td>results/T2_convergencia.csv</td></tr>
<tr><td>Mínimo da grade (2, 2, 1, 0, 0)</td><td class="m">{conv['low'].mean_model_bps:.3f}</td><td class="m">—</td><td class="m">{int(conv['low'].evaluated_trades)}</td><td>results/T2_convergencia.csv</td></tr></table>
<p>Ganho bruto por horizonte (results/T10_cost_budget.csv, IC 95%, blocos de 4 semanas):</p>
<table><tr><th class="m">Horizonte (h)</th><th class="m">n</th><th class="m">Bruto médio</th><th class="m">IC baixo</th><th class="m">IC alto</th><th class="m">Custo modelado</th><th class="m">Saldo</th></tr>
{''.join(f'<tr><td class="m">{int(r.horizon_hours)}</td><td class="m">{int(r.n)}</td><td class="m">{r.mean_gross_bps:.3f}</td><td class="m">{r.gross_lo:.3f}</td><td class="m">{r.gross_hi:.3f}</td><td class="m">{r.mean_modeled_cost_bps:.3f}</td><td class="m">{r.mean_model_bps:.3f}</td></tr>' for r in budget.itertuples())}</table>""")
    t14 = D['t14']
    out.append(f"""<h3>Slide 8 · Quem só carrega o token: risco de base contra a taxa do ETF</h3><p>Fonte: results/T14_risco_de_base.csv. Meses até empatar em custo: GLD {F['gld_m']:.2f}, GLDM {F['gldm_m']:.2f} (T3_custos_etfs.csv, US$ 10 mil, taxa 5, spread 2, câmbio 2). Ida e volta no token: {F['rt_mid']:.1f} bps.</p>
<table><tr><th>Horizonte</th><th class="m">Pregões</th><th class="m">n</th><th class="m">DP da variação</th><th class="m">p05</th><th class="m">p95</th><th class="m">Taxa GLDM</th><th class="m">Taxa GLD</th></tr>
{''.join(f'<tr><td>{r.horizonte}</td><td class="m">{int(r.pregoes)}</td><td class="m">{int(r.n)}</td><td class="m">{r.desvio_padrao_bps:.2f}</td><td class="m">{r.p05_bps:.2f}</td><td class="m">{r.p95_bps:.2f}</td><td class="m">{r.taxa_gldm_no_horizonte_bps:.2f}</td><td class="m">{r.taxa_gld_no_horizonte_bps:.2f}</td></tr>' for r in t14.itertuples())}</table>""")
    rob = df[df.slide == 9].iloc[:8]
    out.append('<h3>Slide 9 (a) · Robustez da rotação</h3><table><tr><th>Configuração</th><th class="m">No slide (ciclos · bps/ano · IC 90%)</th><th class="m">Valor exato</th><th>Origem</th></tr>'
               + ''.join(f'<tr><td>{html.escape(r.item.replace("Tabela (a): ", ""))}</td><td class="m">{html.escape(r.mostrado)}</td><td class="m">{html.escape(str(r.exato))}</td><td>{html.escape(r.origem)}</td></tr>' for r in rob.itertuples())
               + '</table><p>IC 90% por bootstrap circular em blocos de 6 meses, 5.000 repetições. Seleção das linhas: rot_row() em src/v2_report_pages.py:57 e filtros em src/v3_deck.py (hm, hb, xa).</p>')
    out.append("""<h3>Slide 5 · As duas operações testadas</h3><table><tr><th></th><th>Arbitragem na reabertura</th><th>Rotação GLDM ↔ PAXG</th></tr>
<tr><td>Quem</td><td>Arbitrador com conta em cripto e em ouro</td><td>Quem já quer ouro em dólares</td></tr>
<tr><td>Sinal</td><td>1 h após a reabertura, desvio absoluto acima de 10 bps</td><td>Média do pregão fora da faixa de ±19 bps</td></tr>
<tr><td>Saída</td><td>Prazo fixo: 1, 6 ou 24 h</td><td>Quando o desvio cruza a outra ponta</td></tr>
<tr><td>Custo</td><td>Quatro execuções; ver slide 7</td><td>Duas trocas por ciclo; ver slide 8</td></tr>
<tr><td>Venda a descoberto</td><td>Sim</td><td>Não</td></tr></table><p>Texto escrito à mão em src/v3_deck.py (bloco "05 · metodologia II"); os custos vêm dos valores do slide 5 na seção 1.</p>""")
    out.append(SOURCES)
    return out


_SRC_ROWS = [
    ('Makarov e Schoar (2020)', 'Trading and arbitrage in cryptocurrency markets. Journal of Financial Economics 135(2), 293–319.', 'Existe; volume, número e páginas conferem.',
     'Diferenças grandes e recorrentes entre corretoras, maiores entre países, ligadas a controles de capital. Texto do slide 2 ajustado para "recorrentes, sobretudo entre países".',
     'https://econpapers.repec.org/RePEc:eee:jfinec:v:135:y:2020:i:2:p:293-319'),
    ('Shleifer e Vishny (1997)', 'The limits of arbitrage. Journal of Finance 52(1), 35–55.', 'Existe; confere.', 'Arbitragem exige capital e tem risco; fica ineficaz quando o preço se afasta muito. O texto do slide confere.',
     'https://ideas.repec.org/a/bla/jfinan/v52y1997i1p35-55.html'),
    ('Lyons e Viswanath-Natraj (2023)', 'What keeps stablecoins stable? Journal of International Money and Finance 131, 102777.', 'Existe; confere.',
     'A estabilidade vem do desenho da arbitragem (criação e resgate no emissor). Texto ajustado para "arbitragem de criação e resgate".', 'https://ideas.repec.org/a/eee/jimfin/v131y2023ics0261560622001802.html'),
    ('Petajisto (2017)', 'Inefficiencies in the pricing of exchange-traded funds. Financial Analysts Journal 73(1), 24–54.', 'Existe; confere.',
     'Desvios de até cerca de 200 bps, maiores em fundos com ativos internacionais ou ilíquidos. O texto antigo ("mesmo ETFs líquidos") exagerava; foi trocado.',
     'https://econpapers.repec.org/RePEc:taf:ufajxx:v:73:y:2017:i:1:p:24-54'),
    ('Cong, Mayer e Rabetti (2026)', 'Tokenizing Real-World Assets. The Wharton Initiative on Financial Policy and Regulation (WIFPR), maio de 2026, 52 p.', 'Existe; PDF aberto e lido.',
     'O apêndice A.2 (citando Harvey et al., 2025) diz que o ouro tokenizado acompanha o ouro de perto (correlação diária de 0,99) e tem liquidez menor que a do GLD. O texto antigo ("descoberta de preço limitada") não correspondia; foi trocado.',
     'https://wffi.wharton.upenn.edu/wp-content/uploads/2026/05/WIFPR-Tokenizing-Real-World-Assets-Cong-Mayer-and-Rabetti.pdf'),
    ('Harvey (1989)', 'Forecasting, Structural Time Series Models and the Kalman Filter. Cambridge University Press.', 'Existe; confere.', 'Referência do modelo de componentes não observados (slide 5).',
     'https://find.library.upenn.edu/catalog/9979239295203681'),
    ('Bailey et al. (2014), suplementar', 'Pseudo-mathematics and financial charlatanism. Notices of the AMS 61(5), 458–471.', 'Existe; confere.', 'Risco de sobreajuste em backtests.', 'https://www.eurekalert.org/news-releases/817304'),
    ('Lo e MacKinlay (1990), suplementar', 'An econometric analysis of nonsynchronous trading. Journal of Econometrics 45, 181–211.', 'Existe; confere.', 'Negociação não sincronizada.',
     'https://econpapers.repec.org/RePEc:eee:econom:v:45:y:1990:i:1-2:p:181-211'),
    ('Politis e Romano (1992), suplementar', 'A circular block-resampling procedure for stationary data. Em LePage e Billard (orgs.), Exploring the Limits of Bootstrap, Wiley.', 'Confirmada por citações secundárias; a página da Wiley não foi aberta.',
     'Bootstrap circular em blocos, usado nos IC.', 'https://econpapers.repec.org/paper/bocusug26/25.htm'),
    ('Paxos, taxas do PAXG', 'PAX Gold (PAXG) Overview, support.paxos.com.', 'Confere: resgate em faixas de 0,125%, 0,25%, 0,35% e 0,5% (desde 01/09/2026); sem taxa de custódia; criação isenta até 01/01/2027.',
     'Os termos do PAXG exigem cliente verificado para resgatar ("Only verified Customers may … redeem PAXG"). São as condições atuais, não um histórico 2020–2026.',
     'https://support.paxos.com/articles/5590384005-pax-gold-paxg-overview'),
    ('SPDR, taxas do GLD e do GLDM', 'Páginas do emissor (SSGA / spdrgoldshares.com).', 'Confere: GLD 0,40% ao ano; GLDM 0,10% ao ano (taxa atual).', 'Comparação de custo de carregar, com as taxas de hoje.',
     'https://www.ssga.com/us/en/individual/etfs/spdr-gold-minishares-gldm'),
    ('CME, ouro 24/7', 'Contrato 1-Ounce Gold negociado também no fim de semana desde o fim de julho de 2026.', 'Confere.',
     'Por isso o slide 2 deixou de dizer "só o token negocia" e passou a dizer que o XAUUSD para e o token segue negociando.',
     'https://www.cmegroup.com/media-room/press-releases/2026/7/27/traders_drive_strongdemandinfirstweekendofcmegroups247goldfuture.html'),
    ('Horário do ouro', 'Sexta 17h a domingo 18h, hora de Nova York.', 'Confere com o código: src/panel.py:14 (gold_open_mask).', 'Mesma janela usada para definir a reabertura.', '—'),
    ('Dados de mercado', 'Binance (PAXGUSDT, arquivo público desde 28/08/2020 12:00 UTC), Bitfinex (USDT/USD e XAUT/USD), Dukascopy (XAUUSD compra e venda), Coinbase (USDT-USD), Kraken (PAXG/USD, consulta pontual à API).',
     'Confere: arquivos brutos em data/raw com manifesto e hash; Kraken salva em results/T11_kraken_*.csv.', 'Slide 3 ajustado: "cada arquivo bruto tem data, URL e hash; a Kraken entra por consulta pontual à API".',
     'https://github.com/binance/binance-public-data'),
]
SOURCES = ('<h2 class="pb">4 · Fontes verificadas (08/11/2026)</h2><p>Cada referência foi procurada na web; quando possível, o texto original foi aberto. A coluna "O que o deck diz" compara a afirmação do slide com o que a fonte de fato mostra.</p>'
           '<table><tr><th>Fonte</th><th>Citação</th><th>Existe e confere?</th><th>O que o deck diz × o que a fonte diz</th><th>Link</th></tr>'
           + ''.join(f'<tr><td><b>{html.escape(a)}</b></td><td>{html.escape(b)}</td><td>{html.escape(c)}</td><td>{html.escape(d)}</td><td style="word-break:break-all;font-size:8px">{html.escape(e)}</td></tr>' for a, b, c, d, e in _SRC_ROWS)
           + '</table><p><b>Atenção para a banca:</b> segundo Cong, Mayer e Rabetti (2026), Harvey et al. (2025) relatam desvios do PAXG "tipicamente abaixo de 0,1%" nas horas em que os dois mercados negociam. A nossa mediana em hora comum é 36 bps (0,36%), conferida contra Kraken e GLD. A diferença pode vir de corretora, horário, câmbio USDT/USD ou métrica (retorno contra nível); vale ter a resposta pronta.</p>')


def main():
    D = load()
    df = check_pdf(collect(D))
    v3 = ROOT / 'results' / 'v3'
    v3.mkdir(parents=True, exist_ok=True)
    df.to_csv(v3 / 'numeros_v3.csv', index=False, encoding='utf-8-sig')
    outdir = ROOT / 'entrega' / 'v3'
    outdir.mkdir(parents=True, exist_ok=True)
    html_path, pdf_path = outdir / 'numeros_graficos_tabelas_v3.html', outdir / 'numeros_graficos_tabelas_v3.pdf'
    doc = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>PAXG contra o ouro · números, gráficos e tabelas</title><style>' + CSS + '</style></head><body>' + ''.join(build_doc(D, df)) + '</body></html>'
    html_path.write_text(doc, encoding='utf-8')
    from playwright.sync_api import sync_playwright
    exe = next((p for p in [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', shutil.which('google-chrome') or ''] if p and Path(p).is_file()), None)
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=exe, headless=True)
        pg = b.new_page()
        pg.goto(html_path.as_uri())
        pg.evaluate('document.fonts.ready')
        pg.wait_for_timeout(300)
        pg.pdf(path=str(pdf_path), format='A4', landscape=True, print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template='<span></span>',
               footer_template='<div style="font-size:8px;width:100%;text-align:right;padding-right:12mm;color:#6B6457">PAXG contra o ouro · números da entrega v3 · <span class="pageNumber"></span>/<span class="totalPages"></span></div>')
        b.close()
    print('valores', len(df), 'escritos à mão', int((df.tipo == KIND['M']).sum()), 'a conferir', df[df.no_pdf != 'sim'][['slide', 'item', 'mostrado']].to_dict('records'))


if __name__ == '__main__':
    main()
