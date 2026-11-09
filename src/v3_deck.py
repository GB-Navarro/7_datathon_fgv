"""Entrega v3: 10 slides com metodologia em fluxograma, HMM nos slides e layout inspirado no PDF de referência da equipe.

Uso: python -m src.v3_deck
Saídas: slides/entrega_v3.html/.pdf, slides/entrega_v3_suplementar.pdf (cópia da v2), results/v3/QA_presentation_v3.json.
Não altera v1 nem v2: as cores dos gráficos são trocadas só na memória deste processo.
"""
from __future__ import annotations

import html
import shutil

import re
import numpy as np
import pandas as pd

from . import report_v5 as R5
from .common import ROOT, dump_json, utc_now

# ---------------------------------------------------------------- paleta do layout de referência (só neste processo)
INK, RED, BLUE, SAND, MUTED, CREAM, PANEL = '#1C1A17', '#B23A1E', '#2E6AA3', '#BDB394', '#6B6457', '#ECE3CF', '#F4ECDB'
OCHRE = '#A8862C'
R5.PAXG, R5.OURO, R5.CUSTO, R5.NEUTRO, R5.GRID, R5.INK, R5.MUTED = RED, OCHRE, INK, SAND, '#D9CFB8', INK, MUTED
R5.OURO_L, R5.PAXG_L, R5.PANEL = '#E9DDBA', '#F0D5CB', PANEL
R5.HALO = f'stroke="{PANEL}" stroke-width="4" paint-order="stroke"'

from .v2_figs import fig_xaut_vs_paxg  # noqa: E402  (importado depois da troca de cores)
from .v2_report_pages import facts, load, rot_row  # noqa: E402
from .report_v5 import (fig_basis_risk, fig_costs, fig_level, fig_placebo, fig_rotation, fig_waterfall, fig_weekend, num, pct, svg, tx)  # noqa: E402

T = 10


# ---------------------------------------------------------------- figura nova: regimes do HMM


def shift_label(svg_html, prefix, dy):
    """Desce um rótulo de texto do SVG para não ficar sobre a linha."""
    def f(m):
        return f'{m.group(1)}{float(m.group(2)) + dy:.1f}{m.group(3)}'
    return re.sub(r'(<text x="[^"]+" y=")([-0-9.]+)("[^>]*>' + re.escape(prefix) + ')', f, svg_html, count=1)

def fig_hmm(serie, probs):
    s = serie.copy()
    s['dia'] = pd.to_datetime(s.dia)
    p = probs.copy()
    p['dia'] = pd.to_datetime(p.dia)
    m = s.merge(p, on='dia', how='left')
    w, h = 940, 262
    l, r, top, ph = 58, 14, 28, 196
    t0, t1 = m.dia.min(), m.dia.max()
    x = lambda ts: l + (pd.Timestamp(ts) - t0).days / (t1 - t0).days * (w - l - r)
    lo, hi = -320, 200
    y = lambda v: top + (hi - max(lo, min(hi, v))) / (hi - lo) * ph
    out = []
    reg = np.where(m.p_desconto > .5, 'd', np.where(m.p_premio > .5, 'p', np.where(m.p_neutro > .5, 'n', '')))
    start = None
    for i in range(len(m) + 1):
        cur = reg[i] if i < len(m) else ''
        prev = reg[i - 1] if i > 0 else ''
        if i == 0 or cur != prev:
            if start is not None and prev in ('d', 'p'):
                col = '#F0D5CB' if prev == 'd' else '#D6E3F0'
                out.append(f'<rect x="{x(m.dia[start]):.1f}" y="{top}" width="{max(1, x(m.dia[i - 1]) - x(m.dia[start])):.1f}" height="{ph}" fill="{col}"/>')
            start = i
    for v in [-300, -150, 0, 150]:
        out.append(f'<path d="M{l} {y(v):.1f}H{w - r}" stroke="{INK if v == 0 else "#D9CFB8"}"/>' + tx(l - 8, y(v) + 4, num(v, 0, True) if v else '0', 12, MUTED, 'end'))
    pts = ' '.join(f'{x(a):.1f},{y(v):.1f}' for a, v in zip(m.dia, m.desvio_bps))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="1"/>')
    first = m.dia[m.p_desconto.notna()].min()
    out.append(f'<path d="M{x(first):.1f} {top}V{top + ph}" stroke="{RED}" stroke-width="1.5" stroke-dasharray="4 4"/>')
    out.append(tx(x(first) - 6, top - 9, 'antes: só treino (500 pregões)', 12, MUTED, 'end', 600, R5.HALO))
    out.append(tx(x(first) + 6, top - 9, 'depois: probabilidade filtrada, reestimada todo mês', 12, INK, 'start', 600, R5.HALO))
    for yr in range(t0.year + 1, t1.year + 1):
        out.append(tx(x(pd.Timestamp(f'{yr}-01-01')), top + ph + 18, yr, 12, MUTED, 'middle'))
    return svg(w, h, 'Desvio diário e regimes de desconto e prêmio segundo o modelo de Markov filtrado.', ''.join(out))


# ---------------------------------------------------------------- moldura

CSS = """
@font-face{font-family:Slab;src:url("design-systems/assets/fonts/AlfaSlabOne-Regular.ttf")}
@font-face{font-family:Manrope;src:url("design-systems/assets/fonts/Manrope.ttf");font-weight:200 800}
@font-face{font-family:PlexMono;src:url("design-systems/assets/fonts/IBMPlexMono-Regular.ttf")}
@page{size:1600px 900px;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html{background:#8f887a}
body{font-family:Manrope,Arial,sans-serif;font-variant-ligatures:none;font-feature-settings:"liga" 0,"calt" 0,"dlig" 0;color:#1C1A17;font-size:15px;line-height:1.45;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page,.cover{width:1600px;height:900px;position:relative;overflow:hidden;margin:20px auto;page-break-after:always;break-after:page;
 background:#ECE3CF radial-gradient(circle at 20% 10%,rgba(255,255,255,.35),transparent 55%)}
.page{padding:40px 106px 0}
@media print{html{background:none}.page,.cover{margin:0}}
.hd{display:flex;justify-content:space-between;align-items:center;font-family:PlexMono,monospace;font-size:15px;letter-spacing:.18em;text-transform:uppercase;color:#B23A1E;padding-bottom:12px;border-bottom:4px solid #1C1A17}
.hd .no{color:#1C1A17;letter-spacing:.05em}
h1{font-family:Slab,serif;font-weight:400;font-size:40px;line-height:1.08;margin:22px 0 16px;letter-spacing:-.005em}
.lab{font-family:PlexMono,monospace;font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#B23A1E;margin-bottom:6px}
p{font-size:15px}p+p{margin-top:7px}
b{font-weight:800}
.r{color:#B23A1E}.bl{color:#2E6AA3}
.grid{display:grid;gap:22px}
.box{background:#F4ECDB;border:2px solid #1C1A17;padding:14px 16px}
.box.flat{border:none;background:transparent;padding:0}
.dark{background:#1E1B18;color:#F2EADB;padding:16px 18px;box-shadow:9px 9px 0 #B23A1E}
.dark .lab{color:#E07A5F}
.redbar{border-left:5px solid #B23A1E;padding:2px 0 2px 16px}
.big{font-family:Slab,serif;color:#B23A1E;font-size:40px;line-height:1}
.strip{display:grid;grid-template-columns:repeat(5,1fr);border-top:3px solid #1C1A17;border-bottom:3px solid #1C1A17}
.strip div{padding:8px 14px;border-left:2px solid #1C1A17}.strip div:first-child{border-left:none}
.strip strong{display:block;font-family:Slab,serif;font-weight:400;font-size:38px;color:#B23A1E;line-height:1.05}
.strip span{font-size:14px}
.figt{font-weight:800;font-size:15px;margin-bottom:6px}
.fig{background:#F4ECDB;border:2px solid #1C1A17;padding:8px 10px 4px}
.note{font-size:12.5px;color:#6B6457;line-height:1.38}
table{border-collapse:collapse;width:100%;font-size:14px}
th{text-align:left;background:#1C1A17;color:#F2EADB;font-weight:700;padding:7px 9px}
td{padding:6px 9px;border-bottom:1px solid #B9AE93}
td.n,th.n{text-align:right;font-family:PlexMono,monospace;white-space:nowrap}
tr.hl td{background:#E4D6B6;font-weight:800}
.ft{position:absolute;left:106px;right:106px;bottom:18px;font-size:12.5px;color:#6B6457}
.hyp{border:2px solid #1C1A17;background:#F4ECDB;padding:10px 14px}
.hyp b.t{color:#B23A1E}
.hyp p{font-size:14.5px}.hyp .tt{font-size:13px;color:#6B6457;margin-top:4px}
.flow{display:grid;align-items:stretch;gap:0}
.fnode{border:2px solid #1C1A17;background:#F4ECDB;padding:10px 12px}
.fnode.red{background:#B23A1E;color:#F7EFE0;border-color:#B23A1E}
.fnode.dk{background:#1E1B18;color:#F2EADB}
.fnode h4{font-size:15px;font-weight:800;margin-bottom:3px}
.fnode p{font-size:13.2px;line-height:1.38}
.fnode .m{font-family:PlexMono,monospace;font-size:12.5px}
.arr{display:flex;align-items:center;justify-content:center;font-size:26px;color:#B23A1E;font-weight:800}
.down{text-align:center;font-size:26px;color:#B23A1E;font-weight:800;line-height:1.1;margin:4px 0}
.eq{font-family:PlexMono,monospace;font-size:13px;background:#E9DFC6;padding:6px 8px;margin:6px 0;border-left:3px solid #1C1A17}
.risk{border-top:3px solid #1C1A17;padding-top:8px}
.risk .k{font-family:PlexMono,monospace;font-size:12px;color:#B23A1E;letter-spacing:.1em;text-transform:uppercase}
.risk strong{display:block;font-family:Slab,serif;font-weight:400;font-size:26px;color:#B23A1E;line-height:1.1}
.risk p{font-size:13.5px}
.read{border-top:3px solid #1C1A17;padding-top:8px;font-size:15px}
.read b{color:#B23A1E}
.pagedark{background:#1E1B18 !important;color:#F2EADB}
.roomy p{font-size:16.5px;line-height:1.52}.roomy .fnode p{font-size:15px}.roomy .fnode h4{font-size:16.5px}.roomy td{font-size:15px;padding:9px 10px}
.roomy .eq{font-size:14.5px;padding:9px 10px}.roomy .box{padding:18px 20px}.roomy .note{font-size:13.5px}.roomy .down{margin:12px 0;font-size:30px}
.roomy .fnode{padding:14px 16px}.roomy .figt{font-size:16px}.roomy .read{font-size:16px}
.pagedark .hd{color:#E07A5F;border-bottom-color:#F2EADB}.pagedark .hd .no{color:#F2EADB}
.pagedark .lab{color:#E07A5F}
.concl{display:grid;grid-template-columns:44px 1fr;gap:6px;margin-bottom:8px}
.concl .n{font-family:Slab,serif;font-size:34px;color:#E07A5F;line-height:1}
.concl p{font-size:15.5px;line-height:1.4}
.tok{margin-top:10px;border-top:3px solid #E07A5F;padding-top:8px}.tokg{display:grid;grid-template-columns:1fr 1.3fr;gap:30px;align-items:start}.evo{color:#F2EADB}.evo th{background:#3A342C;color:#F2EADB;padding:4px 8px;font-size:13px}.evo td{border-color:#4A443B;padding:3px 8px;font-size:13.5px}.tokg b{color:#E07A5F;font-size:16px;display:block}.tokg p{font-size:14px;line-height:1.38;margin-top:3px}.persp{margin-top:8px;font-size:16px;line-height:1.38}.persp b{color:#E07A5F}
.impl{background:#F4ECDB;color:#1C1A17;padding:11px 15px;margin-bottom:11px}
.impl b{color:#B23A1E;display:block;font-size:16.5px;margin-bottom:3px}
.impl p{font-size:15px;line-height:1.42}
/* capa */
.cover .kick{position:absolute;left:96px;top:86px;font-family:PlexMono,monospace;font-size:19px;letter-spacing:.2em;color:#B23A1E}
.cover .ttl{position:absolute;left:96px;top:130px;font-family:Slab,serif;font-size:122px;line-height:.98;letter-spacing:-.01em}
.cover .sub{position:absolute;left:96px;top:400px;width:820px;font-size:30px;line-height:1.3;color:#3A352E}
.cover .res{position:absolute;left:96px;top:518px;width:840px;border-left:5px solid #B23A1E;padding:4px 0 4px 20px}
.cover .res .lab{margin-bottom:4px}
.cover .res p{font-size:16.5px;line-height:1.55}
.cover .team{position:absolute;left:96px;top:735px;width:840px;border-top:3px solid #1C1A17;padding-top:12px}
.cover .team b{font-family:Slab,serif;font-weight:400;font-size:34px}
.cover .team p{font-style:italic;color:#3A352E;font-size:17px}
.cover .frame{position:absolute;left:1040px;top:100px;width:460px;height:640px;border:6px solid #1C1A17;background:#EFE5CF;box-shadow:12px 12px 0 #1C1A17;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px}
.cover .frame .cap{font-family:PlexMono,monospace;font-size:14px;letter-spacing:.12em;color:#6B6457;text-transform:uppercase;text-align:center;line-height:1.6}
.cover .stamp{position:absolute;left:960px;top:610px;width:200px;height:200px;border:6px solid #B23A1E;border-radius:50%;background:#ECE3CF;display:flex;flex-direction:column;align-items:center;justify-content:center;transform:rotate(-12deg);color:#B23A1E;text-align:center}
.cover .stamp small{font-family:PlexMono,monospace;font-size:14px;letter-spacing:.1em}
.cover .stamp strong{font-family:Slab,serif;font-weight:400;font-size:52px;line-height:1}
"""


def page(no, kicker, title, body, source='', dark=False, roomy=False):
    return (f'<section class="page{" pagedark" if dark else ""}{" roomy" if roomy else ""}"><div class="hd"><span>{kicker}</span><span class="no">{no:02d}</span></div>'
            f'<h1>{title}</h1>{body}<div class="ft">{source}</div></section>')


def figbox(title, svg_html, note=''):
    n = f'<div class="note" style="margin-top:4px">{note}</div>' if note else ''
    return f'<div class="figt">{title}</div><div class="fig">{svg_html}</div>{n}'


def symbol_big(size):
    return (f'<svg viewBox="0 0 100 100" style="width:{size}px;height:{size}px" aria-hidden="true">'
            f'<path d="M18 23h55l8 22H10z" fill="{RED}"/><path d="M31 55h55l8 22H23z" fill="none" stroke="{INK}" stroke-width="3"/></svg>')


def risk(k, title, big, text):
    return f'<div class="risk"><div class="k">{k}</div><b>{title}</b><strong>{big}</strong><p>{text}</p></div>'


# ---------------------------------------------------------------- slides

def build(D):
    S, Rg = D['S'], D['R']
    t15, t16, t13r = D['t15'], D['t16'], D['t13r']
    F = facts(D)
    prim, prim_o, k = F['prim'], F['prim_o'], F['k']
    gross, mid_net, mid_cost = F['gross'], F['mid_net'], F['mid_cost']
    r12, cap = F['r12'], F['cap']
    orig, low = D['conv']['orig'], D['conv']['low']
    rot = D['rot']
    jx, r19, j19 = D['x17j'], D['r19'], D['r19j']
    hm = r19[(r19.regra == 'hmm_filtrado') & (r19.cenario_custos == 'intermediario') & (r19.lag_pregoes == 1)].iloc[0]
    hb = r19[(r19.regra == 'faixa_fixa') & (r19.cenario_custos == 'intermediario') & (r19.lag_pregoes == 1)].iloc[0]
    x17 = D['x17']
    xa = x17[(x17.par == 'XAUT/USD') & (x17.min_barras == 4) & (x17.cenario_custos == 'intermediario') & (x17.lag_pregoes == 1)].iloc[0]
    ini = j19['inicio_regra']
    ini_txt = f'{["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][int(ini[5:7]) - 1]}/{ini[:4]}'
    probs = pd.read_csv(ROOT / 'results/v2/T19_regimes_probabilidades.csv')
    pages = []

    # 01 · capa
    pages.append(f"""<section class="cover">
<div class="kick">7º DATATHON DE MOEDAS DIGITAIS · FGV EESP · 2026</div>
<div class="ttl">PAXG contra<br>o ouro</div>
<div class="sub">Quanto o token se afasta do ouro, por que o desvio persiste e quem consegue ganhar com essa diferença</div>
<div class="res"><div class="lab">Resumo</div><p>Medimos o desvio entre o PAXG e o ouro em {num(S['valid_hours'], 0)} horas, de 2020 a 2026. Ele tem dois ritmos: um ruído que some em cerca de {num(t15['meia_vida_transitorio_pregoes'], 0)} pregões e um nível que dura meses. A arbitragem na reabertura do fim de semana não cobre os custos ({num(mid_net, 0)} bps por operação). Quem já quer ouro captura o nível trocando GLDM por PAXG: {num(prim.ganho_anual_vs_gldm_bps, 0, True)} bps por ano contra o GLDM (IC 90% de {num(prim.ic90_lo, 0)} a {num(prim.ic90_hi, 0)}), e a mesma regra rende {num(jx['ganho_anual_bps'], 0, True)} bps por ano no XAUT, sem ajuste.</p></div>
<div class="team"><b>Equipe BitFlow</b><p>Gabriel Navarro · Lorenzo Cavalcante · Rodrigo Menin</p></div>
<div class="frame">{symbol_big(300)}<div class="cap">barra cheia: o ouro<br>barra vazada: o token<br>o deslocamento: o desvio</div></div>
<div class="stamp"><small>ROTAÇÃO</small><strong>{num(prim.ganho_anual_vs_gldm_bps, 0, True)}</strong><small>bps por ano</small></div>
</section>""")

    # 02 · motivação, fundamentação e hipóteses
    vol26 = F['y26'].usd_volume_millions / 1000
    body = f"""
<div class="grid" style="grid-template-columns:1fr 1fr 1.05fr;gap:24px">
 <div class="box">
  <div class="lab">Motivação</div>
  <p>O PAXG é um token da Paxos lastreado em uma onça troy de ouro. Negocia em corretoras de cripto 24 horas por dia, inclusive quando o ouro à vista (XAUUSD) não negocia. Deveria valer o ouro, mas se afasta: em janeiro de 2021, 90% das horas ficaram mais de {num(F['j21_p10'], 0)} bps acima; em março de 2024, ficou de {num(F['m24_lo'], 1)}% a {num(F['m24_hi'], 1)}% abaixo durante três pregões.</p>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:10px;margin-top:10px">
   <div><div class="big" style="white-space:nowrap;font-size:34px">US$ {num(vol26, 0)} bi</div><p class="note">negociados na Binance em 2026, nas horas de ouro ativo</p></div>
   <div><div class="big" style="white-space:nowrap;font-size:34px">36 bps</div><p class="note">desvio mediano em hora comum, 2020–2026</p></div>
  </div>
  <div class="lab" style="margin-top:18px">Quando o ouro fecha</div>
  <div class="flow" style="grid-template-columns:1fr 20px 1fr 20px 1fr;margin-top:6px">
   <div class="fnode"><h4>Sexta, 17h</h4><p>o XAUUSD para (hora de Nova York)</p></div><div class="arr">→</div>
   <div class="fnode red"><h4>Fim de semana</h4><p>o token segue negociando</p></div><div class="arr">→</div>
   <div class="fnode"><h4>Domingo, 18h</h4><p>o XAUUSD reabre</p></div>
  </div>
  <p class="note" style="margin-top:10px">Na reabertura os dois preços voltam a ser comparáveis. É o primeiro lugar onde procurar arbitragem (H2). Desde jul/2026 a CME também negocia ouro no fim de semana.</p>
 </div>
 <div class="box">
  <div class="lab">Fundamentação</div>
  <p><b>Makarov e Schoar (2020).</b> Desvios de preço entre corretoras de cripto são grandes e recorrentes, sobretudo entre países, onde mover capital é difícil.</p>
  <p><b>Shleifer e Vishny (1997).</b> Arbitradores com capital limitado não eliminam desvios que podem piorar antes de fechar.</p>
  <p><b>Lyons e Viswanath-Natraj (2023).</b> A paridade das stablecoins depende da arbitragem de criação e resgate no emissor.</p>
  <p><b>Petajisto (2017).</b> ETFs negociam com prêmio e desconto sobre o valor dos ativos, maiores quando os ativos são ilíquidos ou negociam em outro horário.</p>
  <p><b>Cong, Mayer e Rabetti (2026).</b> O ouro tokenizado acompanha o ouro em retorno (correlação diária de 0,99) e tem liquidez menor que a do GLD.</p>
  <div class="dark" style="margin-top:12px"><p><b style="color:#E07A5F">Lacuna:</b> não encontramos medida, para o PAXG, de quanto do desvio é ruído e quanto é nível, nem de quem consegue capturá-lo depois dos custos. Correlação alta não descarta um nível persistente.</p></div>
 </div>
 <div>
  <div class="redbar" style="margin-bottom:12px"><p style="font-size:21px;font-weight:800;line-height:1.25">O desvio do PAXG paga alguém? Quem, e quanto?</p></div>
  <div class="hyp"><p><b class="t">H1 · dois ritmos.</b> O desvio tem um ruído que some em dias e um nível que dura meses.</p><p class="tt">Teste: componentes não observados, correção de erro e regimes de Markov.</p></div>
  <div class="hyp" style="margin-top:10px"><p><b class="t">H2 · a reabertura não paga.</b> Comprar o barato e vender o caro na reabertura do fim de semana, com saída em até 24 h, não cobre os custos.</p><p class="tt">Teste: 44 operações e 1.458 combinações de custo e prazo.</p></div>
  <div class="hyp" style="margin-top:10px"><p><b class="t">H3 · a rotação captura o nível.</b> Quem já quer ouro ganha trocando GLDM por PAXG no desconto, sem vender a descoberto.</p><p class="tt">Teste: regra fixada pelo custo, placebo, XAUT, regras alternativas e comparação com só carregar o token.</p></div>
  <div class="lab" style="margin-top:14px">Delimitação</div>
  <p style="font-size:14px">28/08/2020 a 08/11/2026 · PAXG/USDT da Binance contra XAUUSD da Dukascopy · valores em dólares, antes de impostos · custos do token supostos em cenários · associação, não causa.</p>
 </div>
</div>"""
    pages.append(page(2, 'I · Motivação e problema', 'Motivação, fundamentação e hipóteses', body,
                      'Makarov e Schoar (2020), JFE 135 · Shleifer e Vishny (1997), JF 52 · Lyons e Viswanath-Natraj (2023), JIMF 131 · Petajisto (2017), FAJ 73 · Cong, Mayer e Rabetti (2026), Tokenizing Real-World Assets, Wharton (WIFPR).', roomy=True))

    # 03 · dados
    ex = F['ex']
    body = f"""
<div class="strip">
 <div><strong>{num(S['valid_hours'], 0)}</strong><span>horas com ouro e token ativos</span></div>
 <div><strong>{int(S['valid_weekends'])}</strong><span>fins de semana válidos de {int(S['candidate_weekends'])}</span></div>
 <div><strong>{num(D['plac']['dias_uteis'], 0)}</strong><span>pregões da NYSE (base diária)</span></div>
 <div><strong>{num(jx['dias_validos'], 0)}</strong><span>pregões de XAUT (teste em outro token)</span></div>
 <div><strong>3</strong><span>checagens em outras fontes</span></div>
</div>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:24px;margin-top:20px">
 <div class="box">
  <div class="lab">Fontes</div>
  <table style="font-size:13.5px"><tbody>
   <tr><td><b>PAXG/USDT</b></td><td>Binance, arquivo público, hora e minuto</td></tr>
   <tr><td><b>USDT/USD</b></td><td>Bitfinex; Coinbase como checagem</td></tr>
   <tr><td><b>XAUUSD</b></td><td>Dukascopy, compra e venda</td></tr>
   <tr><td><b>XAUT/USD</b></td><td>Bitfinex, hora (teste com outro token)</td></tr>
   <tr><td><b>GLD e GLDM</b></td><td>SPDR: taxas, spread e checagem</td></tr></tbody></table>
  <p class="note" style="margin-top:8px">Cada arquivo bruto tem data, URL e hash registrados; a Kraken entra por consulta pontual à API. Horas sem ouro ativo, sem câmbio observado ou em feriados não confirmados ficam fora; nenhuma exclusão por ser extrema.</p>
 </div>
 <div class="box">
  <div class="lab">A medida, numa hora real</div>
  <p style="font-size:14px">04/03/2024, 16h UTC:</p>
  <div class="eq">PAXG {num(ex.p_usdt, 2)} USDT × {num(ex.q, 4)} = US$ {num(ex.p_usdt * ex.q, 2)}</div>
  <div class="eq">ouro (Dukascopy) = US$ {num(ex.S, 2)}</div>
  <div class="eq">desvio = 10.000 × ln(PAXG em US$ ÷ ouro) = {num(ex.basis_log_bps, 1)} bps</div>
  <p style="font-size:14px">Positivo: o token está acima do ouro. 100 bps = 1%. Na mesma hora, a Kraken dá {num(ex.kraken_bps, 1)} bps.</p>
  <p class="note" style="margin-top:6px">Os modelos e a rotação usam a média do desvio das 15h às 20h UTC de cada pregão, quando ETF e token negociam juntos.</p>
 </div>
 <div class="dark">
  <div class="lab">Antes de concluir, checamos</div>
  <table style="font-size:14px;color:#F2EADB"><tbody>
   <tr><td style="border-color:#4A443B">Nosso ouro × GLD por onça</td><td class="n" style="border-color:#4A443B">{num(D['gld']['median_abs_level_difference_bps'])} bps</td></tr>
   <tr><td style="border-color:#4A443B">USDT/USD: Bitfinex × Coinbase</td><td class="n" style="border-color:#4A443B">{num(S['fx_source_median_abs_difference_bps'])} bps</td></tr>
   <tr><td style="border-color:#4A443B">PAXG: Binance × Kraken nos extremos</td><td class="n" style="border-color:#4A443B">{num(F['kx_diff'], 0)} bps</td></tr></tbody></table>
  <p style="margin-top:10px;font-size:14px">Diferenças medianas. O desconto de 3% de março de 2024 aparece também na Kraken, então não é erro de uma corretora.</p>
  <p style="margin-top:8px;font-size:14px">Testes automáticos alteram dados futuros e conferem que nenhuma decisão anterior muda.</p>
 </div>
</div>"""
    pages.append(page(3, 'II · Dados', 'Dados, medida e checagens', body,
                      'Binance, Bitfinex, Coinbase, Dukascopy, Kraken e SPDR. Janela: 28/08/2020 12:00 a 08/11/2026 00:00 UTC. Preço de hora = último negócio, sem livro de ofertas.', roomy=True))

    # 04 · metodologia I · fluxograma
    body = """
<div class="flow" style="grid-template-columns:1fr 34px 1.1fr 34px 1fr 34px 1fr">
 <div class="fnode"><h4>1 · Preços</h4><p>PAXG/USDT (Binance), USDT/USD (Bitfinex) e XAUUSD (Dukascopy), hora a hora.</p></div><div class="arr">→</div>
 <div class="fnode red"><h4>2 · Desvio</h4><p class="m">10.000 × ln(PAXG em US$ ÷ ouro)</p><p>só com ouro ativo e câmbio observado</p></div><div class="arr">→</div>
 <div class="fnode"><h4>3 · Série diária</h4><p>Média das 15h às 20h UTC de cada pregão da NYSE: 1.552 dias.</p></div><div class="arr">→</div>
 <div class="fnode"><h4>4 · Três perguntas</h4><p>Como o desvio se comporta (H1), se a arbitragem paga (H2), se a rotação paga (H3).</p></div>
</div>
<div class="down">↓</div>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:22px">
 <div class="fnode"><h4>H1 · Descrever o desvio</h4><p><b>Componentes não observados:</b> separa nível e ruído.<br><b>Correção de erro:</b> quanto do desvio fecha por dia.<br><b>Regimes de Markov (HMM):</b> data os períodos de prêmio, neutro e desconto.</p></div>
 <div class="fnode"><h4>H2 · Arbitragem na reabertura</h4><p>Usa preços de minuto em torno da reabertura, não a série diária. Sinal 1 h depois da reabertura, se o desvio absoluto passa de 10 bps; entrada no minuto seguinte; token contra ouro; saída em 1, 6 ou 24 h; quatro execuções e venda a descoberto.</p></div>
 <div class="fnode"><h4>H3 · Rotação GLDM ↔ PAXG</h4><p>Quem já tem ouro vai ao PAXG se o desvio ≤ −19 bps e volta ao GLDM se ≥ +19 bps. A faixa é o custo de um ciclo. Execução no pregão seguinte, sem venda a descoberto.</p></div>
</div>
<div class="down">↓</div>
<div class="grid" style="grid-template-columns:1.6fr 1fr;gap:26px">
 <div class="fnode"><h4>5 · Como avaliamos</h4><p>Intervalos de 90% por bootstrap em blocos de 6 meses na rotação (95% e blocos de 4 semanas na arbitragem) · três cenários de custo (original, intermediário, mínimo) · execução dois pregões depois · placebo com 1.000 carteiras de datas sorteadas · regra alternativa por regimes · a mesma regra no XAUT, outro token de ouro, sem nenhum ajuste.</p></div>
 <div class="dark" style="box-shadow:7px 7px 0 #B23A1E"><div class="lab">Regras contra dado futuro</div><p style="font-size:13.5px">O sinal usa só o dia; a execução é no pregão seguinte. Modelos reestimados só com o passado. Fixado por hash antes dos resultados: medida, arbitragem e custos originais. Definido depois, e marcado assim: componentes, correção de erro, HMM, rotação e custos intermediários. Regra do XAUT registrada antes do download.</p></div>
</div>"""
    pages.append(page(4, 'III · Metodologia', 'Metodologia I · do preço ao resultado', body,
                      'Pipeline em Python 3.11; cada execução grava configuração, hashes e saídas. Detalhes de custos e grades no material suplementar.', roomy=True))

    # 05 · metodologia II · modelos e operações
    body = f"""
<div class="grid" style="grid-template-columns:1.12fr 1fr;gap:30px">
 <div>
  <div class="lab">Os três modelos do desvio (H1)</div>
  <div class="box" style="padding:10px 14px"><b>Componentes não observados</b> (Harvey, 1989)
   <div class="eq">desvio<sub>t</sub> = nível<sub>t</sub> + c<sub>t</sub> + ruído<sub>t</sub><br>nível<sub>t</sub> = nível<sub>t−1</sub> + η<sub>t</sub><br>c<sub>t</sub> = φ c<sub>t−1</sub> + ω<sub>t</sub></div>
   <p style="font-size:13.5px">O nível anda devagar; c<sub>t</sub> volta à média com meia-vida ln(0,5)/ln(φ).</p></div>
  <div class="box" style="padding:10px 14px;margin-top:10px"><b>Correção de erro</b> (retorno diário, erros HAC)
   <div class="eq">r<sub>PAXG,t</sub> = a + b<sub>0</sub> r<sub>ouro,t</sub> + b<sub>1</sub> r<sub>ouro,t−1</sub> − γ desvio<sub>t−1</sub></div>
   <p style="font-size:13.5px">b<sub>0</sub> diz quanto do ouro o token acompanha no dia; γ, quanto do desvio de ontem se corrige hoje.</p></div>
  <div class="box" style="padding:10px 14px;margin-top:10px"><b>Regimes de Markov (HMM)</b>, 3 estados com média e variância próprias
   <div class="flow" style="grid-template-columns:1fr 24px 1fr 24px 1fr 24px 1fr;margin-top:8px">
    <div class="fnode" style="padding:6px 8px"><p>dados até o fim do mês anterior</p></div><div class="arr" style="font-size:20px">→</div>
    <div class="fnode" style="padding:6px 8px"><p>estima o modelo (mín. 500 pregões)</p></div><div class="arr" style="font-size:20px">→</div>
    <div class="fnode red" style="padding:6px 8px"><p>filtra cada dia do mês: P(desconto), P(prêmio)</p></div><div class="arr" style="font-size:20px">→</div>
    <div class="fnode" style="padding:6px 8px"><p>sinal no dia, execução no pregão seguinte</p></div>
   </div>
   <p style="font-size:13.5px;margin-top:6px">A probabilidade filtrada do dia usa só dados até aquele dia. Regra: P(desconto) &gt; 50% → PAXG; P(prêmio) &gt; 50% → GLDM.</p></div>
 </div>
 <div>
  <div class="lab">As duas operações testadas (H2 e H3)</div>
  <table><thead><tr><th></th><th>Arbitragem na reabertura</th><th>Rotação GLDM ↔ PAXG</th></tr></thead><tbody>
   <tr><td><b>Quem</b></td><td>Arbitrador com conta em cripto e em ouro</td><td>Quem já quer ouro em dólares</td></tr>
   <tr><td><b>Posição</b></td><td>Token contra ouro, 1 onça por perna</td><td>100% em ouro: GLDM ou PAXG</td></tr>
   <tr><td><b>Sinal</b></td><td>1 h após a reabertura, desvio absoluto acima de 10 bps</td><td>Média do pregão fora da faixa de ±19 bps</td></tr>
   <tr><td><b>Saída</b></td><td>Prazo fixo: 1, 6 ou 24 h</td><td>Sem prazo: quando o desvio cruza a outra ponta</td></tr>
   <tr><td><b>Custo</b></td><td>Quatro execuções: {num(mid_cost, 1)} bps no cenário intermediário</td><td>Duas trocas por ciclo: {num(float(prim.custo_ciclo_bps), 0)} bps</td></tr>
   <tr><td><b>Venda a descoberto</b></td><td class="r"><b>Sim, de token ou ouro</b></td><td><b>Não</b></td></tr></tbody></table>
  <div class="box" style="margin-top:14px"><div class="lab">Custos supostos por execução</div>
   <p style="font-size:13.5px"><b>Intermediário:</b> taxa do token 5 bps, spread 2, ouro 1, câmbio 2 (ida e volta), deslizamento 2. <b>Original</b> (fixado antes dos resultados): taxa 10, spread 10. O intermediário foi escolhido depois dos resultados; os dois aparecem sempre lado a lado.</p></div>
 </div>
</div>"""
    pages.append(page(5, 'III · Metodologia', 'Metodologia II · os modelos do desvio e as duas operações', body,
                      'Harvey (1989); statsmodels UnobservedComponents, OLS com HAC e MarkovRegression. Desvio diário: média 15–20 UTC dos pregões da NYSE.', roomy=True))

    # 06 · resultado 1 (H1)
    body = f"""
<div class="grid" style="grid-template-columns:1.55fr 1fr;gap:28px">
 <div>
  {figbox('(a) Desvio diário e nível estimado pelo modelo de componentes, 2020–2026', fig_level(D['serie'], F['kx_ext']))}
 </div>
 <div>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:12px">
   <div class="box"><div class="lab">Ruído</div><div class="big">{num(t15['meia_vida_transitorio_pregoes'])}</div><p class="note">pregões de meia-vida do componente rápido</p></div>
   <div class="box"><div class="lab">Nível</div><div class="big">{pct(Rg['variance_share_monthly_level'])}</div><p class="note">da variação horária vem do nível do mês</p></div>
   <div class="box"><div class="lab">Segue o ouro</div><div class="big">{pct(t16['coef']['ret_ouro'])}</div><p class="note">do retorno diário do ouro, no mesmo dia</p></div>
   <div class="box"><div class="lab">Corrige</div><div class="big">{pct(t16['correcao_diaria'])}</div><p class="note">do desvio por dia; meia-vida de {num(t16['meia_vida_pregoes'])} pregões, perto dos {num(t15['meia_vida_transitorio_pregoes'])} do outro modelo</p></div>
  </div>
  <div class="read" style="margin-top:12px"><b>Leitura.</b> O token acompanha o ouro no dia, mas carrega um nível próprio, de {num(F['lvl_min'], 0)} a {num(F['lvl_max'], 0, True)} bps, que muda devagar. Uma explicação compatível é o custo de arbitrar: resgatar PAXG na Paxos custa de 0,125% a 0,5% e exige conta aprovada; o retorno do ouro explica só {pct(t16['semanal_var_desvio_em_ret_ouro']['r2'])} da variação semanal do desvio.</div>
 </div>
</div>
<div class="grid" style="grid-template-columns:1.55fr 1fr;gap:28px;margin-top:12px">
 <div>{figbox(f'(b) Regimes de Markov com probabilidade filtrada, reestimados todo mês só com o passado (desde {ini_txt})', fig_hmm(D['serie'], probs), 'Fundo vermelho claro: regime de desconto dominante; azul claro: prêmio dominante; linha: desvio diário, em bps.')}</div>
 <div>
  <div class="lab" style="margin-top:4px">O que o HMM acrescenta</div>
  <p>Ele data os períodos de forma automática e sem olhar o futuro: o regime de desconto domina {pct(j19['fracao_dias_desconto_dominante'])} dos pregões desde {ini_txt}, e o de prêmio, {pct(j19['fracao_dias_premio_dominante'])}. Os regimes duram meses, como o nível do painel (a). Os estados são ordenados pela média de cada reestimação; em set/2022, primeira janela, o modelo ainda marcou como prêmio dias de desvio negativo.</p>
  <p style="margin-top:8px">Em 2026, {pct(F['y26'].within_25_bps)} das horas ficaram a até 25 bps do ouro, contra {pct(F['y20'].within_25_bps)} em 2020; a tendência ainda não é estatisticamente firme.</p>
  <div class="read" style="margin-top:10px"><b>H1 se sustenta.</b> O ruído some em dias; o nível dura meses. O ganho possível está nas viradas do nível.</div>
 </div>
</div>"""
    pages.append(page(6, 'IV · Resultados', 'Resultado 1 · o desvio tem dois ritmos (H1)', body,
                      f'Binance, Bitfinex e Dukascopy; Kraken nos extremos. Componentes, correção de erro e HMM posteriores à análise original. Mínimo do dia: mar/2024 (Kraken: {F["kx_ext"]} bps).'))

    # 07 · resultado 2 (H2)
    budget = D['budget'].set_index('horizon_hours')
    p1 = D['pair'].loc['b_0_to_b_1h']
    body = f"""
<div class="grid" style="grid-template-columns:1fr 1fr 1.1fr;gap:26px">
 <div>
  {figbox('(a) O token sai do fim de semana mais caro', fig_weekend(t13r), 'Variação média do desvio com sinal desde o fechamento de sexta, em bps; tracejado: mediana.')}
  <div class="box" style="margin-top:12px"><div class="lab">A reabertura herda a sexta</div>
   <p style="font-size:14px">O desvio de sexta explica o desvio da reabertura com R² de <b>{num(t13r['r2_reabertura_em_sexta'], 2)}</b>, que sobe para <b>{num(t13r['r2_7h_em_sexta'], 2)}</b> sete horas depois; o sinal se mantém em {pct(t13r['mesmo_sinal_sexta_reabertura'])} dos fins de semana. O desvio absoluto cai em média {num(-p1.mean_abs_change_bps, 1)} bps em 1 h, mas não zera.</p></div>
 </div>
 <div>
  {figbox('(b) O custo fica com a maior parte da diferença', fig_waterfall(gross, mid_cost, mid_net), f'Média de {F["n_eval"]} operações de 6 h, cenário intermediário.')}
 </div>
 <div>
  <div class="figt">(c) Nenhum cenário de custo deixa a média positiva</div>
  <table><thead><tr><th>Cenário (6 h)</th><th class="n">Saldo</th><th class="n">Positivas</th></tr></thead><tbody>
   <tr><td>Original (taxa 10, spread 10)</td><td class="n">{num(orig.mean_model_bps, 1)}</td><td class="n">{F['orig_pos']} de {F['n_eval']}</td></tr>
   <tr class="hl"><td>Intermediário (taxa 5, spread 2)</td><td class="n">{num(mid_net, 1)}</td><td class="n">{F['mid_pos']} de {F['n_eval']}</td></tr>
   <tr><td>Mínimo da grade</td><td class="n">{num(low.mean_model_bps, 1)}</td><td class="n">—</td></tr></tbody></table>
  <p style="margin-top:10px;font-size:14px">Nas <b>{num(F['n_grid'], 0)}</b> combinações de custo e prazo (1, 6 e 24 h), nenhuma média ficou positiva. O ganho bruto em 6 h é de {num(gross)} bps (IC 95% de {num(budget.loc[6, 'gross_lo'], 1)} a {num(budget.loc[6, 'gross_hi'], 1)}, blocos de 4 semanas), menor que o custo mínimo da grade.</p>
  <p style="margin-top:6px;font-size:14px">Faltaram preços para {int(S['signals_unassessed'])} sinais; eles precisariam render {num(F['tip_mid'], 0)} bps em média para zerar o saldo deste cenário. A venda a descoberto de PAXG não foi verificada.</p>
  <div class="read" style="margin-top:10px"><b>H2 se sustenta.</b> Em poucas horas só o ruído fecha, e ele é pequeno demais para quatro execuções.</div>
 </div>
</div>"""
    pages.append(page(7, 'IV · Resultados', 'Resultado 2 · a reabertura não paga a arbitragem (H2)', body,
                      '301 fins de semana válidos; operações com preços de minuto da Binance, Bitfinex e Dukascopy. Cenário intermediário escolhido depois dos resultados; o original foi fixado antes.', roomy=True))

    # 08 · resultado 3 (H3)
    alw = rot[(rot.config == 'sempre PAXG') & (rot.cenario_custos == 'intermediario')].iloc[0]
    yr = D['plac']['ganho_por_ano_calendario_bps']
    t14b = D['t14'].set_index('horizonte')
    cs = float(prim.custo_ciclo_bps) / 2
    body = f"""
<div class="flow" style="grid-template-columns:1fr 30px 1fr 30px 1fr 30px 1fr 30px 1fr">
 <div class="fnode"><h4>Carteira em GLDM</h4><p>sempre 100% em ouro</p></div><div class="arr">→</div>
 <div class="fnode red"><h4>Desvio ≤ −{k} bps</h4><p>token com desconto</p></div><div class="arr">→</div>
 <div class="fnode"><h4>Troca para PAXG</h4><p>no pregão seguinte · {num(cs, 1)} bps</p></div><div class="arr">→</div>
 <div class="fnode red"><h4>Desvio ≥ +{k} bps</h4><p>token com prêmio</p></div><div class="arr">→</div>
 <div class="fnode"><h4>Volta ao GLDM</h4><p>fica com a diferença</p></div>
</div>
<div class="grid" style="grid-template-columns:1.45fr 1fr;gap:28px;margin-top:16px">
 <div>{figbox(f'(a) Ganho acumulado contra manter o GLDM e desvio diário com a faixa de ±{k} bps', shift_label(fig_rotation(D['curve'], k), 'custos originais:', 14).replace(f'desvio do dia, bps; faixa de ±{k} bps; fundo verde = carteira em PAXG', ''), f'Fundo vermelho claro: carteira em PAXG. Em cima, linha cheia: custos intermediários; tracejada: originais. Embaixo: desvio do dia e faixa de ±{k} bps.')}</div>
 <div>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:12px">
   <div class="box"><div class="lab">Ganho</div><div class="big">{num(prim.ganho_anual_vs_gldm_bps, 0, True)}</div><p class="note">bps por ano contra o GLDM · IC 90% de {num(prim.ic90_lo, 0)} a {num(prim.ic90_hi, 0)}</p></div>
   <div class="box"><div class="lab">Ciclos</div><div class="big">{int(prim.ciclos)}</div><p class="note">{pct(prim.ciclos_positivos)} positivos; todo ano com operação foi positivo</p></div>
   <div class="box"><div class="lab">De onde vem</div><div class="big">{pct(F['share_week'])}</div><p class="note">do ganho em ciclos com mais de uma semana</p></div>
   <div class="box"><div class="lab">Sem a regra</div><div class="big">{num(alw.ganho_anual_vs_gldm_bps, 0)}</div><p class="note">bps por ano mantendo PAXG o tempo todo</p></div>
  </div>
  <div class="read" style="margin-top:12px"><b>Por que funciona onde a arbitragem falha.</b> Não há prazo para sair, então a carteira espera o desvio atravessar a faixa, e cada troca custa {num(cs, 1)} bps, sem perna de ouro nem empréstimo.</div>
  <div class="read" style="margin-top:10px"><b>H3 se sustenta</b> para carteiras pequenas, antes de impostos. O próximo slide mostra se o resultado resiste.</div>
 </div>
</div>
<div class="dark" style="box-shadow:7px 7px 0 #B23A1E;padding:10px 18px;margin-top:14px"><p style="font-size:14.5px"><b style="color:#E07A5F">E quem só carrega o token?</b> Entrar e sair do PAXG custa {num(F['rt_mid'], 0)} bps, contra 1 bp no ETF, mas o token não cobra taxa anual: em custo, ele fica mais barato depois de <b>{num(F['gld_m'])} meses</b> contra o GLD (0,40% ao ano) e <b>{num(F['gldm_m'])} meses</b> contra o GLDM (0,10%). Em 12 meses, porém, a variação do desvio tem desvio-padrão de <b>{num(t14b.loc['12 meses', 'desvio_padrao_bps'], 0)} bps</b>, contra {num(t14b.loc['12 meses', 'taxa_gldm_no_horizonte_bps'], 0)} bps de taxa do GLDM e {num(t14b.loc['12 meses', 'taxa_gld_no_horizonte_bps'], 0)} do GLD.</p></div>"""
    pages.append(page(8, 'IV · Resultados', 'Resultado 3 · a rotação GLDM ↔ PAXG captura o nível (H3)', body,
                      f'1.552 pregões da NYSE, 28/08/2020 a 06/11/2026. Por ano: 2022 {num(yr["2022"], 0, True)}, 2023 {num(yr["2023"], 0, True)}, 2024 {num(yr["2024"], 0, True)}, 2025 {num(yr["2025"], 0, True)}, 2026 {num(yr["2026"], 0, True)} bps. Regra definida depois da análise original.'))

    # 09 · resultado 4 (robustez)
    r_lag2 = rot_row(rot, f'faixa fixa ±{k}', 'intermediario', 2)
    r30 = rot_row(rot, 'faixa fixa ±30', 'intermediario', 1)
    ko = int(prim_o.k_bps)
    mv_o = rot_row(rot, 'nível móvel 60d ±30', 'original', 1)

    def row(name, r, hl=False):
        return (f'<tr class="{"hl" if hl else ""}"><td>{name}</td><td class="n">{int(r.ciclos)}</td><td class="n">{num(r.ganho_anual_vs_gldm_bps, 0, True)}</td>'
                f'<td class="n">[{num(r.ic90_lo, 0)}; {num(r.ic90_hi, 0)}]</td></tr>')
    table = ''.join([row(f'PAXG, regra principal (±{k})', prim, True), row('Execução dois pregões depois', r_lag2), row(f'Custos originais (±{ko})', prim_o),
                     row('Faixa de ±30 bps', r30), row('Faixa em torno do nível móvel de 60 pregões, custos originais', mv_o),
                     row(f'Regimes de Markov (desde {ini_txt})', hm), row(f'Faixa ±{k} no mesmo período do HMM', hb),
                     row('XAUT, mesma regra, sem ajuste', xa, True)])
    body = f"""
<div class="grid" style="grid-template-columns:1.05fr 1fr 1fr;gap:26px">
 <div>
  <div class="figt">(a) A regra contra custos, atraso, variações e outro token</div>
  <table><thead><tr><th>Configuração</th><th class="n">Ciclos</th><th class="n">bps/ano</th><th class="n">IC 90%</th></tr></thead><tbody>{table}</tbody></table>
  <p class="note" style="margin-top:6px">A regra principal não é a melhor da grade. O HMM também ganha, mas menos e com intervalo que inclui zero: um modelo mais elaborado não melhora a regra simples.</p>
 </div>
 <div>
  {figbox('(b) A mesma regra no XAUT, outro token de ouro', shift_label(fig_xaut_vs_paxg(D['curve'], D['x17c']), 'XAUT:', 30), f"XAUT/USD da Bitfinex, {num(jx['dias_validos'], 0)} pregões; correlação diária com o desvio do PAXG de {num(jx['correlacao_diaria_com_paxg'], 2)}. Regra registrada antes do download.")}
 </div>
 <div>
  {figbox('(c) Placebo: 1.000 rotações com datas sorteadas', fig_placebo(D['sims'], D['plac']['ganho_anual_bps']), f"Ganho anual em bps. Mesmo número de ciclos e mesmas durações; nenhuma chegou ao resultado da regra; no XAUT, {num(jx['fracao_placebos_acima'] * 1000, 0)} de 1.000.")}
 </div>
</div>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr 1.2fr;gap:24px;margin-top:16px">
 {risk('risco 1', 'O desconto pode piorar', num(prim.pior_queda_bps, 0) + ' bps', 'Queda contra o GLDM em mar/2024, com a carteira em PAXG; confirmada na Kraken.')}
 {risk('risco 2', 'Capacidade pequena', f'US$ {num(cap["2023"] / 1e3, 0)}–{num(cap["2026"] / 1e3, 0)} mil', 'por pregão, a 5% do volume; serve para carteiras pequenas.')}
 {risk('risco 3', 'Impostos e custódia', 'fora do saldo', 'Cada troca realiza ganho de capital; o token exige custódia.')}
 <div class="dark" style="box-shadow:7px 7px 0 #B23A1E"><p style="font-size:14.5px"><b style="color:#E07A5F">Resultado.</b> A rotação continua positiva com custos maiores, com atraso e contra o placebo, e a mesma regra, sem ajuste, ganha {num(jx['ganho_anual_bps'], 0, True)} bps por ano no XAUT.</p></div>
</div>"""
    pages.append(page(9, 'IV · Resultados', 'Resultado 4 · robustez: custos, atraso, placebo e XAUT', body,
                      'Tabelas T12 (PAXG), T17 (XAUT) e T19 (regimes) no pacote. IC por bootstrap circular em blocos de 6 meses (5.000 repetições).'))

    # 10 · discussão (escura)
    an = D['annual'].set_index('year')
    wk = D['t13'].set_index('periodo')
    yrr = D['plac']['ganho_por_ano_calendario_bps']
    led = pd.read_csv(ROOT / 'results/T2_trade_ledger.csv')
    led = led[(led.horizon_hours == 6) & (led.evaluated_trade == True)].copy()
    led['ano'] = pd.to_datetime(led.t_0, utc=True).dt.year
    arb = led.groupby('ano').gross_mid_bps.agg(['mean', 'count'])
    YS = [2021, 2023, 2025, 2026]
    def ev_row(label, vals):
        return f'<tr><td>{label}</td>' + ''.join(f'<td class="n">{v}</td>' for v in vals) + '</tr>'
    evo_rows = ''.join([
        ev_row('Desvio mediano, bps', [num(an.loc[y, 'median_abs_bps'], 0) for y in YS]),
        ev_row('Horas a até 25 bps do ouro', [pct(an.loc[y, 'within_25_bps']) for y in YS]),
        ev_row('Volume na Binance, US$ bi', [num(an.loc[y, 'usd_volume_millions'] / 1000, 1) for y in YS]),
        ev_row('Salto do ouro explicado pelo token (R²)', [num(wk.loc[str(y), 'r2'], 2) for y in YS]),
        ev_row('Arbitragem: ganho bruto em 6 h, bps', [num(arb.loc[y, 'mean'], 1, True) if y in arb.index else '—' for y in YS]),
        ev_row('Rotação: ganho no ano, bps', [num(yrr[str(y)], 0, True) if yrr[str(y)] else '0' for y in YS])])
    evo_n = f'{int(arb.loc[2025, "count"])} operações em 2025 e {int(arb.loc[2026, "count"])} em 2026'
    body = f"""
<div class="grid" style="grid-template-columns:1.12fr 1fr 1fr;gap:30px">
 <div>
  <div class="lab">Conclusões</div>
  <div class="concl"><span class="n">1</span><p><b>O token segue o ouro no dia</b> ({pct(t16['coef']['ret_ouro'])} do retorno diário), mas carrega um nível próprio de {num(F['lvl_min'], 0)} a {num(F['lvl_max'], 0, True)} bps que dura meses (H1).</p></div>
  <div class="concl"><span class="n">2</span><p><b>A arbitragem na reabertura não paga:</b> {num(gross, 1, True)} bps brutos contra {num(mid_cost, 1)} de custo; 0 de {num(F['n_grid'], 0)} combinações positivas (H2).</p></div>
  <div class="concl"><span class="n">3</span><p><b>Quem já tem ouro captura o nível:</b> a rotação GLDM ↔ PAXG rendeu {num(prim.ganho_anual_vs_gldm_bps, 0, True)} bps por ano (IC 90% de {num(prim.ic90_lo, 0)} a {num(prim.ic90_hi, 0)}) (H3).</p></div>
  <div class="concl"><span class="n">4</span><p><b>O resultado resiste:</b> custos originais, atraso, placebo e o XAUT ({num(jx['ganho_anual_bps'], 0, True)} bps/ano, sem ajuste). O HMM não melhora a regra simples.</p></div>
  <div class="concl"><span class="n">5</span><p><b>Para quem só carrega</b> (slide 8), o token fica mais barato só depois de {num(F['gld_m'])} meses (GLD) ou {num(F['gldm_m'])} (GLDM), e o risco de base de 12 meses ({num(r12.desvio_padrao_bps, 0)} bps) supera a economia de taxa.</p></div>
 </div>
 <div>
  <div class="lab">Implicações práticas</div>
  <div class="impl"><b>Investidores</b><p>Olhar o desvio do dia antes de escolher entre token e ETF; trocar de veículo no desconto vale mais que a taxa anual.</p></div>
  <div class="impl"><b>Corretoras e emissor</b><p>O atrito está no nível. Hipótese a testar: resgate mais barato e com menos exigências estreitaria a faixa.</p></div>
  <div class="impl"><b>Pesquisa em tokenização</b><p>Medir o nível do desvio, além da correlação, antes de tratar um token como substituto do ativo real.</p></div>
 </div>
 <div style="border:2px solid #6B6457;padding:14px 16px">
  <div class="lab">Limitações e próximos passos</div>
  <p style="font-size:15px">Custos do token supostos; cenário intermediário e regra de rotação definidos depois da análise original. O XAUT é um teste em outro ativo, no mesmo período, e não em datas novas.</p>
  <p style="font-size:15px">Capacidade pequena; impostos, custódia e empréstimo de PAXG fora do saldo.</p>
  <p style="font-size:15px">A coleta de emissão e resgate on-chain não terminou a tempo; fica como próximo passo.</p>
  <p style="font-size:15px">Próximos passos: acompanhar a regra daqui para frente sem mudá-la; incluir emissão on-chain e outras corretoras; levar a conta para reais, com IOF e IR.</p>
 </div>
</div>
<div class="tok"><div class="lab">O token e o ouro ao longo do tempo</div><div class="tokg">
 <table class="evo"><thead><tr><th></th><th class="n">2021</th><th class="n">2023</th><th class="n">2025</th><th class="n">2026*</th></tr></thead><tbody>{evo_rows}</tbody></table>
 <div><p><b>Leitura.</b> O PAXG já entrega o retorno do ouro; o que o separa do ativo é o nível do desvio. Até 2025 esse nível abriu e fechou sem direção. Em 2026, com o maior volume da amostra, o desvio ficou menor, a arbitragem perdeu até o ganho bruto e o token passou a antecipar boa parte do salto do ouro na reabertura, a descoberta de preço fora do horário descrita por Cong, Mayer e Rabetti (2026).</p>
 <p><b>Daqui para frente.</b> São dez meses, e a tendência trimestral do desvio ainda não é significativa (p = {num(D['t4']['p_value_exploratory'], 2)}). Se 2026 se mantiver, o token fica mais perto de um substituto do ouro e a rotação rende menos, como já rendeu no ano. Acompanhar a regra sem mudá-la é o teste.</p></div>
</div><p class="note" style="color:#C9BFA9;margin-top:3px;font-size:11.5px">* até 08/11. R²: salto do ouro de sexta à reabertura contra o movimento do token no fim de semana. Arbitragem simulada de 2024 a 2026 (6 h): {evo_n}.</p></div>
<div class="ft" style="position:absolute;left:106px;right:106px;bottom:16px;border-top:2px solid #6B6457;color:#F2EADB;padding-top:8px;display:flex;align-items:center;gap:14px">
 {symbol_big(32).replace(INK, '#F2EADB')}<span style="font-family:Slab,serif;font-size:24px">Obrigado!</span><span style="font-size:14px;color:#C9BFA9">Equipe BitFlow · Gabriel Navarro, Lorenzo Cavalcante e Rodrigo Menin · 7º Datathon de Moedas Digitais FGV EESP</span>
</div>"""
    pages.append(page(10, 'V · Discussão', 'Discussão, implicações e conclusões', body, '', dark=True))
    return pages


def main():
    from .v2_report_build import export
    D = load()
    pages = build(D)
    out = ROOT / 'slides'
    v3 = ROOT / 'results' / 'v3'
    v3.mkdir(parents=True, exist_ok=True)
    html_path, pdf_path = out / 'entrega_v3.html', out / 'entrega_v3.pdf'
    protected = {out / 'entrega.pdf', out / 'entrega_v2.pdf', out / 'entrega.html', out / 'entrega_v2.html'}
    assert pdf_path not in protected and html_path not in protected
    head = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=1600"><title>PAXG contra o ouro · BitFlow</title><style>' + CSS + '</style></head><body>'
    html_path.write_text(head + ''.join(pages) + '</body></html>', encoding='utf-8')
    qa = export(html_path, pdf_path, len(pages))
    shutil.copyfile(out / 'entrega_v2_suplementar.pdf', out / 'entrega_v3_suplementar.pdf')
    bad = [p for p in qa if p['overflow']]
    dump_json(v3 / 'QA_presentation_v3.json', {'at_utc': utc_now(), 'design': 'entrega-v3', 'pages': len(pages), 'qa': qa,
                                               'status': 'passed' if not bad else 'needs_review'})
    print('páginas', len(pages), 'estouros', bad)


if __name__ == '__main__':
    main()
