"""Entrega v2: conteúdo dos 10 slides (capa + 9). Cópia de report_v5_pages.py com as correções do PLANO_ENTREGA_V2.md. Todos os números vêm de results/ (ver load())."""
from __future__ import annotations

import pandas as pd

from .v2_figs import fig_onchain, fig_xaut_vs_paxg
from .report_v5 import (card, fig, fig_annual, fig_basis_risk, fig_costs, fig_level, fig_placebo, fig_r2, fig_rotation,
                        fig_waterfall, fig_week, fig_weekend, num, page, pct, read, readj, risk, step, symbol)


def load():
    from .deck_v4 import crossing, scenario_row
    D = {}
    D['S'] = readj('summary.json')
    D['R'] = readj('T11_regime_resumo.json')
    D['annual'] = read('T11_regime_anual.csv')
    D['mensal'] = read('T11_regime_mensal.csv').set_index('month')
    D['t15'] = readj('T15_componentes.json')
    D['serie'] = read('T15_componentes_serie.csv')
    D['t16'] = readj('T16_correcao_de_erro.json')
    D['t13'] = read('T13_fim_de_semana.csv')
    D['t13r'] = readj('T13_fim_de_semana_resumo.json')
    D['t14'] = read('T14_risco_de_base.csv')
    D['rot'] = read('T12_rotacao_resumo.csv')
    D['plac'] = readj('T12_rotacao_placebo.json')
    D['sims'] = read('T12_rotacao_placebo_dist.csv').ganho_anual_bps.values
    D['curve'] = read('T12_rotacao_curva.csv')
    D['cyc'] = read('T12_rotacao_ciclos.csv')
    D['kx'] = read('T11_kraken_extremos.csv')
    D['grid'] = read('T10_grid_summary.csv')
    D['budget'] = read('T10_cost_budget.csv')
    D['fc'] = read('T8_forecast_summary.csv').set_index('model')
    D['pair'] = read('T7_paired_changes.csv').set_index('comparison')
    D['fx'] = read('T9_fx_coverage.csv')
    D['t1'] = read('T1_fidelidade.csv')
    D['t4'] = read('T4_trend.csv').iloc[0]
    D['gld'] = readj('QA_gold_reference_summary.json')
    import json as _json
    from .common import ROOT as _ROOT
    v2 = _ROOT / 'results' / 'v2'
    D['x17'] = pd.read_csv(v2 / 'T17_xaut_resumo.csv')
    D['x17c'] = pd.read_csv(v2 / 'T17_xaut_curva.csv')
    D['x17j'] = _json.loads((v2 / 'T17_xaut_resumo.json').read_text(encoding='utf-8'))
    D['r19'] = pd.read_csv(v2 / 'T19_regimes_resumo.csv')
    D['r19j'] = _json.loads((v2 / 'T19_regimes_resumo.json').read_text(encoding='utf-8'))
    D['t18'] = pd.read_csv(v2 / 'T18_onchain_semanal.csv') if (v2 / 'T18_onchain_semanal.csv').exists() else None
    D['t18j'] = _json.loads((v2 / 'T18_onchain_resumo.json').read_text(encoding='utf-8')) if (v2 / 'T18_onchain_resumo.json').exists() else None
    g = read('T2_convergencia.csv')
    D['conv'] = {k: scenario_row(g, *a) for k, a in {'orig': (10, 10, 1, 2, 2), 'mid': (5, 2, 1, 2, 2), 'low': (2, 2, 1, 0, 0)}.items()}
    t3 = read('T3_custos_etfs.csv')
    D['cross'] = {'gld_mid': crossing(t3, 'GLD', 5, 2), 'gldm_mid': crossing(t3, 'GLDM', 5, 2),
                  'gld_orig': crossing(t3, 'GLD', 10, 10), 'gldm_orig': crossing(t3, 'GLDM', 10, 10),
                  'gldm_mid_store10': crossing(t3, 'GLDM', 5, 2, storage=10)}
    return D


def rot_row(rot, config, scen, lag=1):
    q = rot[(rot.config == config) & (rot.cenario_custos == scen) & (rot.lag_pregoes == lag)]
    assert len(q) == 1, (config, scen, lag)
    return q.iloc[0]


def facts(D):
    """Números derivados usados em mais de uma página."""
    S, a = D['S'], D['annual'].set_index('year')
    rot = D['rot']
    F = {}
    F['y26'], F['y20'] = a.loc[2026], a.loc[2020]
    F['prim'] = rot[(rot.papel == 'principal') & (rot.cenario_custos == 'intermediario')].iloc[0]
    F['prim_o'] = rot[(rot.papel == 'principal') & (rot.cenario_custos == 'original')].iloc[0]
    F['k'] = int(F['prim'].k_bps)
    F['gross'] = S['mean_gross_mid_bps']
    F['mid_net'] = float(D['conv']['mid'].mean_model_bps)
    F['mid_cost'] = F['gross'] - F['mid_net']
    F['n_eval'] = int(S['evaluated_trades'])
    F['mid_pos'] = int(round(float(D['conv']['mid'].positive_fraction) * int(D['conv']['mid'].evaluated_trades)))
    F['orig_pos'] = int(round(float(D['conv']['orig'].positive_fraction) * int(D['conv']['orig'].evaluated_trades)))
    mid = D['conv']['mid']
    F['tip_mid'] = -int(mid.evaluated_trades) * float(mid.mean_model_bps) / (int(mid.signals) - int(mid.evaluated_trades))
    cx = D['cross']
    assert cx['gldm_mid_store10'].status == 'token_always_more_expensive'
    F['gld_m'], F['gldm_m'] = float(cx['gld_mid'].crossing_months), float(cx['gldm_mid'].crossing_months)
    F['gld_o'], F['gldm_o'] = float(cx['gld_orig'].crossing_months), float(cx['gldm_orig'].crossing_months)
    F['rt_mid'], F['rt_orig'] = float(cx['gld_mid'].token_cost_bps), float(cx['gld_orig'].token_cost_bps)
    F['r12'] = D['t14'].set_index('horizonte').loc['12 meses']
    F['n_grid'] = int(D['grid'].configurations.sum())
    F['cap'] = D['t16']['capacidade_5pct_sessao_usd_por_ano']
    F['vol'] = D['t16']['volume_binance_sessao_mediana_usd_por_ano']
    s = D['serie'].copy()
    s['dia'] = pd.to_datetime(s.dia)
    F['lvl_min'], F['lvl_max'] = float(s.nivel_suavizado_bps.min()), float(s.nivel_suavizado_bps.max())
    F['day_min'] = float(s.desvio_bps.min())
    m24 = s[(s.dia.dt.strftime('%Y-%m') == '2024-03') & (s.desvio_bps <= -200)].desvio_bps
    F['m24_n'], F['m24_lo'], F['m24_hi'] = len(m24), float(-m24.max()) / 100, float(-m24.min()) / 100
    j21 = D['mensal'].loc['2021-01']
    F['j21_med'], F['j21_p10'] = float(j21.median_bps), float(j21.p10_bps)
    cyc = D['cyc']
    F['share_week'] = float(cyc[cyc.dias > 7].resultado_bps.sum() / cyc.resultado_bps.sum())
    kx = D['kx']
    F['ex'] = kx[kx.t.str.startswith('2024-03-04 16')].iloc[0]
    F['kx_diff'] = float((kx.kraken_bps - kx.basis_log_bps).abs().median())
    d1 = kx[kx.t.str.startswith('2024-03-01')]
    F['kx_ext'] = f'{num(d1.kraken_bps.max(), 0)} a {num(d1.kraken_bps.min(), 0)}'
    return F


def build_main(D, n_tests=None):
    S, R = D['S'], D['R']
    t15, t16, t13r = D['t15'], D['t16'], D['t13r']
    F = facts(D)
    prim, prim_o, k = F['prim'], F['prim_o'], F['k']
    gross, mid_net, mid_cost = F['gross'], F['mid_net'], F['mid_cost']
    r12, cap = F['r12'], F['cap']
    orig, low = D['conv']['orig'], D['conv']['low']
    yr = D['plac']['ganho_por_ano_calendario_bps']
    rot = D['rot']
    T = 10
    pages = []

    # ---------------- 01 · capa (sistema Áureo)
    pages.append(f"""<section class="cover">
<div class="imprint">{symbol(44, 'var(--gold)', '#F3EEE3')}BitFlow</div>
<div class="event">FGV EESP<br>7º Datathon de Moedas Digitais</div>
<div class="title"><span>PAXG</span><span class="second"><small>contra o</small> <em>ouro.</em></span></div>
<div class="mark">{symbol(262, 'var(--gold)', 'var(--gold)')}</div>
<div class="date">PAXG / 2020—2026</div>
<div class="regi"><i></i><i></i></div>
<div class="desc">Fidelidade, custos e captura do desvio<br>entre o token e o ouro, de 2020 a 2026.</div>
<div class="question">Quanto o PAXG se afasta do ouro, e quem consegue ganhar com essa diferença?</div>
<div class="cft"><span>Gabriel Navarro · Lorenzo Cavalcante · Rodrigo Menin</span><span class="mono">01 / {T:02d}</span></div>
</section>""")

    # ---------------- 02 · problema e perguntas
    vol26 = F['y26'].usd_volume_millions / 1000
    qs = [('01', 'Quanto o PAXG se afasta do ouro, e como esse desvio se comporta no tempo?', 'Medimos o desvio hora a hora e separamos o que é ruído do que é nível.', 'slides 3 a 5'),
          ('02', 'Dá para ganhar com o desvio depois dos custos? Quem consegue?', 'Comparamos a arbitragem na reabertura com a troca entre GLDM e PAXG, e repetimos a troca no XAUT.', 'slides 6 a 8'),
          ('03', 'O que muda para quem escolhe entre o token e um ETF de ouro?', 'Somamos taxas, custos de entrada e o risco de o desvio mudar.', 'slide 9')]
    qrows = ''.join(f'<div class="qrow"><span class="n">{n}</span><div><h3>{q}</h3><p>{d}</p></div><span class="w">{w}</span></div>' for n, q, d, w in qs)
    body = f"""
<div class="grid" style="grid-template-columns:.95fr 1.05fr;gap:52px">
 <div>
  <div class="h">O que é o PAXG</div>
  <p>Um token emitido pela Paxos em que cada unidade corresponde a uma onça troy de ouro guardada em cofre. Ele negocia em corretoras de criptoativos 24 horas por dia, inclusive quando o mercado de ouro está fechado. Em tese, deveria valer o ouro. Na prática, em janeiro de 2021, 90% das horas ficaram mais de {num(F['j21_p10'], 0)} bps acima do ouro; em março de 2024, o token ficou de {num(F['m24_lo'], 1)}% a {num(F['m24_hi'], 1)}% abaixo durante três pregões.</p>
  <div class="fig" style="margin-top:14px">{fig_week()}</div>
  <div class="h" style="margin-top:16px">Por que importa</div>
  <p>Só na Binance, mais de US$ {num(vol26, 0)} bilhões em PAXG foram negociados em 2026, contando apenas as horas em que o ouro também cota. Para quem usa o token no lugar do ouro, a diferença de preço é custo ou oportunidade. O tema fica entre a tokenização de ativos reais (RWA) e as stablecoins, e o trabalho conversa com duas literaturas: desvios de preço em ETFs (Petajisto, 2017) e paridade de stablecoins (Lyons e Viswanath-Natraj, 2023).</p>
 </div>
 <div>
  <div class="h">Três perguntas</div>
  {qrows}
  <div class="h" style="margin-top:20px">A tese</div>
  <div class="call serif"><p>O PAXG acompanha o ouro dia a dia, mas o desvio tem dois ritmos: um ruído que some em poucos pregões e um nível que dura meses. A arbitragem na reabertura do fim de semana, com saída em até 24 h, não paga; quem já quer ouro captura o desvio trocando de veículo; quem só carrega o token assume o risco desse nível.</p></div>
 </div>
</div>"""
    pages.append(page(2, 'O PAXG deveria valer uma onça de ouro, mas seu preço se afasta do ouro por meses', body, total=T,
                      kicker='Problema / Pergunta e tese', theme='light roomy big',
                      source='Paxos (termos do PAXG); Binance (volume em dólares nas horas com ouro ativo). 100 bps = 1%.'))

    # ---------------- 03 · dados e medida
    ex = F['ex']
    rail = ''.join([
        step(1, 'Preço do token', 'Último negócio da hora no par PAXG/USDT da Binance.', f'{num(ex.p_usdt, 2)} USDT'),
        step(2, 'Moeda', 'Convertemos para dólar com o USDT/USD da Bitfinex, sem supor USDT = US$ 1.', f'× {num(ex.q, 4)} = US$ {num(ex.p_usdt * ex.q, 2)}'),
        step(3, 'Referência', 'XAUUSD da Dukascopy, só em horas com cotação ativa do ouro.', f'US$ {num(ex.S, 2)}'),
        step(4, 'Desvio', '10.000 × ln(PAXG em US$ ÷ ouro). Positivo: token acima do ouro.', f'{num(ex.basis_log_bps, 1)} bps'),
        step(5, 'Outra corretora', 'Na mesma hora, o PAXG/USD da Kraken dá um desvio parecido.', f'{num(ex.kraken_bps, 1)} bps')])
    body = f"""
<div class="grid" style="grid-template-columns:1fr 1fr;gap:40px">
 <div>
  <div class="h">De onde vêm os preços</div>
  <p>Usamos só preços observados e fontes públicas, com data, URL e hash de cada arquivo. Horas sem negócio de ouro, sem câmbio observado ou em feriados não confirmados ficam fora da amostra, e cada exclusão fica registrada com o motivo.</p>
  <table style="margin-top:10px"><thead><tr><th>Dado</th><th>Fonte</th><th>Uso</th></tr></thead><tbody>
   <tr><td>PAXG/USDT</td><td>Binance, arquivo público</td><td>hora e minuto</td></tr>
   <tr><td>USDT/USD</td><td>Bitfinex; Coinbase como checagem</td><td>conversão para dólar</td></tr>
   <tr><td>XAUUSD compra e venda</td><td>Dukascopy</td><td>referência de ouro</td></tr>
   <tr><td>GLD e GLDM</td><td>SPDR (emissor)</td><td>taxas e checagem</td></tr>
   <tr><td>PAXG/USD</td><td>Kraken</td><td>checagem dos extremos</td></tr></tbody></table>
 </div>
 <div>
  <div class="h">A amostra e as checagens</div>
  <div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:14px">
   {card(1, 'Fins de semana', [(f'{int(S["candidate_weekends"])} → {int(S["valid_weekends"])}', 'candidatos → válidos', '')], f'{int(S["candidate_weekends"]) - int(S["valid_weekends"])} exclusões, nenhuma por ser extrema.')}
   {card(2, 'Horas comuns', [(num(S['valid_hours'], 0), 'horas válidas', '')], 'Ouro e token negociando ao mesmo tempo.')}
   {card(3, 'Pregões', [(num(D['plac']['dias_uteis'], 0), 'dias da NYSE', '')], 'Média das 15h às 20h UTC de cada dia.')}
   {card(4, 'Ouro × GLD', [(num(D['gld']['median_abs_level_difference_bps']), 'bps de diferença', 'g')], f"Em {num(D['gld']['n_dates'], 0)} dias, às 16h de NY.")}
   {card(5, 'Bitfinex × Coinbase', [(num(S['fx_source_median_abs_difference_bps']), 'bps no USDT/USD', 'g')], f'{num(S["fx_source_comparison_hours"], 0)} horas em comum.')}
   {card(6, 'Binance × Kraken', [(num(F['kx_diff'], 0), 'bps de diferença', 'g')], f'{len(D["kx"])} horas nos dias mais extremos.')}
  </div>
 </div>
</div>
<div class="h" style="margin-top:34px">Anatomia de uma observação · 04/03/2024, 16h UTC</div>
<div class="rail">{rail}</div>"""
    pages.append(page(3, 'Como medimos o desvio entre o PAXG e o ouro', body, total=T, kicker='Método / Dados e medida', theme='light roomy big',
                      source='Binance, Bitfinex, Coinbase, Dukascopy, Kraken e SPDR. Janela: 28/08/2020 12:00 a 08/11/2026 00:00 UTC. Preço de hora = último negócio, sem livro de ofertas.'))

    # ---------------- 04 · dois ritmos
    fig2_html = fig(fig_annual(D['annual']), 2, 'Horas a até 25 bps do ouro, por ano', '* 2020 a partir de 28/ago; 2026 até 8/nov.')
    onchain_html = ''
    if D.get('t18j') is not None:
        oc = D['t18j']['testes'][0]
        corr, prem, disc = oc['corr_desvio_t_emissao_t1_t4'], oc['emissao_prox_4s_media_pct_quando_premio_25'], oc['emissao_prox_4s_media_pct_quando_desconto_25']
        fig2_html = fig(fig_onchain(D['t18']), 2, 'Emissão do PAXG depois de semanas com prêmio ou desconto',
                        f"Eventos de emissão e resgate no Ethereum ({D['t18j']['emissoes']} e {D['t18j']['resgates']}, via Blockscout), em % da oferta. Linha: ajuste linear.")
        if corr > 0.1 and prem > disc:
            leitura = (f'Nos dados on-chain, a oferta cresce depois de semanas com prêmio ({num(prem, 1, True)}% em 4 semanas) mais do que depois de desconto '
                       f'({num(disc, 1, True)}%); correlação de {num(corr, 2)}. A emissão reage ao desvio, mas devagar, o que combina com o atrito.')
        elif abs(corr) <= 0.1:
            leitura = (f'Nos dados on-chain, a emissão quase não responde ao desvio (correlação de {num(corr, 2)} com as 4 semanas seguintes), '
                       'o que combina com um canal de arbitragem fraco.')
        else:
            leitura = (f'Nos dados on-chain, a emissão anda no sentido oposto ao esperado (correlação de {num(corr, 2)}); a emissão em lotes '
                       'para a tesouraria pode explicar isso.')
        onchain_html = f'<p style="margin-top:8px">{leitura} É associação, não causa.</p>'
    body = f"""
<div class="grid" style="grid-template-columns:1.62fr 1fr;gap:30px">
 <div>
  {fig(fig_level(D['serie'], F['kx_ext']), 1, 'O desvio tem um nível que muda devagar e um ruído que some em dias',
       'Cinza: média diária do desvio nas horas de pregão da NYSE. Verde: nível estimado pelo modelo de dois componentes. Faixa dourada: ±25 bps.')}
 </div>
 <div>
  <div class="h">O que o gráfico mostra</div>
  <p>Se o PAXG fosse um espelho do ouro, a linha cinza ficaria colada no zero. Em vez disso, há prêmio em 2020 e 2021, desconto de meados de 2022 a meados de 2024 e prêmio de novo em 2025. O nível do mês explica <b>{pct(R['variance_share_monthly_level'])}</b> da variação hora a hora.</p>
  <p>Separamos os dois ritmos com um modelo de componentes não observados (Harvey, 1989) e uma regressão de correção de erro do retorno diário do PAXG contra o do ouro.</p>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:12px;margin-top:12px">
   {card(1, 'Dois ritmos', [(num(t15['meia_vida_transitorio_pregoes']), 'pregões de meia-vida', 'g'), (num(t15['dp_choque_nivel_bps_ano'], 0), 'bps/ano no nível', 'o')], 'O ruído some em dias; o nível acumula choques ao longo do ano.')}
   {card(2, 'Segue o ouro no dia', [(pct(t16['coef']['ret_ouro']), 'do retorno do ouro', 'g'), (pct(t16['correcao_diaria']), 'do desvio por dia', 'g')], f'Correção de erro com R² de {num(t16["r2"], 2)}.')}
  </div>
 </div>
</div>
<div class="grid" style="grid-template-columns:1fr 1.1fr 1.1fr;gap:30px;margin-top:14px">
 <div>{fig2_html}</div>
 <div>
  <div class="h">De onde vem o nível</div>
  <p>O retorno do ouro explica só {pct(t16['semanal_var_desvio_em_ret_ouro']['r2'])} da variação semanal do desvio, então o nível não vem de atraso em relação ao ouro. Ele se move por fatores do próprio mercado do token, que não testamos. Desvios assim persistem quando arbitrar custa caro (Shleifer e Vishny, 1997; Makarov e Schoar, 2020): resgatar PAXG na Paxos custa de 0,125% a 0,5% e exige conta aprovada.</p>{onchain_html}
 </div>
 <div>
  <div class="h">Está melhorando?</div>
  <p>Em 2026, {pct(F['y26'].within_25_bps)} das horas ficaram a até 25 bps do ouro, contra {pct(F['y20'].within_25_bps)} em 2020, e o volume diário cresceu cerca de dez vezes desde 2023. A tendência trimestral ainda não é firme (intervalo de {num(D['t4'].beta_lo, 2)} a {num(D['t4'].beta_hi, 2)} por ano).</p>
  <div class="call" style="margin-top:12px"><p>O ruído é pequeno demais para pagar uma arbitragem; o dinheiro está nas viradas do nível.</p></div>
 </div>
</div>"""
    pages.append(page(4, 'O desvio tem dois ritmos: um nível que dura meses e um ruído que some em dias', body, total=T, kicker='Evidência / O desvio e seu modelo', theme='light big',
                      source='Binance, Bitfinex e Dukascopy; Kraken nos extremos. Decomposição e correção de erro posteriores à análise original.'))

    # ---------------- 05 · fim de semana
    t13 = D['t13'].set_index('periodo')
    p1 = D['pair'].loc['b_0_to_b_1h']
    fc = D['fc']
    body = f"""
<div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:30px">
 <div>
  <div class="h">O token encarece</div>
  <p>O ouro fecha na sexta à tarde e reabre no domingo à noite; o PAXG continua negociando. Nos {int(S['valid_weekends'])} fins de semana, o token sai em média {num(t13r['premio_fds_media_bps'], 1)} bps mais caro do que entrou, em relação ao ouro (mediana de {num(t13r['premio_fds_mediana_bps'], 1)}, IC 90% de {num(t13r['premio_fds_mediana_ic90'][0], 1)} a {num(t13r['premio_fds_mediana_ic90'][1], 1)}). Parte disso some nas primeiras horas.</p>
  {fig(fig_weekend(t13r), 3, 'O token sai do fim de semana mais caro e devolve parte disso', 'Variação média do desvio com sinal desde o fechamento de sexta, em bps. Não é o |desvio| do cartão ao lado.')}
 </div>
 <div>
  <div class="h">O PAXG antecipa o ouro?</div>
  <p>Se o preço do token no domingo carregasse informação, ele preveria o salto do ouro na reabertura. No período todo, o R² é só {num(t13.loc['todos', 'r2'], 2)}: o token se mexe demais no fim de semana. Em 2026 o R² sobe para {num(t13.loc['2026', 'r2'], 2)}, no ano do perpétuo de ouro da Binance e do ouro de fim de semana da CME; não identificamos a causa.</p>
  {fig(fig_r2(D['t13']), 4, 'Em 2026 o fim de semana do PAXG passou a explicar o salto do ouro', 'R² da regressão do salto de reabertura do ouro no movimento do PAXG, por ano.')}
 </div>
 <div>
  <div class="h">A reabertura herda a sexta</div>
  <div class="grid" style="grid-template-columns:1fr;gap:14px">
   {card(1, 'O desvio de sexta volta', [(pct(t13r['r2_reabertura_em_sexta']), 'R², sexta → reabertura', 'g'), (pct(t13r['mesmo_sinal_sexta_reabertura']), 'com o mesmo sinal', 'g')], f'Sete horas depois, a parcela explicada chega a {pct(t13r["r2_7h_em_sexta"])}: o ruído da reabertura se dissipa e o desvio volta para perto do nível de sexta.')}
   {card(2, 'Cai, mas não zera', [(f"{num(S['reopen_median_abs_bps'], 0)} → {num(S['one_hour_median_abs_bps'], 0)}", 'bps, mediana absoluta', ''), (num(p1.mean_abs_change_bps, 1), 'mudança média do |desvio| em 1 h', 'g')], f'Prever o desvio de +7 h repetindo o último valor erra {num(fc.loc["persistence", "mae_bps"], 1)} bps; um modelo linear erra {num(fc.loc["linear_adjustment", "mae_bps"], 1)}.')}
  </div>
  <div class="call" style="margin-top:16px"><p>O desvio da reabertura é, em boa parte, o nível que já estava lá na sexta.</p></div>
 </div>
</div>"""
    pages.append(page(5, 'No fim de semana o token encarece, e a reabertura herda o desvio de sexta', body, total=T, kicker='Evidência / Fim de semana e reabertura', theme='light roomy big',
                      source='301 fins de semana válidos de 323. Intervalos por blocos de semanas; regressões com erro HC1. Detalhe por ano no material suplementar.'))

    # ---------------- 06 · arbitragem em horas (carvão)
    rail = ''.join([
        step(1, 'Sinal', 'Uma hora depois da reabertura, se o desvio passa de 10 bps, apostamos na volta ao ouro.', 'sinal em +1 h'),
        step(2, 'Entrada', 'No minuto seguinte, compramos o lado barato e vendemos o caro: token contra ouro.', 'preços de minuto'),
        step(3, 'Tamanho', 'Uma unidade em cada perna, sem alavancagem e sem escolher semanas boas.', '1 onça × 1 onça'),
        step(4, 'Saída', 'Seis horas depois da entrada, desfazemos as duas pernas.', 'saída em 6 h'),
        step(5, 'Resultado', f'Média de {F["n_eval"]} operações no cenário intermediário de custos.', f'{num(gross, 1, True)} − {num(mid_cost, 1)} = {num(mid_net, 1)} bps')])
    budget = D['budget'].set_index('horizon_hours')
    body = f"""
<div class="h">Anatomia de uma operação de convergência</div>
<div class="rail">{rail}</div>
<div class="grid" style="grid-template-columns:1fr 1.05fr 1.1fr;gap:30px;margin-top:24px">
 <div>{fig(fig_waterfall(gross, mid_cost, mid_net), 5, 'O custo fica com a maior parte da diferença', 'Média por operação: taxa do token de 5 bps por execução, spread de 2, ouro 1, câmbio 2 e deslizamento 2.')}</div>
 <div>
  <div class="h">Por que não paga</div>
  <p>Em 6 horas, só o ruído rápido tem tempo de fechar; o nível quase não se mexe. O ganho bruto médio fica em {num(gross)} bps (intervalo de {num(budget.loc[6, 'gross_lo'], 1)} a {num(budget.loc[6, 'gross_hi'], 1)}). Nenhum dos três cenários de custo da grade original deixa a média positiva:</p>
  <table style="margin-top:8px"><thead><tr><th>Cenário</th><th class="n">Saldo médio</th><th class="n">Positivas</th></tr></thead><tbody>
   <tr><td>Original (taxa 10, spread 10)</td><td class="n">{num(orig.mean_model_bps, 1)}</td><td class="n">{F['orig_pos']} de {F['n_eval']}</td></tr>
   <tr class="hl"><td>Intermediário (taxa 5, spread 2)</td><td class="n">{num(mid_net, 1)}</td><td class="n">{F['mid_pos']} de {F['n_eval']}</td></tr>
   <tr><td>Mínimo da grade</td><td class="n">{num(low.mean_model_bps, 1)}</td><td class="n">—</td></tr></tbody></table>
  <p style="margin-top:8px">Nas <b>{num(F['n_grid'], 0)}</b> combinações de custo e prazo (1, 6 e 24 h), nenhuma média ficou positiva.</p>
 </div>
 <div>
  <div class="h neg">Onde essa operação perde</div>
  <div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:16px">
   {risk('risco 1', 'O bruto é pequeno', num(gross, 1, True), 'bps em 6 h', f'Menor que o custo mínimo da grade, de {num(gross - float(low.mean_model_bps), 1)} bps.')}
   {risk('risco 2', 'Vender token exige empréstimo', 'não verificado', 'acesso e custo', 'Sem empréstimo de PAXG documentado, o saldo pode ser pior.')}
   {risk('risco 3', 'Limiar dos sinais faltantes', f"{num(F['tip_mid'], 1)} bps", 'média necessária', f'{int(S["signals_unassessed"])} sinais não tinham saída observável; este é um limiar, não uma estimativa.')}
  </div>
  <div class="call" style="margin-top:18px"><p>Quem consegue esperar as viradas do nível, sem vender nada a descoberto? Os dois próximos slides respondem.</p></div>
 </div>
</div>"""
    pages.append(page(6, f'Arbitragem na reabertura: o ganho bruto de {num(gross)} bps não cobre os custos', body, total=T, kicker='Evidência / Arbitragem na reabertura', theme='dark roomy big',
                      source='Preços de minuto da Binance, Bitfinex e Dukascopy; 44 operações em 104 semanas. Cenário intermediário escolhido depois dos resultados; o original foi fixado antes.'))

    # ---------------- 07 · rotação: regra e resultado
    cs = float(prim.custo_ciclo_bps) / 2
    alw = rot[(rot.config == 'sempre PAXG') & (rot.cenario_custos == 'intermediario')].iloc[0]
    rail = ''.join([
        step(1, 'Quem', 'Investidor em dólares que já quer ouro e tem GLDM e PAXG à mão. Não vende a descoberto.', 'sempre 100% em ouro'),
        step(2, 'Sinal', 'Média do desvio das 15h às 20h UTC, quando ETF e token negociam juntos.', 'um número por pregão'),
        step(3, 'Regra', f'Vai para o PAXG se o desvio ≤ −{k}; volta ao GLDM se ≥ +{k}. Faixa = custo de um ciclo.', f'faixa = ±{k} bps'),
        step(4, 'Execução', 'No pregão seguinte, ao desvio médio daquele dia; o sinal nunca vê esse preço.', 'atraso de 1 pregão'),
        step(5, 'Custo', 'Token 5, meio spread 1, câmbio 1, deslizamento 2 e meio spread do ETF 0,5.', f'{num(cs, 1)} bps por troca')])
    body = f"""
<div class="h">Anatomia da rotação</div>
<div class="rail">{rail}</div>
<div class="grid" style="grid-template-columns:1.35fr 1fr;gap:30px;margin-top:22px">
 <div>{fig(fig_rotation(D['curve'], k), 6, 'A rotação ganha nas viradas de desconto para prêmio', f'Acima: ganho acumulado contra manter o GLDM o tempo todo. Abaixo: desvio diário e faixa de ±{k} bps. Fundo verde: carteira em PAXG.')}</div>
 <div>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:14px">
   {card(1, 'Ganho contra o GLDM', [(num(prim.ganho_anual_vs_gldm_bps, 0, True), 'bps por ano', 'g')], f'IC 90% de {num(prim.ic90_lo, 0)} a {num(prim.ic90_hi, 0)}, bootstrap em blocos de 6 meses.')}
   {card(2, 'Ciclos', [(f'{int(prim.ciclos)}', f'{pct(prim.ciclos_positivos)} positivos', '')], f'Todos os anos com operação foram positivos, de {num(min(v for v in yr.values() if v), 0, True)} a {num(max(yr.values()), 0, True)} bps.')}
   {card(3, 'De onde vem', [(pct(F['share_week']), 'de ciclos com mais de 1 semana', 'o')], 'O ganho vem das viradas do nível, não do ruído de poucos dias.')}
   {card(4, 'Sem a regra', [(num(alw.ganho_anual_vs_gldm_bps, 0), 'bps/ano: sempre PAXG', 'r')], 'Ficar no token o tempo todo não captura nada.')}
  </div>
  <div class="call" style="margin-top:14px"><p>A rotação ganha onde a arbitragem perde por dois motivos: não tem prazo para sair, então espera o desvio atravessar a faixa, e cada troca custa {num(cs, 1)} bps, sem perna de ouro nem empréstimo.</p></div>
 </div>
</div>"""
    pages.append(page(7, 'Rotação GLDM ↔ PAXG: quem já tem ouro captura o desvio sem vender a descoberto', body, total=T, kicker='Evidência / Rotação entre veículos', theme='light roomy big',
                      source='1.552 pregões da NYSE, 28/08/2020 a 06/11/2026; feriados da NYSE excluídos. Regra definida depois da análise original.'))

    # ---------------- 08 · rotação: robustez (v2: XAUT e regimes)
    r_lag2 = rot_row(rot, f'faixa fixa ±{k}', 'intermediario', 2)
    r30 = rot_row(rot, 'faixa fixa ±30', 'intermediario', 1)
    ko = int(prim_o.k_bps)
    mv_i = rot_row(rot, 'nível móvel 60d ±30', 'intermediario', 1)
    mv_o = rot_row(rot, 'nível móvel 60d ±30', 'original', 1)
    x17 = D['x17']
    xa = x17[(x17.par == 'XAUT/USD') & (x17.min_barras == 4) & (x17.cenario_custos == 'intermediario') & (x17.lag_pregoes == 1)].iloc[0]
    xo = x17[(x17.par == 'XAUT/USD') & (x17.min_barras == 4) & (x17.cenario_custos == 'original') & (x17.lag_pregoes == 1)].iloc[0]
    xu = x17[(x17.par == 'XAUT/UST') & (x17.min_barras == 4) & (x17.cenario_custos == 'intermediario') & (x17.lag_pregoes == 1)].iloc[0]
    r19 = D['r19']
    hm = r19[(r19.regra == 'hmm_filtrado') & (r19.cenario_custos == 'intermediario') & (r19.lag_pregoes == 1)].iloc[0]
    hb = r19[(r19.regra == 'faixa_fixa') & (r19.cenario_custos == 'intermediario') & (r19.lag_pregoes == 1)].iloc[0]
    jx = D['x17j']
    ini = D['r19j']['inicio_regra']

    def row(name, r, cls=''):
        return (f'<tr class="{cls}"><td>{name}</td><td class="n">{int(r.ciclos)}</td><td class="n">{pct(r.ciclos_positivos)}</td>'
                f'<td class="n">{num(r.ganho_anual_vs_gldm_bps, 0, True)}</td><td class="n">[{num(r.ic90_lo, 0)}; {num(r.ic90_hi, 0)}]</td></tr>')
    table = ''.join([row(f'PAXG, principal: ±{k}, custos intermediários', prim, 'hl'), row('PAXG, execução 2 pregões depois', r_lag2), row('PAXG, faixa de ±30 bps', r30),
                     row(f'PAXG, custos originais (±{ko})', prim_o), row('PAXG, faixa em torno do nível dos 60 pregões', mv_i), row('Idem, custos originais', mv_o),
                     row(f'PAXG, regimes de Markov (desde {ini[5:7]}/{ini[:4]})', hm),
                     row('XAUT, mesma regra (±19), Bitfinex', xa, 'hl'), row(f'XAUT, custos originais (±{int(xo.k_bps)})', xo), row('XAUT via USDT (checagem)', xu)])
    placebo_x = num(jx['fracao_placebos_acima'] * 1000, 0)
    body = f"""
<div class="grid" style="grid-template-columns:1.18fr 1fr;gap:34px">
 <div>
  <div class="h">O que pode estar errado, e o que testamos</div>
  <p>A regra foi desenhada depois da análise original. Por isso a faixa não é estimada (é o custo de um ciclo) e o resultado foi refeito com custos maiores, atraso, outras regras e, como teste fora da amostra, em outro token de ouro, o XAUT, sem mudar nada.</p>
  <table class="tight" style="margin-top:10px"><thead><tr><th>Configuração</th><th class="n">Ciclos</th><th class="n">Pos.</th><th class="n">bps/ano</th><th class="n">IC 90%</th></tr></thead><tbody>{table}</tbody></table>
  <p class="small" style="margin-top:6px">Regimes: Markov com 3 estados, reestimado todo mês só com o passado; no mesmo período, a faixa de ±19 rendeu {num(hb.ganho_anual_vs_gldm_bps, 0, True)}. A regra principal não é a melhor da grade (±30 rendeu mais). Tabelas completas no suplementar.</p>
 </div>
 <div>
  {fig(fig_xaut_vs_paxg(D['curve'], D['x17c']), 7, 'A mesma regra também ganha no XAUT, sem nenhum ajuste',
       f"XAUT/USD da Bitfinex, {num(jx['dias_validos'], 0)} pregões. O desvio do XAUT é menor (mediana de {num(jx['desvio_mediano_abs_bps'], 0)} bps) e pouco ligado ao do PAXG (correlação de {num(jx['correlacao_diaria_com_paxg'], 2)}). Teste entre ativos, no mesmo período.")}
  <p style="margin-top:10px"><b>Placebo:</b> com o mesmo número de ciclos em datas sorteadas, 0 de 1.000 carteiras chegaram ao resultado no PAXG e {placebo_x} de 1.000 no XAUT.</p>
 </div>
</div>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:30px;margin-top:14px">
 {risk('risco 1', 'O desconto pode piorar com a carteira dentro', num(prim.pior_queda_bps, 0), 'bps contra o GLDM em mar/2024', 'O PAXG chegou a 3% abaixo do ouro; a Kraken mostrou o mesmo desconto.')}
 {risk('risco 2', 'Capacidade pequena', f'US$ {num(cap["2023"] / 1e3, 0)} mil a {num(cap["2026"] / 1e3, 0)} mil', 'por pregão, 5% do volume', 'Serve para carteiras pequenas; o volume de 2026 é dez vezes o de 2023.')}
 {risk('risco 3', 'Impostos e custódia', 'fora do cálculo', 'resultado antes de IR', 'Cada troca realiza ganho de capital, e o token exige custódia.')}
</div>"""
    pages.append(page(8, 'O resultado da rotação resiste a custos, atraso, outra regra e outro token de ouro', body, total=T, kicker='Evidência / Robustez da rotação', theme='light roomy big',
                      source='T12 (PAXG), results/v2/T17 (XAUT) e T19 (regimes). IC por bootstrap circular em blocos de 6 meses. Regras do XAUT e dos regimes pré-registradas antes do download.'))

    # ---------------- 09 · quem só carrega
    body = f"""
<div class="grid" style="grid-template-columns:1fr 1fr 1.1fr;gap:30px">
 <div>
  <div class="h">Quanto custa carregar</div>
  <p>O PAXG custa mais para entrar e sair ({num(F['rt_mid'], 0)} bps, contra 1 bp no ETF), mas não cobra taxa anual; o GLD cobra 0,40% ao ano e o GLDM, 0,10%. A taxa do ETF alcança o custo de entrada do token em <b>{num(F['gld_m'])} meses</b> (GLD) e <b>{num(F['gldm_m'])} meses</b> (GLDM). Com os custos originais, seriam {num(F['gld_o'])} e {num(F['gldm_o'])} meses.</p>
  {fig(fig_costs(F['rt_mid'], 1.0, F['gld_m'], F['gldm_m']), 8, 'Em custo, o token só compensa para quem fica', 'Custo acumulado em dólares, antes de impostos.')}
 </div>
 <div>
  <div class="h neg">O risco que a taxa não mostra</div>
  <p>A conta de taxas supõe que o PAXG vale o ouro na compra e na venda. Quem compra com prêmio e vende com desconto perde a diferença. Em 12 meses, a variação do desvio tem desvio-padrão de <b class="r">{num(r12.desvio_padrao_bps, 0)} bps</b>, {num(r12.desvio_padrao_bps / 10, 0)} vezes a taxa do GLDM e duas vezes a do GLD.</p>
  {fig(fig_basis_risk(D['t14']), 9, 'O risco de base é maior que a economia de taxa', 'Desvio-padrão da variação do desvio, por horizonte, contra a taxa de cada ETF, em bps.')}
 </div>
 <div>
  <div class="h">O que os números sugerem para cada perfil</div>
  <table class="airy"><tbody>
   <tr><td><b>Fica poucos meses</b></td><td>O ETF sai mais barato até {num(F['gld_m'])} meses (GLD) ou {num(F['gldm_m'])} (GLDM).</td></tr>
   <tr><td><b>Fica anos sem mexer</b></td><td>O token economiza de 10 a 40 bps por ano, mas assume um desvio que varia {num(r12.desvio_padrao_bps, 0)} bps em um ano.</td></tr>
   <tr><td><b>Pode trocar de veículo</b></td><td>A rotação rendeu {num(prim.ganho_anual_vs_gldm_bps, 0, True)} bps por ano contra o GLDM, antes de impostos.</td></tr>
   <tr><td><b>Negocia no fim de semana</b></td><td>Só o token negocia, com prêmio médio de {num(t13r['premio_fds_media_bps'], 0)} bps na reabertura.</td></tr>
   <tr><td><b>Emissor e corretoras</b></td><td>O atrito está no nível. Resgate mais barato e com menos exigências tende a estreitar a faixa; em 2026, com mais volume, o desvio ficou menor.</td></tr></tbody></table>
  <div class="call" style="margin-top:14px"><p><b>Brasil.</b> Não medimos câmbio em reais, IOF, imposto de renda nem o acesso local a GLD e GLDM; é o próximo passo.</p></div>
 </div>
</div>"""
    pages.append(page(9, 'Para quem só carrega ouro, a economia de taxa é menor que o risco de base', body, total=T, kicker='Implicações / Token ou ETF', theme='light roomy big',
                      source='SPDR (taxas e spreads atuais de GLD e GLDM); custos do token supostos (cenário intermediário). Valores em dólares, antes de impostos.'))

    # ---------------- 10 · conclusão
    body = f"""
<div class="band"><div class="lab">A resposta</div><p>O PAXG acompanha o ouro dia a dia, mas o desvio que sobra se comporta como um nível que muda devagar e dura meses. Por isso a arbitragem na reabertura do fim de semana, com saída em até 24 h, não paga, enquanto quem já quer ouro captura esse nível trocando de GLDM para PAXG no desconto e voltando no prêmio. Para quem só carrega o token, o mesmo nível é um risco maior que a economia de taxa.</p></div>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:34px;margin-top:24px">
 <div class="ans"><div class="q">01 · Quanto se afasta?</div><h3>O token segue {pct(t16['coef']['ret_ouro'])} do retorno diário do ouro, mas carrega um nível que variou de {num(F['lvl_min'], 0)} a {num(F['lvl_max'], 0, True)} bps.</h3><strong>{pct(R['variance_share_monthly_level'])}</strong><small>da variação horária vem do nível do mês</small></div>
 <div class="ans"><div class="q">02 · Quem ganha com o desvio?</div><h3>A arbitragem na reabertura perde {num(-mid_net, 0)} bps por operação; a rotação, para quem já tem ouro, ganha, e a mesma regra também ganha no XAUT.</h3><strong>{num(prim.ganho_anual_vs_gldm_bps, 0, True)} bps/ano</strong><small>PAXG contra o GLDM (IC 90% de {num(prim.ic90_lo, 0)} a {num(prim.ic90_hi, 0)}); XAUT: {num(D['x17j']['ganho_anual_bps'], 0, True)}</small></div>
 <div class="ans"><div class="q">03 · Token ou ETF?</div><h3>Em custo, o token compensa após {num(F['gld_m'])} meses (GLD) ou {num(F['gldm_m'])} (GLDM), mas o desvio de 12 meses pesa mais.</h3><strong>{num(r12.desvio_padrao_bps, 0)} bps</strong><small>de desvio-padrão em 12 meses</small></div>
</div>
<div class="grid" style="grid-template-columns:1.25fr 1fr;gap:40px;margin-top:26px">
 <div>
  <div class="h">O que isso implica</div>
  <p><b>Para quem investe:</b> olhar o desvio do dia antes de escolher entre token e ETF. <b>Para corretoras e emissor:</b> o atrito está no nível; resgate mais barato tende a estreitar a faixa, e em 2026, com mais volume, {pct(F['y26'].within_25_bps)} das horas ficaram a até 25 bps do ouro. <b>Para quem avalia ouro tokenizado:</b> medir o nível do desvio, além da correlação.</p>
 </div>
 <div>
  <div class="h neg">Limites e próximos passos</div>
  <p class="small">Custos do token supostos; cenário intermediário e regra de rotação definidos depois da análise original, sem teste em dados novos; impostos e custódia fora do saldo. Próximos passos: acompanhar a regra daqui para frente sem mudá-la, incluir o XAUT e levar a conta para reais.</p>
 </div>
</div>"""
    pages.append(page(10, 'Conclusão: o PAXG acompanha o ouro, mas carrega um nível de desvio que a arbitragem na reabertura não fecha', body, total=T, kicker='Conclusão', theme='light roomy big',
                      source='Equipe BitFlow: Gabriel Navarro, Lorenzo Cavalcante e Rodrigo Menin. Referências, fontes e tabelas completas no material suplementar.'))
    return pages
