"""Entrega v2: figuras novas (mesma paleta e helpers do relatório v1, sem alterá-lo)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .report_v5 import CUSTO, GRID, HALO, INK, MUTED, NEUTRO, OURO, PAXG, PAXG_L, num, svg, tx


def fig_xaut_vs_paxg(curve_paxg, curve_xaut):
    """Ganho acumulado contra o GLDM com a mesma regra (±19, custos intermediários) no PAXG e no XAUT."""
    w, h = 620, 330
    l, r, top, ph = 56, 12, 16, 266
    a = curve_paxg.copy()
    b = curve_xaut.copy()
    a['dia'], b['dia'] = pd.to_datetime(a.dia), pd.to_datetime(b.dia)
    t0, t1 = min(a.dia.min(), b.dia.min()), max(a.dia.max(), b.dia.max())
    x = lambda ts: l + (pd.Timestamp(ts) - t0).days / (t1 - t0).days * (w - l - r)
    hi = max(900, float(a.ganho_acumulado_bps.max()) * 1.08)
    lo = min(-100, float(b.ganho_acumulado_bps.min()), float(a.ganho_acumulado_bps.min()))
    y = lambda v: top + (hi - v) / (hi - lo) * ph
    out = []
    for v in range(0, int(hi) + 1, 200):
        out.append(f'<path d="M{l} {y(v):.1f}H{w - r}" stroke="{INK if v == 0 else GRID}"/>' + tx(l - 8, y(v) + 4, num(v, 0, True) if v else '0', 12, MUTED, 'end'))
    for yr in range(t0.year + 1, t1.year + 1):
        out.append(tx(x(pd.Timestamp(f'{yr}-01-01')), top + ph + 20, yr, 12, MUTED, 'middle'))
    for d, col, label in [(a, PAXG, 'PAXG'), (b, OURO, 'XAUT')]:
        pts = ' '.join(f'{x(t):.1f},{y(v):.1f}' for t, v in zip(d.dia, d.ganho_acumulado_bps))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        last = d.iloc[-1]
        out.append(tx(x(last.dia) - 4, y(last.ganho_acumulado_bps) - 8, f'{label}: {num(last.ganho_acumulado_bps, 0, True)} bps', 13, col, 'end', 800, HALO))
    out.append(tx(l + 6, top + 12, 'ganho acumulado contra manter o GLDM, bps', 12, MUTED, 'start', 500, HALO))
    return svg(w, h, 'Ganho acumulado da mesma regra de rotação no PAXG e no XAUT.', ''.join(out))


def fig_onchain(weekly):
    """Desvio semanal do PAXG e emissão líquida das 4 semanas seguintes (% da oferta no Ethereum)."""
    d = weekly.dropna(subset=['emissao_prox_4s_pct']).copy()
    d['semana'] = pd.to_datetime(d.semana)
    w, h = 470, 230
    l, top, ph = 46, 18, 180
    xs = d.desvio_bps.clip(-200, 160).values
    ys = d.emissao_prox_4s_pct.clip(-15, 15).values
    xl, xh, yl, yh = -200, 160, -15, 15
    x = lambda v: l + (v - xl) / (xh - xl) * (w - l - 12)
    y = lambda v: top + (yh - v) / (yh - yl) * ph
    out = []
    for v in [-15, -10, -5, 0, 5, 10, 15]:
        out.append(f'<path d="M{l} {y(v):.1f}H{w - 12}" stroke="{INK if v == 0 else GRID}"/>' + tx(l - 6, y(v) + 4, num(v, 0, True) if v else '0', 11, MUTED, 'end'))
    for v in [-200, -100, 0, 100]:
        out.append(f'<path d="M{x(v):.1f} {top}V{top + ph}" stroke="{INK if v == 0 else GRID}"/>' + tx(x(v), top + ph + 16, num(v, 0, True) if v else '0', 11, MUTED, 'middle'))
    for a, b_ in zip(xs, ys):
        out.append(f'<circle cx="{x(a):.1f}" cy="{y(b_):.1f}" r="2.4" fill="{PAXG}" fill-opacity=".45"/>')
    beta = np.polyfit(d.desvio_bps.values, d.emissao_prox_4s_pct.values, 1)
    out.append(f'<path d="M{x(xl):.1f} {y(np.polyval(beta, xl)):.1f}L{x(xh):.1f} {y(np.polyval(beta, xh)):.1f}" stroke="{CUSTO}" stroke-width="2"/>')
    out.append(tx(w - 14, top + 12, 'emissão líquida nas 4 semanas seguintes, % da oferta', 11, MUTED, 'end', 500, HALO))
    out.append(tx(w - 14, top + ph - 6, 'desvio da semana, bps', 11, MUTED, 'end', 500, HALO))
    return svg(w, h, 'Desvio semanal do PAXG contra a emissão líquida das quatro semanas seguintes.', ''.join(out))
