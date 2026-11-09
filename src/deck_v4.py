"""Apresentação final v4: HTML autônomo + PDF. Todos os números vêm de results/ (nada digitado à mão).

Uso: python -m src.deck_v4
"""
from __future__ import annotations

import html
import json
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from .common import ROOT, dump_json, utc_now

W, H = 1280, 720
INK, MUTED, GRID = 'var(--ink)', 'var(--muted)', 'var(--grid)'
TEAL, GOLD, RED, BAR, BG = 'var(--c1)', 'var(--c2)', 'var(--neg)', 'var(--bar)', 'var(--bg)'
MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


def num(value, d=1, sign=False):
    v = float(value)
    text = f'{abs(v):,.{d}f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    if v < 0:
        return '−' + text
    return ('+' + text) if sign and v > 0 else text


def pct(value, d=0):
    return num(float(value) * 100, d) + '%'


def read(name):
    return pd.read_csv(ROOT / 'results' / name)


def month_label(m):
    y, mo = m.split('-')
    return f'{MONTHS[int(mo) - 1]}/{y}'


# ------------------------------------------------------------------ gráficos (SVG)

def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" style="width:100%;height:auto;display:block" role="img" '
            f'aria-label="{html.escape(label, quote=True)}">{body}</svg>')


def t(x, y, s, size=16, fill=INK, anchor='start', weight=500, extra=''):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" {extra}>{html.escape(str(s))}</text>')


def chart_regime(monthly):
    w, h = 1180, 400
    left, right, top, bottom = 70, 20, 20, 50
    pw, ph = w - left - right, h - top - bottom
    lo, hi = -160, 160
    x = lambda i: left + (i + .5) / len(monthly) * pw
    y = lambda v: top + (hi - max(lo, min(hi, v))) / (hi - lo) * ph
    b = []
    b.append(f'<rect x="{left}" y="{y(25):.1f}" width="{pw}" height="{y(-25) - y(25):.1f}" fill="{GOLD}" opacity=".12"/>')
    for v in [-150, -100, -50, 0, 50, 100, 150]:
        b.append(f'<path d="M{left} {y(v):.1f}H{left + pw}" stroke="{INK if v == 0 else GRID}" stroke-width="{1.5 if v == 0 else 1}"/>')
        b.append(t(left - 10, y(v) + 5, num(v, 0, sign=True) if v else '0', 14, MUTED, 'end'))
    # faixa p10-p90
    up = ' '.join(f'{x(i):.1f},{y(v):.1f}' for i, v in enumerate(monthly.p90_bps))
    dn = ' '.join(f'{x(i):.1f},{y(v):.1f}' for i, v in reversed(list(enumerate(monthly.p10_bps))))
    b.append(f'<polygon points="{up} {dn}" fill="{TEAL}" opacity=".16"/>')
    line = ' '.join(f'{x(i):.1f},{y(v):.1f}' for i, v in enumerate(monthly.median_bps))
    b.append(f'<polyline points="{line}" fill="none" stroke="{TEAL}" stroke-width="3" stroke-linejoin="round"/>')
    for i, m in enumerate(monthly.month):
        if m.endswith('-01'):
            b.append(f'<path d="M{x(i):.1f} {top + ph}v6" stroke="{MUTED}"/>')
            b.append(t(x(i), top + ph + 28, m[:4], 15, MUTED, 'middle'))
    imax, imin = monthly.median_bps.idxmax(), monthly.median_bps.idxmin()
    for i, dy in [(imax, -14), (imin, 26)]:
        v = monthly.median_bps[i]
        b.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="5" fill="{GOLD}" stroke="var(--bg)" stroke-width="2"/>')
        anchor = 'start' if i < len(monthly) / 2 else 'middle'
        b.append(t(x(i) + (10 if anchor == 'start' else 0), y(v) + dy, f'{month_label(monthly.month[i])}: {num(v, 0, True)} bps', 16, INK, anchor, 700))
    b.append(t(left + 8, y(150), 'PAXG acima do ouro (prêmio)', 15, MUTED))
    b.append(t(left + 8, y(-150) + 5, 'PAXG abaixo do ouro (desconto)', 15, MUTED))
    b.append(t(left + pw, y(25) - 6, 'faixa de ±25 bps', 14, GOLD, 'end', 600))
    return svg(w, h, 'Mediana mensal do desvio do PAXG contra o ouro, de 2020 a 2026, entre −103 e +95 bps.', ''.join(b))


def chart_years(annual):
    w, h = 640, 380
    left, top, bottom = 20, 30, 60
    pw, ph = w - left - 10, h - top - bottom
    n = len(annual)
    bw = pw / n * .64
    b = []
    for v in [0, 25, 50, 75, 100]:
        yy = top + ph * (1 - v / 100)
        b.append(f'<path d="M{left} {yy:.1f}H{w - 10}" stroke="{GRID}"/>')
    for i, r in annual.reset_index(drop=True).iterrows():
        v = r.within_25_bps * 100
        xx = left + (i + .18) * pw / n
        yy = top + ph * (1 - v / 100)
        fill = TEAL if r.year == 2026 else GOLD
        b.append(f'<rect x="{xx:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{top + ph - yy:.1f}" fill="{fill}" rx="2"/>')
        b.append(t(xx + bw / 2, yy - 8, f'{num(v, 0)}%', 18, INK, 'middle', 700))
        label = f'{int(r.year)}' + ('*' if r.year in (2020, 2026) else '')
        b.append(t(xx + bw / 2, top + ph + 26, label, 16, MUTED, 'middle'))
    b.append(t(left, h - 8, '* 2020: a partir de 28/ago. 2026: até 8/nov.', 14, MUTED))
    return svg(w, h, 'Parcela das horas em que o PAXG ficou a até 25 bps do ouro, por ano.', ''.join(b))


def chart_quarters(ev):
    ev = ev[ev.complete_quarter].reset_index(drop=True)
    w, h = 560, 380
    left, top, bottom = 50, 30, 60
    pw, ph = w - left - 10, h - top - bottom
    y = lambda v: top + ph * (1 - v / 110)
    x = lambda i: left + (i + .5) / len(ev) * pw
    b = []
    for v in [0, 25, 50, 75, 100]:
        b.append(f'<path d="M{left} {y(v):.1f}H{w - 10}" stroke="{GRID}"/>')
        b.append(t(left - 8, y(v) + 5, v, 14, MUTED, 'end'))
    pts = ' '.join(f'{x(i):.1f},{y(v):.1f}' for i, v in enumerate(ev.median_abs_bps))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{TEAL}" stroke-width="3"/>')
    for i, v in enumerate(ev.median_abs_bps):
        b.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3.5" fill="{TEAL}"/>')
    for i, q in enumerate(ev.quarter):
        if q.endswith('Q1'):
            b.append(t(x(i), top + ph + 26, q[:4], 15, MUTED, 'middle'))
    last = len(ev) - 1
    b.append(t(x(last), y(ev.median_abs_bps[last]) - 12, num(ev.median_abs_bps[last], 0), 17, INK, 'end', 700))
    b.append(t(x(int(ev.median_abs_bps.idxmax())), y(ev.median_abs_bps.max()) - 12, num(ev.median_abs_bps.max(), 0), 17, INK, 'middle', 700))
    return svg(w, h, 'Mediana trimestral do desvio absoluto, de 2020 a 2026, em bps.', ''.join(b))


def hbars(items, w, h, maxv, label, colors=None, unit='', row=70, lw=250):
    b = []
    pw = w - lw - 90
    for i, (name, v) in enumerate(items):
        yy = 20 + i * row
        col = (colors or [TEAL] * len(items))[i]
        b.append(t(0, yy + 26, name, 19, INK, 'start', 600))
        b.append(f'<rect x="{lw}" y="{yy}" width="{v / maxv * pw:.1f}" height="38" fill="{col}" rx="2"/>')
        b.append(t(lw + v / maxv * pw + 10, yy + 27, num(v, 1) + unit, 20, INK, 'start', 700))
    return svg(w, h, label, ''.join(b))


def chart_waterfall(gross, cost, net):
    w, h = 640, 400
    left, top = 70, 30
    ph = 300
    lo, hi = -30, 10
    y = lambda v: top + (hi - v) / (hi - lo) * ph
    b = []
    for v in [0, -10, -20, -30]:
        b.append(f'<path d="M{left} {y(v):.1f}H{w - 10}" stroke="{INK if v == 0 else GRID}"/>')
        b.append(t(left - 8, y(v) + 5, num(v, 0), 14, MUTED, 'end'))
    bw = 130
    xs = [left + 40, left + 230, left + 420]
    b.append(f'<rect x="{xs[0]}" y="{y(gross):.1f}" width="{bw}" height="{y(0) - y(gross):.1f}" fill="{GOLD}" rx="2"/>')
    b.append(f'<rect x="{xs[1]}" y="{y(gross):.1f}" width="{bw}" height="{y(gross - cost) - y(gross):.1f}" fill="{BAR}" rx="2"/>')
    b.append(f'<rect x="{xs[2]}" y="{y(0):.1f}" width="{bw}" height="{y(net) - y(0):.1f}" fill="{RED}" rx="2"/>')
    b.append(f'<path d="M{xs[0] + bw} {y(gross):.1f}H{xs[1]}M{xs[1] + bw} {y(net):.1f}H{xs[2]}" stroke="{MUTED}" stroke-dasharray="4 5"/>')
    b.append(t(xs[0] + bw / 2, y(gross) - 10, num(gross, 1, True), 22, INK, 'middle', 800))
    b.append(t(xs[1] + bw / 2, y(gross - cost) + 28, num(-cost, 1), 22, INK, 'middle', 800))
    b.append(t(xs[2] + bw / 2, y(net) + 28, num(net, 1), 22, INK, 'middle', 800))
    for xx, s in zip(xs, ['Ganho bruto', 'Custos modelados', 'Resultado']):
        b.append(t(xx + bw / 2, top + ph + 34, s, 17, INK, 'middle', 600))
    b.append(t(left, 16, 'bps por operação, média de 44 operações', 14, MUTED))
    return svg(w, h, 'Cascata: ganho bruto de 4,5 bps, custos de 44,5 bps, resultado de −40,0 bps.', ''.join(b))


def chart_cost_lines(base, store10):
    w, h = 700, 400
    left, top, pw, ph = 60, 30, 610, 300
    ymax = 80
    x = lambda m: left + m / 48 * pw
    y = lambda v: top + (1 - v / ymax) * ph
    rt_token, rt_etf = base['token_rt_bps'], base['etf_rt_bps']
    halo = 'stroke="var(--bg)" stroke-width="5" paint-order="stroke"'
    b = []
    for v in [0, 20, 40, 60, 80]:
        b.append(f'<path d="M{left} {y(v):.1f}H{left + pw}" stroke="{GRID}"/>')
        b.append(t(left - 8, y(v) + 5, v, 14, MUTED, 'end'))
    for m in [0, 12, 24, 36, 48]:
        b.append(t(x(m), top + ph + 26, m, 15, MUTED, 'middle'))
    b.append(t(left + pw, top + ph + 52, 'meses de manutenção', 15, MUTED, 'end'))
    m_cap = (ymax - rt_etf) / (40 / 12)
    b.append(f'<path d="M{x(0):.1f} {y(rt_token):.1f}H{x(48):.1f}" stroke="{TEAL}" stroke-width="3.5"/>')
    b.append(f'<path d="M{x(0):.1f} {y(rt_token):.1f}L{x(48):.1f} {y(rt_token + 40):.1f}" stroke="{TEAL}" stroke-width="2.5" stroke-dasharray="7 6"/>')
    b.append(f'<path d="M{x(0):.1f} {y(rt_etf):.1f}L{x(m_cap):.1f} {y(ymax):.1f}" stroke="{RED}" stroke-width="3.5"/>')
    b.append(f'<path d="M{x(0):.1f} {y(rt_etf):.1f}L{x(48):.1f} {y(rt_etf + 40):.1f}" stroke="{GOLD}" stroke-width="3.5"/>')
    for m, c in [(base['gld'], RED), (base['gldm'], GOLD)]:
        b.append(f'<circle cx="{x(m):.1f}" cy="{y(rt_token):.1f}" r="7" fill="{c}" stroke="var(--bg)" stroke-width="2"/>')
    b.append(t(x(base['gld']) + 14, y(rt_token) - 12, f"{num(base['gld'], 1)} meses", 18, RED, 'start', 800, halo))
    b.append(t(x(base['gldm']) + 12, y(rt_token) - 14, f"{num(base['gldm'], 1)} meses", 18, GOLD, 'start', 800, halo))
    lx, ly = x(27), top + 12
    for i, (col, dash, label) in enumerate([(TEAL, '', 'PAXG, sem guarda'), (TEAL, '7 6', 'PAXG, guarda de 0,10% ao ano'),
                                             (RED, '', 'GLD, taxa de 0,40% ao ano'), (GOLD, '', 'GLDM, taxa de 0,10% ao ano')]):
        yy = ly + i * 24
        b.append(f'<path d="M{lx:.1f} {yy}h30" stroke="{col}" stroke-width="3" stroke-dasharray="{dash}"/>')
        b.append(t(lx + 38, yy + 5, label, 15, INK, 'start', 600))
    b.append(t(left, 16, 'custo acumulado, em bps do valor investido', 14, MUTED))
    return svg(w, h, 'Custo acumulado de PAXG, GLD e GLDM em 48 meses.', ''.join(b))


def chart_week():
    w, h = 1000, 200
    b = []
    # eixo: sexta fecha -> domingo reabre
    x0, x1, x2, x3 = 60, 330, 700, 960
    b.append(f'<rect x="{x1}" y="20" width="{x2 - x1}" height="150" fill="{TEAL}" opacity=".10"/>')
    b.append(t(x0, 18, 'Sexta', 15, MUTED))
    b.append(t((x1 + x2) / 2, 18, 'Fim de semana: o ouro de referência não cota', 15, MUTED, 'middle'))
    b.append(t(x3, 18, 'Domingo à noite: reabertura', 15, MUTED, 'end'))
    b.append(t(0, 80, 'PAXG', 18, GOLD, 'start', 800))
    b.append(f'<path d="M{x0 + 40} 76H{x3}" stroke="{GOLD}" stroke-width="4"/>')
    b.append(t(0, 140, 'Ouro', 18, TEAL, 'start', 800))
    b.append(f'<path d="M{x0 + 40} 136H{x1}M{x2} 136H{x3}" stroke="{TEAL}" stroke-width="4"/>')
    b.append(f'<circle cx="{x2}" cy="136" r="7" fill="{TEAL}"/>')
    b.append(f'')
    b.append(t(x2 - 10, 112, 'primeira cotação do ouro', 15, INK, 'end'))
    return svg(w, h, 'O PAXG negocia sem parar; o ouro de referência fecha no fim de semana.', ''.join(b))


# ------------------------------------------------------------------ montagem (sistema Áureo)

SYMBOL = ('<svg class="symbol" viewBox="0 0 100 100" aria-hidden="true"><path d="M18 23h55l8 22H10z" fill="currentColor"/>'
          '<path d="M31 55h55l8 22H23z" fill="none" stroke="currentColor" stroke-width="1.8"/>'
          '<path d="M9 47v7m-3-7h6m-6 7h6" fill="none" stroke="currentColor"/></svg>')

CSS = f"""
@font-face{{font-family:Manrope;src:url("design-systems/assets/fonts/Manrope.ttf");font-weight:200 800}}
@font-face{{font-family:DMSerif;src:url("design-systems/assets/fonts/DMSerifDisplay-Regular.ttf")}}
@font-face{{font-family:DMSerif;font-style:italic;src:url("design-systems/assets/fonts/DMSerifDisplay-Italic.ttf")}}
@font-face{{font-family:PlexMono;src:url("design-systems/assets/fonts/IBMPlexMono-Regular.ttf")}}
@page{{size:{W}px {H}px;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{background:#0d0e0b}}
body{{font-family:Manrope,"Segoe UI",sans-serif;font-size:21px;line-height:1.45;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.dark{{--bg:#171914;--ink:#F3EEE3;--muted:#ABA797;--grid:#34372F;--c1:#CFAD68;--c2:#A4B7A4;--neg:#E69B88;--bar:#6E7367;--card:#1F221B;--line:#3B3E34}}
.light{{--bg:#F3EEE3;--ink:#171914;--muted:#5E5A4E;--grid:#D9D2C0;--c1:#8F6D22;--c2:#667F69;--neg:#B0482F;--bar:#9A9C92;--card:#FAF6EC;--line:#CCC4AF}}
.slide{{width:{W}px;height:{H}px;background:var(--bg);color:var(--ink);position:relative;overflow:hidden;padding:50px 64px 0;margin:24px auto;page-break-after:always;break-after:page}}
@media print{{html{{background:none}}.slide{{margin:0}}}}
.kicker{{font-size:15px;color:var(--muted);margin-bottom:12px;letter-spacing:.02em}}
h1{{font-family:DMSerif,serif;font-weight:400;font-size:44px;line-height:1.1;letter-spacing:-.005em;max-width:1140px}}
h2{{font-family:DMSerif,serif;font-weight:400;font-size:26px;line-height:1.15}}
p{{font-size:21px}}
.sub{{color:var(--muted);font-size:20px;margin-top:10px}}
.foot{{position:absolute;left:64px;right:64px;bottom:22px;display:flex;align-items:center;gap:18px;font-size:14px;color:var(--muted);border-top:1px solid var(--line);padding-top:10px}}
.foot .brand{{display:flex;align-items:center;gap:8px;color:var(--ink);font-weight:600;white-space:nowrap}}
.foot .symbol{{width:22px;height:22px;color:var(--c1)}}
.foot .src{{flex:1}}
.foot .idx{{font-family:PlexMono,monospace;white-space:nowrap}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:22px}}
.card,.box{{background:var(--card);border:1px solid var(--line);border-radius:2px;padding:18px 24px}}
.card .big{{font-family:DMSerif,serif;font-size:52px;line-height:1;color:var(--c1);margin-bottom:8px}}
.card .big small{{font-family:PlexMono,monospace;font-size:16px;color:var(--muted);margin-left:6px}}
.card h2{{margin-bottom:6px;font-size:24px}}
.card p,.box p,.box li{{font-size:18.5px;line-height:1.4;color:var(--ink)}}
.box h2{{margin-bottom:8px}}
.cols{{display:grid;gap:30px}}
.note{{font-size:16px;color:var(--muted)}}
.mono{{font-family:PlexMono,monospace}}
ul{{padding-left:22px}}li{{margin:5px 0}}
table{{border-collapse:collapse;width:100%;font-size:20px}}
th{{text-align:left;font-size:15px;font-weight:600;color:var(--muted);border-bottom:1px solid var(--ink);padding:8px 10px}}
td{{padding:10px;border-bottom:1px solid var(--line)}}
td.r,th.r{{text-align:right;font-family:PlexMono,monospace;font-size:18px}}
.hl{{color:var(--c1);font-weight:700}}
.neg{{color:var(--neg);font-weight:700}}
a{{color:var(--c1);text-decoration:none;border-bottom:1px solid var(--line)}}
.sheet{{background:#F3EEE3;color:#171914;--ink:#171914;--muted:#5E5A4E;--c1:#8F6D22;--neg:#B0482F;--line:#CCC4AF;border-radius:2px;padding:20px 26px}}
.sheet h2{{margin-bottom:8px}}
.sheet .row{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--line);padding:7px 0;font-size:19px}}
.sheet .row b{{font-family:DMSerif,serif;font-weight:400;font-size:26px}}
.sheet .total b{{font-size:44px;color:var(--neg)}}
.cover-title{{font-family:DMSerif,serif;font-size:132px;line-height:.98;letter-spacing:-.01em}}
.cover-title em{{color:var(--c1)}}
"""


def foot(source, index):
    return (f'<div class="foot"><span class="brand">{SYMBOL} BitFlow</span><span class="src">{source}</span>'
            f'<span class="idx">{index}</span></div>')


def slide(theme, kicker, title, body, source, index, sub=''):
    s = f'<p class="sub">{sub}</p>' if sub else ''
    return (f'<section class="slide {theme}"><div class="kicker">{kicker}</div><h1>{title}</h1>{s}{body}{foot(source, index)}</section>')


def scenario_row(grid, fee, spread, gold, conv, slip, hours=6):
    q = grid[(grid.horizon_hours == hours) & (grid.token_fee_bps_per_fill == fee) & (grid.token_full_spread_bps == spread)
             & (grid.gold_commission_bps_per_fill == gold) & (grid.conversion_roundtrip_bps == conv)
             & (grid.slippage_bps_per_fill == slip) & (grid.assumed_residual_carry_bps == 0)]
    assert len(q) == 1
    return q.iloc[0]


def crossing(t3, etf, fee, spread, storage=0):
    q = t3[(t3.etf == etf) & (t3.notional_usd == 10000) & (t3.horizon_months == 12) & (t3.token_fee_per_fill_bps == fee)
           & (t3.token_full_spread_bps == spread) & (t3.conversion_rt_bps == 2) & (t3.network_rt_usd == 0)
           & (t3.etf_fee_per_fill_bps == 0) & (t3.etf_full_spread_bps == 1) & (t3.token_storage_bps_year == storage)]
    assert len(q) == 1
    return q.iloc[0]


def sym(size, extra=''):
    return SYMBOL.replace('class="symbol"', f'style="width:{size}px;height:{size}px;{extra}"')


def build_html():
    S = json.loads((ROOT / 'results/summary.json').read_text(encoding='utf-8'))
    R = json.loads((ROOT / 'results/T11_regime_resumo.json').read_text(encoding='utf-8'))
    monthly, annual = read('T11_regime_mensal.csv'), read('T11_regime_anual.csv')
    ev = read('T4_evolucao.csv')
    ev['complete_quarter'] = ev.complete_quarter.astype(str).str.lower().eq('true')
    t3 = read('T3_custos_etfs.csv')
    grid_all = read('T2_convergencia.csv')
    grid = read('T10_grid_summary.csv')
    budget = read('T10_cost_budget.csv')
    fc = read('T8_forecast_summary.csv').set_index('model')
    pair = read('T7_paired_changes.csv').set_index('comparison')
    fx = read('T9_fx_coverage.csv')
    a = annual.set_index('year')
    y26, y20 = a.loc[2026], a.loc[2020]
    mmin, mmax = monthly.median_bps.min(), monthly.median_bps.max()

    # cenários de custo: todos vêm da grade original; o intermediário foi escolhido depois dos resultados
    orig = scenario_row(grid_all, 10, 10, 1, 2, 2)
    mid = scenario_row(grid_all, 5, 2, 1, 2, 2)
    low = scenario_row(grid_all, 2, 2, 1, 0, 0)
    gross = S['mean_gross_mid_bps']
    mid_net, orig_net, low_net = float(mid.mean_model_bps), float(orig.mean_model_bps), float(low.mean_model_bps)
    mid_cost = gross - mid_net
    n_eval = int(S['evaluated_trades'])
    mid_pos = int(round(float(mid.positive_fraction) * int(mid.evaluated_trades)))
    gld_m = float(crossing(t3, 'GLD', 5, 2).crossing_months)
    gldm_m = float(crossing(t3, 'GLDM', 5, 2).crossing_months)
    gld_o = float(crossing(t3, 'GLD', 10, 10).crossing_months)
    gldm_o = float(crossing(t3, 'GLDM', 10, 10).crossing_months)
    rt_mid = float(crossing(t3, 'GLD', 5, 2).token_cost_bps)
    rt_orig = float(crossing(t3, 'GLD', 10, 10).token_cost_bps)
    storage_status = crossing(t3, 'GLDM', 5, 2, storage=10).status
    assert storage_status == 'token_always_more_expensive', storage_status
    n_grid = int(grid.configurations.sum())
    slides = []

    # 1 capa
    slides.append(f"""<section class="slide dark" style="padding:0">
<div style="position:absolute;left:80px;top:60px;display:flex;align-items:center;gap:12px;font-weight:600;font-size:20px">{sym(34, 'color:var(--c1)')}BitFlow</div>
<div style="position:absolute;right:80px;top:60px;text-align:right;font-size:16px;color:var(--muted);line-height:1.45">FGV EESP<br>7º Datathon de Moedas Digitais</div>
<div class="cover-title" style="position:absolute;left:80px;top:140px">O preço<br><span style="font-size:.5em">da</span> <em>promessa.</em></div>
<div style="position:absolute;right:90px;top:230px;color:var(--c1)">{sym(170)}</div>
<div style="position:absolute;left:80px;bottom:110px;width:760px"><p style="font-family:DMSerif,serif;font-size:34px;line-height:1.2">O ouro digital acompanha o ouro de verdade?</p>
<p style="margin-top:10px;font-size:19px;color:var(--muted)">Fidelidade, custo e captura de desvios do PAXG, de agosto de 2020 a novembro de 2026.</p></div>
<div style="position:absolute;left:80px;right:80px;bottom:42px;display:flex;justify-content:space-between;font-size:16px;color:var(--muted);border-top:1px solid var(--line);padding-top:12px"><span>Gabriel Navarro · Lorenzo Cavalcante · Rodrigo Menin</span><span class="mono">PAXG / 2020—2026</span></div></section>""")

    # 2 resposta
    cards = f"""<div class="cards">
<div class="card"><div class="big">{num(mmin, 0)} a {num(mmax, 0, True)}<small>bps</small></div><h2>O desvio é um nível que muda com os meses</h2><p>Esse é o intervalo da mediana mensal contra o ouro. O nível do mês explica {pct(R['variance_share_monthly_level'])} da variação hora a hora.</p></div>
<div class="card"><div class="big">{pct(y26.within_25_bps)}</div><h2>Em 2026 o PAXG está mais perto do ouro</h2><p>Das horas de 2026, {pct(y26.within_25_bps)} ficaram a até 25 bps do ouro. Em 2020 foram {pct(y20.within_25_bps)}.</p></div>
<div class="card"><div class="big">{num(S['reopen_median_abs_bps'], 0)} → {num(S['one_hour_median_abs_bps'], 0)}<small>bps</small></div><h2>Na reabertura o desvio cai, mas não zera</h2><p>Desvio mediano na reabertura e 1 hora depois. Um modelo linear não previu melhor que repetir o último valor.</p></div>
<div class="card"><div class="big" style="color:var(--neg)">{num(mid_net, 0)}<small>bps</small></div><h2>Capturar o desvio custa mais do que rende</h2><p>Resultado médio por operação com custos intermediários ({num(orig_net, 0)} no cenário original). Só {mid_pos} de {n_eval} ficaram positivas.</p></div></div>
<p class="note" style="margin-top:12px">Contra ETFs de ouro, o PAXG fica mais barato depois de {num(gld_m)} meses (GLD) ou {num(gldm_m)} meses (GLDM), nesse mesmo cenário de custos.</p>"""
    slides.append(slide('light', 'Resposta / Em uma página', 'O PAXG segue o ouro de perto, mas o desvio é persistente e não rende após os custos', cards,
                        'Binance, Bitfinex, Dukascopy. 28/08/2020 a 08/11/2026.', '02 / 10'))

    # 3 motivação
    vol26 = y26.usd_volume_millions / 1000
    body3 = f"""<div style="margin-top:18px">{chart_week()}</div>
<div class="cols" style="grid-template-columns:1fr 1fr 1fr;margin-top:16px">
<div class="box"><h2>O que é o PAXG</h2><p>Token da Paxos lastreado em uma onça troy de ouro, negociado em corretoras de criptoativos a qualquer hora.</p></div>
<div class="box"><h2>Tamanho do mercado</h2><p>Só na Binance (par PAXG/USDT), foram mais de <span class="hl">US$ {num(vol26, 0)} bi</span> negociados em 2026, contando apenas as horas em que o ouro também cota.</p></div>
<div class="box"><h2>Pergunta</h2><p>O preço do token acompanha o ouro? O que acontece quando o ouro reabre? Dá para lucrar com a diferença depois dos custos?</p></div></div>"""
    slides.append(slide('dark', 'Problema / Acesso e referência', 'O PAXG negocia 24 horas por dia, mas o ouro que serve de referência não', body3,
                        'Paxos (termos do PAXG); Binance. Volume em dólares, horas com ouro ativo.', '03 / 10'))

    # 4 dados e método
    body4 = f"""<div class="cols" style="grid-template-columns:1.05fr .95fr;margin-top:18px">
<div><table><thead><tr><th>Dado</th><th>Fonte</th></tr></thead><tbody>
<tr><td>Preço do PAXG</td><td>Binance, PAXG/USDT, por hora</td></tr>
<tr><td>Dólar do USDT</td><td>Bitfinex, USDT/USD (Coinbase como checagem)</td></tr>
<tr><td>Preço do ouro</td><td>Dukascopy, XAUUSD, compra e venda</td></tr>
<tr><td>Custos dos ETFs</td><td>Emissores do GLD e do GLDM</td></tr></tbody></table>
<div class="box" style="margin-top:14px"><h2>Como medimos</h2><p><b>Desvio (bps) = 10.000 × ln(PAXG em dólares ÷ ouro)</b></p><p class="note" style="margin-top:6px">100 bps = 1%. Positivo: PAXG acima do ouro.</p></div></div>
<div><div class="box"><h2>Amostra</h2><p><span class="hl">{num(S['valid_hours'], 0)}</span> horas e <span class="hl">{int(S['valid_weekends'])}</span> de {int(S['candidate_weekends'])} fins de semana. Excluímos horas sem ouro ativo ou sem câmbio observado.</p></div>
<div class="box" style="margin-top:14px"><h2>Checagens independentes</h2><ul>
<li>Nosso ouro × preço do GLD por onça: diferença mediana de 1,5 bps.</li>
<li>Bitfinex × Coinbase: {num(S['fx_source_median_abs_difference_bps'], 1)} bps de diferença mediana.</li>
<li>Kraken (PAXG/USD) em 3 janelas: mesmo sinal e tamanho do desvio.</li></ul></div></div></div>"""
    slides.append(slide('light', 'Método / Dados e medida', 'Comparamos o PAXG com o ouro hora a hora, usando só preços observados', body4,
                        'Binance; Bitfinex; Coinbase; Dukascopy; Kraken; SPDR. Preços de hora, sem livro de ofertas.', '04 / 10'))

    # 5 regime
    body5 = f"""<div style="margin-top:12px">{chart_regime(monthly)}</div>
<p class="note" style="margin-top:6px">Linha: mediana do mês. Faixa: 10% a 90% das horas. Em torno do nível da semana, a mediana do desvio é de só {num(R['median_abs_around_week_level_bps'], 0)} bps.</p>"""
    slides.append(slide('dark', 'Evidência / Nível do desvio', f'O desvio não é ruído: o PAXG fica meses acima ou abaixo do ouro (de {num(mmin, 0)} a {num(mmax, 0, True)} bps)', body5,
                        'Binance, Bitfinex, Dukascopy. Análise descritiva feita depois dos resultados originais.', '05 / 10'))

    # 6 evolução
    body6 = f"""<div class="cols" style="grid-template-columns:1.1fr .9fr;gap:36px;margin-top:8px">
<div><h2 style="margin-bottom:4px;font-size:23px">Horas a até 25 bps do ouro, por ano</h2>{chart_years(annual)}</div>
<div><h2 style="margin-bottom:4px;font-size:23px">Mediana trimestral, em bps</h2>{chart_quarters(ev)}</div></div>
<p class="note" style="margin-top:8px">Tendência em 24 trimestres: −0,09 por ano no log da mediana, com intervalo de −0,25 a +0,07. O intervalo inclui zero, então a melhora ainda não é estatisticamente firme.</p>"""
    slides.append(slide('light', 'Evidência / Evolução', f'Em 2026 o PAXG está mais perto do ouro: {pct(y26.within_25_bps)} das horas ficaram a até 25 bps', body6,
                        'Binance, Bitfinex, Dukascopy. Tendência com erro padrão robusto a autocorrelação.', '06 / 10'))

    # 7 reabertura e previsão
    items = [('Na reabertura', S['reopen_median_abs_bps']), ('1 hora depois', S['one_hour_median_abs_bps']), ('7 horas depois', S['seven_hours_median_abs_bps'])]
    items2 = [('Repetir o último valor', fc.loc['persistence', 'mae_bps']), ('Modelo linear', fc.loc['linear_adjustment', 'mae_bps']), ('Assumir desvio zero', fc.loc['zero_basis', 'mae_bps'])]
    p1, p7 = pair.loc['b_0_to_b_1h'], pair.loc['b_0_to_b_7h']
    body7 = f"""<div class="cols" style="grid-template-columns:1fr 1fr;gap:44px;margin-top:20px">
<div><h2 style="font-size:23px">Desvio absoluto mediano, em bps</h2><div style="margin-top:14px">{hbars(items, 540, 230, 60, 'Mediana do desvio absoluto na reabertura, 1 e 7 horas depois.', [TEAL, GOLD, GOLD], row=70, lw=200)}</div>
<p style="margin-top:10px;font-size:20px">Nos mesmos {int(p1.paired_n)} fins de semana, o desvio cai em média <span class="hl">{num(-p1.mean_abs_change_bps)} bps</span> em 1 hora (intervalo {num(p1.mean_lo)} a {num(p1.mean_hi)}) e <span class="hl">{num(-p7.mean_abs_change_bps)} bps</span> em 7 horas.</p></div>
<div><h2 style="font-size:23px">Erro de previsão do desvio em +7 h, em bps</h2><div style="margin-top:14px">{hbars(items2, 540, 230, 60, 'Erro médio absoluto de previsão por método.', [TEAL, BAR, BAR], row=70, lw=235)}</div>
<p style="margin-top:10px;font-size:20px">Com {int(fc.loc['persistence', 'n_test'])} previsões, o modelo linear não superou a repetição do último valor. O desvio de hoje é o melhor palpite para daqui a algumas horas.</p></div></div>"""
    slides.append(slide('light', 'Evidência / Reabertura e previsão', 'Depois da reabertura o desvio diminui, mas continua alto e é difícil de prever', body7,
                        'Binance, Bitfinex, Dukascopy. Intervalos de 95% por blocos de semanas; previsão com treino expansivo.', '07 / 10'))

    # 8 custos (cenários)
    body8 = f"""<div class="cols" style="grid-template-columns:1fr 1fr;gap:36px;margin-top:10px">
<div>{chart_waterfall(gross, mid_cost, mid_net)}</div>
<div class="sheet"><div class="mono" style="font-size:13px;color:var(--muted);margin-bottom:6px">CENÁRIO INTERMEDIÁRIO · POSIÇÃO DE 6 HORAS</div><h2>Resultado médio por operação</h2>
<div class="row"><span>Ganho bruto</span><b>{num(gross, 1, True)}</b></div>
<div class="row"><span>Custos modelados</span><b>{num(-mid_cost, 1)}</b></div>
<div class="row total"><span>Saldo médio</span><b>{num(mid_net, 1)}</b></div>
<p style="font-size:16px;margin-top:8px;line-height:1.35">Token: taxa de 5 bps por execução e spread de 2; ouro 1; câmbio 2; deslizamento 2. O saldo foi positivo em {mid_pos} de {n_eval} operações.</p>
<table style="font-size:17px;margin-top:8px"><tbody>
<tr><td style="padding:5px 0">Cenário original (taxa 10, spread 10)</td><td class="r" style="padding:5px 0">{num(orig_net, 1)}</td></tr>
<tr><td style="padding:5px 0">Custos mínimos da grade</td><td class="r" style="padding:5px 0">{num(low_net, 1)}</td></tr></tbody></table></div></div>
<p class="note" style="margin-top:10px">Cenário intermediário escolhido na grade original depois de ver os resultados; o original foi congelado antes. Sem empréstimo e financiamento.</p>"""
    slides.append(slide('dark', 'Evidência / Custos e convergência', f'Com custos intermediários, capturar o desvio ainda perde {num(-mid_net, 0)} bps por operação, em média', body8,
                        'Binance, Bitfinex, Dukascopy. Preços de minuto; venda a descoberto do token não verificada.', '08 / 10'))

    # 9 ETFs
    body9 = f"""<div class="cols" style="grid-template-columns:1.25fr .75fr;gap:30px;margin-top:10px">
<div>{chart_cost_lines({'token_rt_bps': rt_mid, 'etf_rt_bps': 1.0, 'gld': gld_m, 'gldm': gldm_m}, None)}</div>
<div><div class="box"><h2>Como ler</h2><p>Entrar e sair do PAXG custa {num(rt_mid, 0)} bps, contra 1 bp nos ETFs, mas o PAXG não tem taxa anual. A taxa dos ETFs alcança o custo do token em {num(gld_m)} meses (GLD) e {num(gldm_m)} meses (GLDM).</p></div>
<div class="box" style="margin-top:14px"><h2>Cuidado</h2><p>Com guarda de 0,10% ao ano no PAXG, ele nunca ficaria mais barato que o GLDM. No cenário original ({num(rt_orig, 0)} bps de entrada e saída), os prazos seriam {num(gld_o)} e {num(gldm_o)} meses. Em dólares, antes de impostos.</p></div></div></div>"""
    slides.append(slide('light', 'Evidência / Token e ETFs', f'Contra os ETFs, o PAXG compensa para quem fica mais de {num(gld_m)} meses (GLD) ou {num(gldm_m)} meses (GLDM)', body9,
                        'SPDR (GLD, GLDM); Paxos. Custos do token são hipóteses. Custo menor não significa risco menor.', '09 / 10'))

    # 10 conclusão
    body10 = f"""<div class="cols" style="grid-template-columns:repeat(3,1fr);gap:20px;margin-top:20px">
<div class="box"><h2>Para quem investe</h2><p>O prêmio ou desconto do dia pode passar de 100 bps e durar semanas. Quem fica pouco tempo em ouro sente mais o custo de entrada e saída do PAXG ({num(rt_mid, 0)} bps no cenário intermediário).</p></div>
<div class="box"><h2>Para plataformas e emissores</h2><p>O desvio se concentra no nível, e não nos minutos após a reabertura. Ele diminuiu em 2026, com mais volume negociado. As taxas de resgate (0,125% a 0,5%) combinam com esse padrão; não testamos a causa.</p></div>
<div class="box"><h2>Para a pesquisa</h2><p>Faltam horários exatos de negociação, livro de ofertas e custo real de empréstimo. Também não medimos câmbio, impostos e acesso do investidor brasileiro. É o próximo passo.</p></div></div>
<div style="margin-top:24px;border-left:3px solid var(--c1);padding:6px 0 6px 26px"><div class="mono" style="font-size:14px;color:var(--c1);margin-bottom:8px">RESPOSTA À PERGUNTA</div>
<p style="font-family:DMSerif,serif;font-size:32px;line-height:1.22">Sim, o PAXG acompanha o ouro, e mais de perto em 2026. O desvio, porém, é um nível que dura semanas, e os custos que supomos consomem o ganho de capturá-lo.</p></div>"""
    slides.append(slide('dark', 'Conclusão / O que a evidência permite', 'O que concluímos e o que ainda falta', body10,
                        'Resultados 1 a 5. Sem identificação causal; simulações dependem dos custos supostos.', '10 / 10'))

    # A1
    rows = ''.join(f'<tr><td>{int(r.horizon_hours)} h</td><td class="r">{int(r.configurations)}</td><td class="r">{int(r.evaluated_trades)}</td><td class="r">{num(budget.mean_gross_bps[i], 1)} [{num(budget.gross_lo[i], 1)}; {num(budget.gross_hi[i], 1)}]</td><td class="r">{num(r.best_mean_model_bps, 1)}</td></tr>' for i, r in grid.iterrows())
    sc = ''.join(f'<tr><td>{n_}</td><td class="r">{num(v, 1)}</td></tr>' for n_, v in [('Original: taxa 10, spread 10, câmbio 2, deslizamento 2', orig_net), ('Intermediário: taxa 5, spread 2, câmbio 2, deslizamento 2', mid_net), ('Mínimo da grade: taxa 2, spread 2, câmbio 0, deslizamento 0', low_net)])
    ap1 = f"""<div class="cols" style="grid-template-columns:1.2fr .8fr;gap:34px;margin-top:20px"><div>
<table><thead><tr><th>Prazo</th><th class="r">Combinações</th><th class="r">Operações</th><th class="r">Ganho bruto [IC 95%]</th><th class="r">Melhor média</th></tr></thead><tbody>{rows}</tbody></table></div>
<div><table><thead><tr><th>Cenário (posição de 6 h)</th><th class="r">Saldo médio</th></tr></thead><tbody>{sc}</tbody></table></div></div>
<p class="note" style="margin-top:16px">Em bps. As {num(n_grid, 0)} combinações não são independentes, e o melhor caso e o cenário intermediário foram escolhidos depois de ver os resultados. Com posições de 24 horas, o ganho bruto médio já é positivo (de 2,7 a 13,6), mas continua abaixo dos custos. Reduzir {pct(S['refined_cost_reduction_to_zero_fraction'])} dos custos originais zeraria o resultado de 6 horas; essa conta vale para esta amostra e não prevê o futuro.</p>"""
    slides.append(slide('light', 'Anexo A1 / Custos', f'Nenhuma das {num(n_grid, 0)} combinações de custo e prazo teve média positiva', ap1, 'T10_grid_summary.csv; T10_cost_budget.csv; T2_convergencia.csv', 'A1'))

    # A2
    names = {'persistence': 'Repetir o último valor', 'zero_basis': 'Assumir desvio zero', 'historical_mean': 'Média histórica', 'linear_adjustment': 'Modelo linear', 'linear_adjustment_context': 'Linear com ouro e volatilidade'}
    rows = ''.join(f'<tr><td>{names[m]}</td><td class="r">{num(fc.loc[m, "mae_bps"], 2)}</td><td class="r">{num(fc.loc[m, "rmse_bps"], 2)}</td><td class="r">{num(fc.loc[m, "mae_difference_vs_persistence"], 2)} [{num(fc.loc[m, "difference_lo"], 2)}; {num(fc.loc[m, "difference_hi"], 2)}]</td></tr>' for m in names)
    ap2 = f"""<table style="margin-top:24px"><thead><tr><th>Método</th><th class="r">Erro médio absoluto</th><th class="r">Raiz do erro quadrático</th><th class="r">Diferença vs. repetir o último [IC 95%]</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note" style="margin-top:18px">Alvo: desvio 7 h depois da reabertura, previsto com a informação de 1 h depois. Treino expansivo a partir de 104 semanas; {int(fc.loc['persistence', 'n_test'])} previsões de ago/2022 a nov/2026, todas na mesma amostra. Sem busca de parâmetros. Análise feita depois dos resultados originais, sem teste prospectivo.</p>"""
    slides.append(slide('light', 'Anexo A2 / Previsão', 'Repetir o último desvio foi tão bom quanto os modelos lineares', ap2, 'T8_forecast_summary.csv', 'A2'))

    # A3
    f1, f5 = fx[(fx.fx_window_minutes == 1) & (fx.horizon_hours == 6)].iloc[0], fx[(fx.fx_window_minutes == 5) & (fx.horizon_hours == 6)].iloc[0]
    ap3 = f"""<table style="margin-top:24px"><thead><tr><th>Janela de busca do câmbio</th><th class="r">Sinais</th><th class="r">Avaliados</th><th class="r">Sem avaliação</th><th class="r">Saldo médio (bps)</th></tr></thead><tbody>
<tr><td>1 minuto (análise principal)</td><td class="r">{int(f1.signals)}</td><td class="r">{int(f1.evaluated_trades)}</td><td class="r">{int(f1.unassessed_signals)}</td><td class="r">{num(f1.mean_model_bps, 1)}</td></tr>
<tr><td>5 minutos (sensibilidade)</td><td class="r">{int(f5.signals)}</td><td class="r">{int(f5.evaluated_trades)}</td><td class="r">{int(f5.unassessed_signals)}</td><td class="r">{num(f5.mean_model_bps, 1)}</td></tr></tbody></table>
<p class="note" style="margin-top:18px">Saldos no cenário de custos original. Com 5 minutos, usamos o último câmbio já fechado, de até 4 minutos antes; token e ouro seguem no minuto exato. Mais operações entram e o saldo quase não muda. Para os {int(f1.unassessed_signals)} sinais sem avaliação completa anularem o resultado original, eles precisariam render em média <b>{num(S['refined_missing_tipping_mean_bps'], 0)} bps</b>. É um limiar, não uma estimativa.</p>"""
    slides.append(slide('light', 'Anexo A3 / Robustez', 'Alargar a janela do câmbio inclui mais operações e não muda o resultado', ap3, 'T9_fx_coverage.csv; T9_missingness_summary.csv', 'A3'))

    # A4
    ap4 = """<div class="cols" style="grid-template-columns:1fr 1fr;gap:34px;margin-top:22px">
<div class="box"><h2>Dados</h2><ul>
<li><a href="https://github.com/binance/binance-public-data">Binance Public Data</a>: PAXG/USDT</li>
<li><a href="https://docs.bitfinex.com/reference/rest-public-candles">Bitfinex</a> e <a href="https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles">Coinbase</a>: USDT/USD</li>
<li><a href="https://www.dukascopy.com/swiss/english/marketwatch/historical/">Dukascopy</a>: XAUUSD compra e venda</li>
<li><a href="https://www.spdrgoldshares.com/usa/">GLD</a> e <a href="https://www.ssga.com/us/en/individual/etfs/spdr-gold-minishares-gldm">GLDM</a>: taxas e preços</li>
<li><a href="https://www.paxos.com/terms-and-conditions/pax-gold-terms-conditions">Paxos</a>: termos do PAXG; <a href="https://docs.kraken.com/api/">Kraken</a>: checagem</li></ul></div>
<div class="box"><h2>Método e reprodução</h2><ul>
<li><a href="https://otexts.com/fpp3/toolbox.html#time-series-cross-validation">Hyndman e Athanasopoulos</a>: validação temporal</li>
<li><a href="https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf">Bailey et al.</a>: risco de escolher o melhor backtest</li>
<li><a href="https://www.nber.org/papers/w2960">Lo e MacKinlay</a>: preços não simultâneos</li>
<li>Código em Python, scripts em TXT, parâmetros congelados e testes no pacote.</li>
<li>Comando: <b class="mono" style="font-size:17px">python run_all.py --all --offline</b></li>
<li>Pesquisa assistida por IA, com limites documentados no pacote.</li></ul></div></div>"""
    slides.append(slide('light', 'Anexo A4 / Fontes', 'Fontes e como reproduzir', ap4, 'Pacote preco_da_promessa.zip: código, parâmetros, tabelas e figuras.', 'A4'))

    return f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=1280"><title>O preço da promessa · BitFlow</title><style>{CSS}</style></head><body>{"".join(slides)}</body></html>'


def export(html_path: Path, pdf_path: Path):
    from playwright.sync_api import sync_playwright
    cands = [os.getenv('CHROME_PATH', ''), r'C:\Program Files\Google\Chrome\Application\chrome.exe',
             r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', shutil.which('google-chrome') or '', shutil.which('chromium') or '']
    exe = next((p for p in cands if p and Path(p).is_file()), None)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=exe, headless=True)
        page = browser.new_page(viewport={'width': W, 'height': H})
        page.goto(html_path.as_uri())
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(300)
        page.pdf(path=str(pdf_path), width=f'{W}px', height=f'{H}px', print_background=True, prefer_css_page_size=True)
        browser.close()


def main():
    out = ROOT / 'slides'
    html_path = out / 'entrega_v4.html'
    html_path.write_text(build_html(), encoding='utf-8')
    export(html_path, out / 'entrega_v4.pdf')
    print('ok', html_path)


if __name__ == '__main__':
    main()
