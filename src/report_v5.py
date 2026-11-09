"""Relatório final (8 páginas) e material suplementar: moldura visual, componentes e gráficos.

Identidade: sistema Áureo da equipe (carvão, marfim, ouro, DM Serif Display, Manrope, IBM Plex Mono e o
símbolo das duas barras), com leitura densa e explicativa. Todos os números vêm de results/.
"""
from __future__ import annotations

import html
import json

import numpy as np
import pandas as pd

from .common import ROOT

W, H = 1600, 900
# paleta dos gráficos (sempre desenhados sobre painel marfim)
OURO, PAXG, CUSTO = '#A57A2A', '#5F7A62', '#B0482F'
INK, MUTED, GRID, NEUTRO = '#171914', '#6A665A', '#E2DACA', '#A9A496'
OURO_L, PAXG_L = '#EFE2C4', '#DCE5DA'
PANEL = '#FAF6EC'
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
TOTAL_MAIN = 10


# ----------------------------------------------------------------- utilitários

def num(v, d=1, sign=False):
    v = float(v)
    s = f'{abs(v):,.{d}f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    if v < 0 and s.strip('0,.') != '':
        return '−' + s
    return ('+' + s) if sign and v > 0 else s


def pct(v, d=0):
    return num(float(v) * 100, d) + '%'


def read(name):
    return pd.read_csv(ROOT / 'results' / name)


def readj(name):
    return json.loads((ROOT / 'results' / name).read_text(encoding='utf-8'))


def mlabel(ts):
    ts = pd.Timestamp(ts)
    return f'{MESES[ts.month - 1]}/{ts.year}'


def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" style="width:100%;height:auto;display:block" '
            f'role="img" aria-label="{html.escape(label, quote=True)}">{body}</svg>')


def tx(x, y, s, size=13, fill=INK, anchor='start', weight=500, extra=''):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'{extra}>{html.escape(str(s))}</text>')


HALO = f'stroke="{PANEL}" stroke-width="4" paint-order="stroke"'


def symbol(size, gold='currentColor', open_color='currentColor'):
    """Símbolo BitFlow do sistema Áureo: barra cheia (ouro) e barra vazada (token), deslocadas."""
    return (f'<svg viewBox="0 0 100 100" style="width:{size}px;height:{size}px;display:block" aria-hidden="true">'
            f'<path d="M18 23h55l8 22H10z" fill="{gold}"/><path d="M31 55h55l8 22H23z" fill="none" stroke="{open_color}" stroke-width="2.2"/></svg>')


# ----------------------------------------------------------------- gráficos

def fig_level(serie, ext):
    w, h = 940, 300
    l, r, top, bot = 58, 14, 14, 34
    pw, ph = w - l - r, h - top - bot
    lo, hi = -320, 200
    d = pd.to_datetime(serie.dia)
    t0, t1 = d.min(), d.max()
    x = lambda ts: l + (pd.Timestamp(ts) - t0).days / (t1 - t0).days * pw
    y = lambda v: top + (hi - max(lo, min(hi, v))) / (hi - lo) * ph
    b = [f'<rect x="{l}" y="{y(25):.1f}" width="{pw}" height="{y(-25) - y(25):.1f}" fill="{OURO_L}"/>']
    for v in [-300, -200, -100, 0, 100, 200]:
        b.append(f'<path d="M{l} {y(v):.1f}H{l + pw}" stroke="{INK if v == 0 else GRID}" stroke-width="{1.1 if v == 0 else 1}"/>')
        b.append(tx(l - 8, y(v) + 4, num(v, 0, True) if v else '0', 12, MUTED, 'end'))
    pts = ' '.join(f'{x(a):.1f},{y(v):.1f}' for a, v in zip(d, serie.desvio_bps))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{NEUTRO}" stroke-width="1"/>')
    pts = ' '.join(f'{x(a):.1f},{y(v):.1f}' for a, v in zip(d, serie.nivel_suavizado_bps))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{PAXG}" stroke-width="2.8"/>')
    for yr in range(t0.year + 1, t1.year + 1):
        xx = x(pd.Timestamp(f'{yr}-01-01'))
        b.append(f'<path d="M{xx:.1f} {top + ph}v5" stroke="{MUTED}"/>' + tx(xx, top + ph + 20, yr, 12, MUTED, 'middle'))
    i = serie.desvio_bps.idxmin()
    xm, ym = x(d[i]), y(serie.desvio_bps[i])
    b.append(f'<circle cx="{xm:.1f}" cy="{ym:.1f}" r="4.5" fill="{CUSTO}"/>')
    b.append(tx(xm + 10, ym + 4, f'{mlabel(d[i])}: {num(serie.desvio_bps[i], 0)} bps no dia (Kraken: {ext})', 12.5, CUSTO, 'start', 700, HALO))
    for j, dy in [(serie.nivel_suavizado_bps.idxmax(), -10), (serie.nivel_suavizado_bps.idxmin(), 18)]:
        b.append(tx(x(d[j]) + 6, y(serie.nivel_suavizado_bps[j]) + dy, f'nível em {mlabel(d[j])}: {num(serie.nivel_suavizado_bps[j], 0, True)}', 12.5, PAXG, 'start', 700, HALO))
    b.append(tx(l + pw, y(25) - 5, 'faixa de ±25 bps', 11.5, OURO, 'end', 700))
    b.append(f'<path d="M{l + 8} {top + 8}h18" stroke="{NEUTRO}"/>' + tx(l + 32, top + 12, 'desvio do dia (média 15–20 UTC)', 12, MUTED))
    b.append(f'<path d="M{l + 250} {top + 8}h18" stroke="{PAXG}" stroke-width="2.8"/>' + tx(l + 274, top + 12, 'nível estimado pelo modelo de dois componentes', 12, MUTED))
    return svg(w, h, 'Desvio diário do PAXG contra o ouro e o nível estimado, 2020 a 2026.', ''.join(b))


def fig_annual(annual):
    w, h = 470, 205
    l, top, bot = 10, 20, 30
    pw, ph = w - l - 10, h - top - bot
    n = len(annual)
    bw = pw / n * .62
    b = []
    for i, r in annual.reset_index(drop=True).iterrows():
        v = r.within_25_bps * 100
        xx = l + (i + .19) * pw / n
        yy = top + ph * (1 - v / 100)
        b.append(f'<rect x="{xx:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{top + ph - yy:.1f}" fill="{OURO if r.year == 2026 else NEUTRO}"/>')
        b.append(tx(xx + bw / 2, yy - 6, f'{num(v, 0)}%', 13, INK, 'middle', 700))
        b.append(tx(xx + bw / 2, top + ph + 18, f"{int(r.year)}{'*' if r.year in (2020, 2026) else ''}", 12, MUTED, 'middle'))
    b.append(f'<path d="M{l} {top + ph}H{w - 10}" stroke="{INK}"/>')
    return svg(w, h, 'Parcela das horas a até 25 bps do ouro, por ano.', ''.join(b))


def fig_weekend(res):
    items = [('Reabertura', res['premio_fds_media_bps']), ('1 h depois', res['variacao_media_ate_1h_bps']), ('7 h depois', res['variacao_media_ate_7h_bps'])]
    w, h = 470, 340
    l, top, ph = 50, 22, 275
    hi = 20
    y = lambda v: top + (hi - v) / hi * ph
    b = []
    for v in [0, 5, 10, 15, 20]:
        b.append(f'<path d="M{l} {y(v):.1f}H{w - 10}" stroke="{INK if v == 0 else GRID}"/>' + tx(l - 8, y(v) + 4, v, 12, MUTED, 'end'))
    bw = 92
    for i, (name, v) in enumerate(items):
        xx = l + 30 + i * 135
        b.append(f'<rect x="{xx}" y="{y(v):.1f}" width="{bw}" height="{y(0) - y(v):.1f}" fill="{PAXG if i == 0 else PAXG_L}" stroke="{PAXG}"/>')
        b.append(tx(xx + bw / 2, y(v) - 7, num(v, 1, True), 14, INK, 'middle', 800))
        b.append(tx(xx + bw / 2, y(0) + 20, name, 12.5, INK, 'middle', 600))
    med = res['premio_fds_mediana_bps']
    b.append(f'<path d="M{l + 26} {y(med):.1f}h{bw + 8}" stroke="{OURO}" stroke-width="2" stroke-dasharray="5 4"/>')
    b.append(tx(l + 30 + bw + 8, y(med) + 4, f'mediana {num(med, 1, True)}', 11.5, OURO, 'start', 700, HALO))
    return svg(w, h, 'Variação média do desvio desde o fechamento de sexta.', ''.join(b))


def fig_r2(t13):
    d = t13[t13.periodo != 'todos'].reset_index(drop=True)
    w, h = 470, 340
    l, top, ph = 44, 22, 275
    y = lambda v: top + (1 - v) * ph
    b = []
    for v in [0, .25, .5, .75, 1]:
        b.append(f'<path d="M{l} {y(v):.1f}H{w - 10}" stroke="{INK if v == 0 else GRID}"/>' + tx(l - 8, y(v) + 4, num(v, 2), 11.5, MUTED, 'end'))
    n = len(d)
    bw = (w - l - 20) / n * .6
    for i, r in d.iterrows():
        xx = l + 10 + i * (w - l - 20) / n
        b.append(f'<rect x="{xx:.1f}" y="{y(r.r2):.1f}" width="{bw:.1f}" height="{y(0) - y(r.r2):.1f}" fill="{OURO if r.periodo == "2026" else NEUTRO}"/>')
        b.append(tx(xx + bw / 2, y(r.r2) - 6, num(r.r2, 2), 12, INK, 'middle', 700))
        b.append(tx(xx + bw / 2, y(0) + 18, r.periodo, 12, MUTED, 'middle'))
    return svg(w, h, 'R² da regressão do salto de reabertura do ouro no movimento do PAXG, por ano.', ''.join(b))


def fig_waterfall(gross, cost, net):
    w, h = 520, 380
    l, top, ph = 50, 26, 300
    lo, hi = -30, 10
    y = lambda v: top + (hi - v) / (hi - lo) * ph
    b = []
    for v in [10, 0, -10, -20, -30]:
        b.append(f'<path d="M{l} {y(v):.1f}H{w - 10}" stroke="{INK if v == 0 else GRID}"/>' + tx(l - 8, y(v) + 4, num(v, 0, True) if v else '0', 12, MUTED, 'end'))
    xs, bw = [l + 30, l + 180, l + 330], 110
    b.append(f'<rect x="{xs[0]}" y="{y(gross):.1f}" width="{bw}" height="{y(0) - y(gross):.1f}" fill="{PAXG}"/>')
    b.append(f'<rect x="{xs[1]}" y="{y(gross):.1f}" width="{bw}" height="{y(gross - cost) - y(gross):.1f}" fill="{NEUTRO}"/>')
    b.append(f'<rect x="{xs[2]}" y="{y(0):.1f}" width="{bw}" height="{y(net) - y(0):.1f}" fill="{CUSTO}"/>')
    b.append(f'<path d="M{xs[0] + bw} {y(gross):.1f}H{xs[1]}M{xs[1] + bw} {y(net):.1f}H{xs[2]}" stroke="{MUTED}" stroke-dasharray="4 4"/>')
    for xx, v, lab, ty in [(xs[0], gross, 'Ganho bruto', y(gross) - 8), (xs[1], -cost, 'Custos', y(gross - cost) + 20), (xs[2], net, 'Saldo', y(net) + 20)]:
        b.append(tx(xx + bw / 2, ty, num(v, 1, True), 15, INK, 'middle', 800))
        b.append(tx(xx + bw / 2, top + ph + 24, lab, 13, INK, 'middle', 600))
    return svg(w, h, 'Cascata da operação de convergência no cenário intermediário.', ''.join(b))


def fig_rotation(curve, k):
    w, h = 960, 372
    l, r = 58, 14
    pw = w - l - r
    d = pd.to_datetime(curve.dia)
    t0, t1 = d.min(), d.max()
    x = lambda ts: l + (pd.Timestamp(ts) - t0).days / (t1 - t0).days * pw
    top1, ph1 = 14, 200
    hi1 = max(900, float(curve.ganho_acumulado_bps.max()) * 1.1)
    lo1 = min(-100, float(curve.ganho_acumulado_bps.min()))
    y1 = lambda v: top1 + (hi1 - v) / (hi1 - lo1) * ph1
    b = []
    inpos = curve.em_paxg.values
    start = None
    for i in range(len(inpos) + 1):
        on = i < len(inpos) and inpos[i] == 1
        if on and start is None:
            start = i
        if not on and start is not None:
            b.append(f'<rect x="{x(d[start]):.1f}" y="{top1}" width="{max(1, x(d[i - 1]) - x(d[start])):.1f}" height="{ph1 + 14 + 122}" fill="{PAXG_L}" opacity=".75"/>')
            start = None
    for v in range(0, int(hi1) + 1, 200):
        b.append(f'<path d="M{l} {y1(v):.1f}H{l + pw}" stroke="{INK if v == 0 else GRID}"/>' + tx(l - 8, y1(v) + 4, num(v, 0, True) if v else '0', 11.5, MUTED, 'end'))
    for col, name, dash in [(PAXG, 'ganho_acumulado_bps', ''), (OURO, 'ganho_acumulado_original_bps', '6 4')]:
        pts = ' '.join(f'{x(a):.1f},{y1(v):.1f}' for a, v in zip(d, curve[name]))
        b.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.4" stroke-dasharray="{dash}"/>')
    b.append(tx(x(d.iloc[-1]) - 4, y1(curve.ganho_acumulado_bps.iloc[-1]) - 8, f'custos intermediários: {num(curve.ganho_acumulado_bps.iloc[-1], 0, True)} bps', 12, PAXG, 'end', 700, HALO))
    b.append(tx(x(d.iloc[-1]) - 4, y1(curve.ganho_acumulado_original_bps.iloc[-1]) + 16, f'custos originais: {num(curve.ganho_acumulado_original_bps.iloc[-1], 0, True)} bps', 12, OURO, 'end', 700, HALO))
    b.append(tx(l + 6, top1 + 12, 'ganho acumulado contra manter o GLDM, bps', 12, MUTED, 'start', 500, HALO))
    top2, ph2 = top1 + ph1 + 14, 122
    lo2, hi2 = -320, 160
    y2 = lambda v: top2 + (hi2 - max(lo2, min(hi2, v))) / (hi2 - lo2) * ph2
    b.append(f'<rect x="{l}" y="{y2(k):.1f}" width="{pw}" height="{y2(-k) - y2(k):.1f}" fill="{OURO_L}"/>')
    for v in [-300, -150, 0, 150]:
        b.append(f'<path d="M{l} {y2(v):.1f}H{l + pw}" stroke="{INK if v == 0 else GRID}"/>' + tx(l - 8, y2(v) + 4, num(v, 0, True) if v else '0', 11.5, MUTED, 'end'))
    pts = ' '.join(f'{x(a):.1f},{y2(v):.1f}' for a, v in zip(d, curve.desvio_bps))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="1"/>')
    b.append(tx(l + 6, top2 + 12, f'desvio do dia, bps; faixa de ±{k} bps; fundo verde = carteira em PAXG', 12, MUTED, 'start', 500, HALO))
    for yr in range(t0.year + 1, t1.year + 1):
        b.append(tx(x(pd.Timestamp(f'{yr}-01-01')), top2 + ph2 + 18, yr, 12, MUTED, 'middle'))
    return svg(w, h, 'Ganho acumulado da rotação contra o GLDM e desvio diário.', ''.join(b))


def fig_placebo(sims, actual):
    w, h = 470, 290
    l, top, ph = 20, 20, 220
    lo, hi = -260, 160
    bins = np.arange(lo, hi + 1, 20)
    cnt, _ = np.histogram(np.clip(sims, lo, hi - 1), bins)
    x = lambda v: l + (v - lo) / (hi - lo) * (w - l - 20)
    y = lambda c: top + ph - c / cnt.max() * ph
    b = []
    for c, a0, a1 in zip(cnt, bins[:-1], bins[1:]):
        b.append(f'<rect x="{x(a0) + 1:.1f}" y="{y(c):.1f}" width="{x(a1) - x(a0) - 2:.1f}" height="{top + ph - y(c):.1f}" fill="{NEUTRO}"/>')
    b.append(f'<path d="M{l} {top + ph}H{w - 20}" stroke="{INK}"/>')
    for v in [-200, -100, 0, 100]:
        b.append(tx(x(v), top + ph + 18, num(v, 0, True) if v else '0', 12, MUTED, 'middle'))
    b.append(f'<path d="M{x(actual):.1f} {top}V{top + ph}" stroke="{PAXG}" stroke-width="3"/>')
    b.append(tx(x(actual) - 6, top + 14, f'regra: {num(actual, 0, True)}', 13, PAXG, 'end', 800, HALO))
    b.append(tx(l + 4, top + 14, f'1.000 sorteios: média {num(np.mean(sims), 0)}', 12, MUTED, 'start', 600, HALO))
    return svg(w, h, 'Distribuição do ganho anual de rotações com datas sorteadas.', ''.join(b))


def fig_costs(rt_token, rt_etf, gld, gldm):
    w, h = 520, 420
    l, top, pw, ph = 46, 24, 455, 340
    ymax = 60
    x = lambda m: l + m / 48 * pw
    y = lambda v: top + (1 - v / ymax) * ph
    b = []
    for v in [0, 20, 40, 60]:
        b.append(f'<path d="M{l} {y(v):.1f}H{l + pw}" stroke="{GRID}"/>' + tx(l - 8, y(v) + 4, v, 12, MUTED, 'end'))
    for m in [0, 12, 24, 36, 48]:
        b.append(tx(x(m), top + ph + 18, m, 12, MUTED, 'middle'))
    b.append(tx(l + pw, top + ph + 36, 'meses', 12, MUTED, 'end'))
    cap = (ymax - rt_etf) / (40 / 12)
    b.append(f'<path d="M{x(0):.1f} {y(rt_token):.1f}H{x(48):.1f}" stroke="{PAXG}" stroke-width="3"/>')
    b.append(f'<path d="M{x(0):.1f} {y(rt_etf):.1f}L{x(cap):.1f} {y(ymax):.1f}" stroke="{CUSTO}" stroke-width="3"/>')
    b.append(f'<path d="M{x(0):.1f} {y(rt_etf):.1f}L{x(48):.1f} {y(rt_etf + 40):.1f}" stroke="{OURO}" stroke-width="3"/>')
    for m, c in [(gld, CUSTO), (gldm, OURO)]:
        b.append(f'<circle cx="{x(m):.1f}" cy="{y(rt_token):.1f}" r="5.5" fill="{c}"/>')
    b.append(tx(x(gld) + 10, y(rt_token) - 9, f'{num(gld)} meses', 13, CUSTO, 'start', 800, HALO))
    b.append(tx(x(gldm) + 8, y(rt_token) + 20, f'{num(gldm)} meses', 13, OURO, 'start', 800, HALO))
    b.append(tx(x(cap) + 8, y(56), 'GLD, 0,40% ao ano', 12.5, CUSTO, 'start', 700))
    b.append(tx(x(47), y(rt_etf + 40) - 8, 'GLDM, 0,10% ao ano', 12.5, OURO, 'end', 700))
    b.append(tx(x(47), y(rt_token) - 8, f'PAXG: {num(rt_token, 0)} bps para entrar e sair', 12.5, PAXG, 'end', 700))
    b.append(tx(l, 12, 'custo acumulado, bps do valor investido', 12, MUTED))
    return svg(w, h, 'Custo acumulado do PAXG, GLD e GLDM em 48 meses.', ''.join(b))


def fig_basis_risk(t14):
    w, h = 520, 420
    l, top, ph = 46, 30, 340
    hi = 100
    y = lambda v: top + (hi - v) / hi * ph
    b = []
    for v in [0, 25, 50, 75, 100]:
        b.append(f'<path d="M{l} {y(v):.1f}H{w - 10}" stroke="{INK if v == 0 else GRID}"/>' + tx(l - 8, y(v) + 4, v, 12, MUTED, 'end'))
    gw = (w - l - 20) / len(t14)
    for i, r in t14.reset_index(drop=True).iterrows():
        x0 = l + 10 + i * gw
        bw = gw * .3
        for j, (v, c) in enumerate([(r.desvio_padrao_bps, PAXG), (r.taxa_gld_no_horizonte_bps, CUSTO), (r.taxa_gldm_no_horizonte_bps, OURO)]):
            b.append(f'<rect x="{x0 + j * bw:.1f}" y="{y(v):.1f}" width="{bw - 3:.1f}" height="{max(.8, y(0) - y(v)):.1f}" fill="{c}"/>')
        b.append(tx(x0 + bw / 2, y(r.desvio_padrao_bps) - 6, num(r.desvio_padrao_bps, 0), 12.5, INK, 'middle', 800))
        b.append(tx(x0 + 1.5 * bw, y(0) + 18, r.horizonte, 12, MUTED, 'middle'))
    lx = l + 14
    for j, (c, s) in enumerate([(PAXG, 'variação do desvio (DP)'), (CUSTO, 'taxa do GLD'), (OURO, 'taxa do GLDM')]):
        b.append(f'<rect x="{lx + j * 160}" y="{top - 22}" width="11" height="11" fill="{c}"/>' + tx(lx + j * 160 + 16, top - 12, s, 12, MUTED))
    return svg(w, h, 'Desvio-padrão da variação do desvio, por horizonte, contra as taxas dos ETFs.', ''.join(b))


def fig_week():
    """Esquema da semana: o token negocia sem parar; o ouro de referência fecha no fim de semana."""
    w, h = 700, 190
    x0, x1, x2, x3 = 70, 250, 520, 690
    b = [f'<rect x="{x1}" y="26" width="{x2 - x1}" height="140" fill="{OURO_L}"/>']
    b.append(tx(x0, 18, 'sexta', 12.5, MUTED) + tx((x1 + x2) / 2, 18, 'fim de semana: o ouro não cota', 12.5, MUTED, 'middle') + tx(x3, 18, 'domingo à noite', 12.5, MUTED, 'end'))
    b.append(tx(0, 76, 'PAXG', 15, PAXG, 'start', 800) + f'<path d="M{x0} 71H{x3}" stroke="{PAXG}" stroke-width="4"/>')
    b.append(tx(0, 136, 'Ouro', 15, OURO, 'start', 800) + f'<path d="M{x0} 131H{x1}M{x2} 131H{x3}" stroke="{OURO}" stroke-width="4"/>')
    b.append(f'<circle cx="{x2}" cy="131" r="6" fill="{OURO}"/>' + tx(x2 - 10, 158, 'reabertura: primeira cotação do ouro', 12, INK, 'end'))
    b.append(f'<path d="M{x2} 80V122" stroke="{CUSTO}" stroke-width="1.5" stroke-dasharray="3 3"/>' + tx(x2 - 8, 104, 'desvio na reabertura', 12, CUSTO, 'end', 700))
    return svg(w, h, 'O PAXG negocia sem parar; o ouro de referência fecha no fim de semana.', ''.join(b))


# ----------------------------------------------------------------- moldura e componentes

CSS = """
@font-face{font-family:Manrope;src:url("design-systems/assets/fonts/Manrope.ttf");font-weight:200 800}
@font-face{font-family:DMSerif;src:url("design-systems/assets/fonts/DMSerifDisplay-Regular.ttf")}
@font-face{font-family:DMSerif;font-style:italic;src:url("design-systems/assets/fonts/DMSerifDisplay-Italic.ttf")}
@font-face{font-family:PlexMono;src:url("design-systems/assets/fonts/IBMPlexMono-Regular.ttf")}
@page{size:1600px 900px;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html{background:#0d0e0b}
body{font-family:Manrope,Arial,sans-serif;font-size:14.5px;line-height:1.45;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{--bg:#F3EEE3;--ink:#171914;--muted:#5E5A4E;--line:#CFC6B1;--card:#FAF6EC;--gold:#A57A2A;--paxg:#5F7A62;--neg:#B0482F;
 width:1600px;height:900px;background:var(--bg);color:var(--ink);position:relative;overflow:hidden;margin:20px auto;padding:30px 56px 0;page-break-after:always;break-after:page}
.page.dark{--bg:#171914;--ink:#F3EEE3;--muted:#ABA797;--line:#3B3E34;--card:#1F221B;--gold:#CFAD68;--paxg:#A4B7A4;--neg:#E69B88}
@media print{html{background:none}.page{margin:0}}
.hd{display:flex;align-items:center;justify-content:space-between;font-family:PlexMono,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.reg{display:flex;gap:5px;margin-left:auto;margin-right:16px}.reg i{display:block;width:16px;height:3px;background:var(--line)}.reg i.on{background:var(--gold)}
h1{font-family:DMSerif,serif;font-weight:400;font-size:36px;line-height:1.12;margin-top:12px;max-width:1420px}
.rule{width:64px;height:3px;background:var(--gold);margin:12px 0 16px}
.h{font-family:PlexMono,monospace;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);margin-bottom:6px}
.h.neg{color:var(--neg)}
p{font-size:14.5px}p+p{margin-top:6px}
b{font-weight:800}
.g{color:var(--paxg)}.r{color:var(--neg)}.o{color:var(--gold)}
.grid{display:grid;gap:22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:2px;padding:11px 14px}
.card .ct{font-size:13.5px;font-weight:700;margin-bottom:5px}
.card .ct i{font-style:normal;font-family:PlexMono,monospace;font-size:12px;color:var(--gold);margin-right:8px}
.nums{display:flex;gap:18px;margin-bottom:5px}.nums div{flex:1}
.nums strong{display:block;font-family:DMSerif,serif;font-weight:400;font-size:30px;line-height:1.05}
.nums span{display:block;font-family:PlexMono,monospace;font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);line-height:1.3;margin-top:2px}
.card p{font-size:13px;line-height:1.42}
.fig{background:#FAF6EC;border:1px solid #D9D0BA;border-radius:2px;padding:10px 12px 6px;color:#171914}
.cap{margin-top:7px;font-family:DMSerif,serif;font-size:15.5px;line-height:1.25}
.cap i{font-style:normal;font-family:PlexMono,monospace;font-size:11.5px;color:var(--gold);margin-right:8px;letter-spacing:.06em}
.capd{font-size:12px;color:var(--muted);line-height:1.35;margin-top:2px}
.rail{display:grid;grid-template-columns:repeat(5,1fr);gap:26px;border-top:1px solid var(--line);margin-top:14px;padding-top:14px}
.st{position:relative}
.st:before{content:"";position:absolute;top:-20px;left:0;width:11px;height:11px;border-radius:50%;background:var(--gold);box-shadow:0 0 0 4px var(--bg)}
.st .sn{font-family:PlexMono,monospace;font-size:11.5px;color:var(--gold);letter-spacing:.08em}
.st h3{font-family:DMSerif,serif;font-weight:400;font-size:19px;line-height:1.15;margin:1px 0 4px}
.st p{font-size:13px;line-height:1.42}
.st .k{font-family:PlexMono,monospace;font-size:13px;border-left:2px solid var(--gold);padding:1px 0 1px 8px;margin-top:6px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{text-align:left;font-family:PlexMono,monospace;font-weight:400;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:6px 8px;border-bottom:1px solid var(--ink)}
td{padding:6px 8px;border-bottom:1px solid var(--line)}
td.n,th.n{text-align:right;font-family:PlexMono,monospace;white-space:nowrap}
tr.hl td{background:rgba(165,122,42,.13);font-weight:700}
table.tight td{padding:3px 6px;font-size:11.5px}table.tight th{padding:4px 6px;font-size:10px}
table.tighter td{padding:2px 6px;font-size:11px}
.risk{border-top:1px solid var(--line);padding-top:8px}
.risk .lab{font-family:PlexMono,monospace;font-size:11px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
.risk h4{font-size:14px;font-weight:800;margin:2px 0}
.risk strong{display:block;font-family:DMSerif,serif;font-weight:400;font-size:24px;line-height:1.1}
.risk small{display:block;font-family:PlexMono,monospace;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.risk p{font-size:12.8px;line-height:1.4}
.call{border-left:3px solid var(--gold);padding:4px 0 4px 16px}
.call p{font-size:14.5px}
.call.serif p{font-family:DMSerif,serif;font-size:19px;line-height:1.3}
.box{border-left:3px solid var(--gold);padding:4px 0 4px 16px}
.box.gold{border-color:var(--gold)}
.sheet{--ink:#171914;--muted:#5E5A4E;--line:#CFC6B1;--card:#FFFFFF;--gold:#A57A2A;--paxg:#5F7A62;--neg:#B0482F;background:#F3EEE3;color:#171914;border-radius:2px;padding:20px 24px}
.roadrow{display:grid;grid-template-columns:36px 1fr 220px;gap:12px;align-items:baseline;border-top:1px solid var(--line);padding:8px 0}
.roadrow .n{font-family:PlexMono,monospace;font-size:12px;color:var(--gold)}
.roadrow h3{font-family:DMSerif,serif;font-weight:400;font-size:18px;line-height:1.2}
.roadrow p{font-size:12.8px;color:var(--muted);line-height:1.35}
.roadrow .v{font-family:PlexMono,monospace;font-size:13px;text-align:right}
.ft{position:absolute;left:56px;right:56px;bottom:16px;display:flex;align-items:center;gap:16px;border-top:1px solid var(--line);padding-top:8px;font-size:11.5px;color:var(--muted)}
.ft .brand{display:flex;align-items:center;gap:7px;color:var(--ink);font-weight:700;white-space:nowrap}
.ft .src{flex:1}
.ft .mono{font-family:PlexMono,monospace;white-space:nowrap}
.small{font-size:12px;color:var(--muted);line-height:1.38}
a{color:var(--gold);text-decoration:none}
.cover{--bg:#171914;--ink:#F3EEE3;--muted:#ABA797;--line:#3B3E34;--gold:#CFAD68;width:1600px;height:900px;background:#171914;color:#F3EEE3;position:relative;overflow:hidden;margin:20px auto;page-break-after:always;break-after:page}
@media print{.cover{margin:0}}
.cover .imprint{position:absolute;left:80px;top:64px;display:flex;align-items:center;gap:16px;font-size:24px;font-weight:600;letter-spacing:-.02em}
.cover .event{position:absolute;right:80px;top:66px;text-align:right;font-size:15px;line-height:1.75;color:var(--muted)}
.cover .title{position:absolute;left:80px;top:150px;font-family:DMSerif,serif;font-size:181px;line-height:1.01;letter-spacing:-.04em}
.cover .title span{display:block}
.cover .title .second{margin-left:150px;margin-top:10px;white-space:nowrap}
.cover .title small{font-size:72px;letter-spacing:-.02em;position:relative;top:-3px}
.cover .title em{font-family:DMSerif,serif;font-style:italic;color:var(--gold);letter-spacing:-.035em}
.cover .mark{position:absolute;right:80px;top:158px;color:var(--gold)}
.cover .regi{position:absolute;left:80px;top:589px;display:flex;gap:19px}
.cover .regi i{display:block;height:1px;background:var(--gold);width:156px}.cover .regi i:last-child{position:relative;top:15px;width:69px}
.cover .desc{position:absolute;left:80px;top:651px;font-size:28px;line-height:1.5;letter-spacing:-.02em}
.cover .question{position:absolute;left:960px;top:644px;width:560px;font-family:DMSerif,serif;font-size:32px;line-height:1.25;color:var(--muted)}
.cover .date{position:absolute;right:80px;top:509px;font-family:PlexMono,monospace;font-size:13px;letter-spacing:.06em;color:var(--muted)}
.cover .cft{position:absolute;left:80px;right:80px;bottom:30px;display:flex;justify-content:space-between;align-items:center;font-size:14px;color:var(--muted)}
.cover .cft .mono{font-family:PlexMono,monospace;font-size:13px}
.qrow{display:grid;grid-template-columns:44px 1fr 150px;gap:14px;align-items:baseline;border-top:1px solid var(--line);padding:14px 0}
.qrow .n{font-family:PlexMono,monospace;font-size:13px;color:var(--gold)}
.qrow h3{font-family:DMSerif,serif;font-weight:400;font-size:23px;line-height:1.2}
.qrow p{font-size:14px;color:var(--muted);margin-top:4px}
.qrow .w{font-family:PlexMono,monospace;font-size:12px;color:var(--muted);text-align:right;text-transform:uppercase;letter-spacing:.06em}
.band{background:#171914;color:#F3EEE3;border-radius:2px;padding:22px 30px;display:grid;grid-template-columns:150px 1fr;gap:24px;align-items:start}
.band .lab{font-family:DMSerif,serif;font-style:italic;color:#CFAD68;font-size:26px;line-height:1.1}
.band p{font-family:DMSerif,serif;font-size:22px;line-height:1.35}
.ans{border-top:3px solid var(--gold);padding-top:10px}
.ans .q{font-family:PlexMono,monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.ans h3{font-family:DMSerif,serif;font-weight:400;font-size:20px;line-height:1.25;margin:6px 0 8px}
.ans strong{display:block;font-family:DMSerif,serif;font-weight:400;font-size:40px;line-height:1;color:var(--gold)}
.ans small{display:block;font-family:PlexMono,monospace;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-top:4px}
.roomy p{font-size:15.5px;line-height:1.5}.roomy .st p,.roomy .card p{font-size:14px}.roomy .st h3{font-size:20px}
.roomy .roadrow{padding:10px 0}.roomy .roadrow h3{font-size:20px}.roomy .roadrow p{font-size:13.5px}.roomy .call.serif p{font-size:21px}
.roomy .sheet.compact .roadrow{padding:7px 0}.roomy .sheet.compact .roadrow h3{font-size:18px}.roomy .sheet.compact .roadrow p{font-size:12.8px}.roomy .sheet.compact .call.serif p{font-size:19px}
.roomy td{font-size:14px}
.big h1{font-size:40px}.big .h{font-size:13px;margin-bottom:8px}
.big p{font-size:16.5px;line-height:1.55}.big p+p{margin-top:8px}
.big .st p,.big .card p{font-size:14.8px}.big .st h3{font-size:21px}.big .st .k{font-size:14px}
.big .card{padding:14px 16px}.big .card .ct{font-size:14.5px}.big .nums strong{font-size:36px}.big .nums span{font-size:11px}
.big td{font-size:15px;padding:8px}.big th{font-size:11px}
.big .risk p{font-size:14.8px}.big .risk strong{font-size:28px}.big .risk h4{font-size:15.5px}
.big .call p{font-size:17px}.big .call.serif p{font-size:22px}
.big .cap{font-size:17px}.big .capd{font-size:13px}
.big .qrow{padding:18px 0}.big .qrow h3{font-size:25px}.big .qrow p{font-size:15.5px}
.big .band p{font-size:24px}.big .band .lab{font-size:30px}
.big .ans h3{font-size:22px}.big .ans strong{font-size:50px}.big .ans small{font-size:12px}
.big .small{font-size:14px}
.big table.airy td{padding:13px 8px;vertical-align:top}.roomy .small{font-size:13.2px}.roomy .risk p{font-size:13.5px}.roomy .capd{font-size:12.8px}
"""


def page(no, title, body, supp=False, total=TOTAL_MAIN, kicker='', source='', theme='light'):
    ticks = ''.join(f'<i class="{"on" if i < no else ""}"></i>' for i in range(total))
    label = kicker or ('Material suplementar' if supp else '')
    idx = f'A{no} / A{total}' if supp else f'{no:02d} / {total:02d}'
    src = source or ('Binance, Bitfinex, Coinbase, Dukascopy, Kraken e SPDR. Tabelas completas em results/.' if supp else '')
    head_html = '' if title is None else f'<h1>{title}</h1><div class="rule"></div>'
    return (f'<section class="page {theme}"><div class="hd"><span>{label}</span><div class="reg">{ticks}</div><span>{idx}</span></div>'
            f'{head_html}{body}'
            f'<div class="ft"><span class="brand">{symbol(20, "var(--gold)", "var(--ink)")}BitFlow</span><span class="src">{src}</span>'
            f'<span class="mono">PAXG × OURO · 2020–2026</span></div></section>')


def card(i, title, nums, text):
    n = ''.join(f'<div><strong class="{c}">{v}</strong><span>{lab}</span></div>' for v, lab, c in nums)
    return f'<div class="card"><div class="ct"><i>{i:02d}</i>{title}</div><div class="nums">{n}</div><p>{text}</p></div>'


def step(i, title, text, k=''):
    kk = f'<div class="k">{k}</div>' if k else ''
    return f'<div class="st"><div class="sn">{i:02d}</div><h3>{title}</h3><p>{text}</p>{kk}</div>'


def risk(lab, title, big, small, text, ok=False):
    return f'<div class="risk"><div class="lab">{lab}</div><h4>{title}</h4><strong class="{"g" if ok else "r"}">{big}</strong><small>{small}</small><p>{text}</p></div>'


def fig(svg_html, n, title, desc):
    return f'<div class="fig">{svg_html}</div><div class="cap"><i>FIG. {n}</i>{title}</div><div class="capd">{desc}</div>'
