"""Análise descritiva v4 (posterior aos resultados originais): o desvio PAXG vs ouro como nível que muda de regime.

Uso: python -m src.regime            (offline, usa data/panel/panel_hourly.parquet)
     python -m src.regime --kraken   (acrescenta a checagem pontual com a Kraken; exige rede)
Saídas: results/T11_regime_mensal.csv, T11_regime_anual.csv, T11_regime_resumo.json, T11_kraken_checagem.csv
Não altera parâmetros congelados. Exploratório: foi escolhido depois de ver os resultados originais.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from .common import ROOT, dump_json, save_csv


def run_regime() -> dict:
    p = pd.read_parquet(ROOT / 'data/panel/panel_hourly.parquet')
    p = p[p.valid].copy()
    p['month'] = p.t.dt.tz_localize(None).dt.to_period('M').astype(str)
    p['year'] = p.t.dt.year
    b = p.basis_log_bps
    monthly = p.groupby('month').agg(
        hours=('basis_log_bps', 'size'), median_bps=('basis_log_bps', 'median'),
        p10_bps=('basis_log_bps', lambda s: s.quantile(.10)), p90_bps=('basis_log_bps', lambda s: s.quantile(.90)),
        usd_volume=('vol_token_usd', 'sum')).reset_index()
    save_csv(monthly, 'T11_regime_mensal.csv')

    g = p.groupby('year').basis_log_bps
    annual = pd.DataFrame({
        'hours': g.size(), 'mean_signed_bps': g.mean(), 'median_abs_bps': g.apply(lambda s: s.abs().median()),
        'p95_abs_bps': g.apply(lambda s: s.abs().quantile(.95)),
        'within_25_bps': g.apply(lambda s: (s.abs() <= 25).mean()),
        'usd_volume_millions': p.groupby('year').vol_token_usd.sum() / 1e6}).reset_index()
    save_csv(annual, 'T11_regime_anual.csv')

    def r2(group):
        level = p.groupby(group).basis_log_bps.transform('mean')
        return 1 - ((b - level) ** 2).sum() / ((b - b.mean()) ** 2).sum(), (b - level).abs().median()
    r2_month, resid_month = r2('month')
    r2_week, resid_week = r2('week')
    med = monthly.set_index('month').median_bps
    summary = {
        'hours': int(len(p)), 'months': int(len(med)),
        'variance_share_monthly_level': float(r2_month), 'variance_share_weekly_level': float(r2_week),
        'median_abs_around_month_level_bps': float(resid_month), 'median_abs_around_week_level_bps': float(resid_week),
        'monthly_median_min_bps': float(med.min()), 'monthly_median_max_bps': float(med.max()),
        'months_abs_median_above_25': float((med.abs() > 25).mean()),
        'hours_within_25_bps': float((b.abs() <= 25).mean()), 'hours_discount_share': float((b < 0).mean()),
        'ar1_hourly_2026': float(np.corrcoef(*(lambda x: (x[:-1], x[1:]))(p[p.year == 2026].sort_values('t').basis_log_bps.values))[0, 1]),
    }
    dump_json(ROOT / 'results/T11_regime_resumo.json', summary)
    return summary


def kraken_check() -> pd.DataFrame:
    """Checagem pontual: a Kraken (PAXG/USD) mostra o mesmo sinal e magnitude de desvio contra o ouro."""
    import requests
    panel = pd.read_parquet(ROOT / 'data/panel/panel_hourly.parquet')
    panel = panel[panel.valid].set_index('t')
    rows = []
    for since in ['2023-07-10', '2024-02-05', '2025-02-10']:
        start = int(pd.Timestamp(since, tz='UTC').timestamp())
        reply = requests.get('https://api.kraken.com/0/public/Trades',
                             params={'pair': 'PAXGUSD', 'since': start, 'count': 1000}, timeout=30).json()
        trades = pd.DataFrame(list(reply['result'].values())[0]).iloc[:, :3]
        trades.columns = ['price', 'volume', 'ts']
        trades['price'] = trades.price.astype(float)
        trades['t'] = pd.to_datetime(trades.ts.astype(float), unit='s', utc=True).dt.ceil('h')
        last = trades.groupby('t').price.last().rename('kraken')
        m = pd.concat([last, panel[['p_usdt', 'S']]], axis=1, join='inner')
        rows.append({'window_start': since, 'hours_matched': len(m),
                     'kraken_median_bps': float((1e4 * np.log(m.kraken / m.S)).median()),
                     'binance_median_bps': float((1e4 * np.log(m.p_usdt / m.S)).median())})
    frame = pd.DataFrame(rows)
    save_csv(frame, 'T11_kraken_checagem.csv')
    return frame


def kraken_extremes() -> pd.DataFrame:
    """Checagem dos dias mais extremos do desvio (mar/2024 e jun/2023) contra negócios da Kraken, hora a hora."""
    import requests
    panel = pd.read_parquet(ROOT / 'data/panel/panel_hourly.parquet')
    panel = panel[panel.valid].set_index('t')
    rows = []
    for since in ['2023-06-09T10:00:00', '2024-03-01T12:00:00', '2024-03-04T12:00:00']:
        start = int(pd.Timestamp(since, tz='UTC').timestamp())
        reply = requests.get('https://api.kraken.com/0/public/Trades',
                             params={'pair': 'PAXGUSD', 'since': start, 'count': 1000}, timeout=30).json()
        trades = pd.DataFrame(list(reply['result'].values())[0]).iloc[:, :3]
        trades.columns = ['price', 'volume', 'ts']
        trades['price'] = trades.price.astype(float)
        trades['usd'] = trades.price * trades.volume.astype(float)
        trades['t'] = pd.to_datetime(trades.ts.astype(float), unit='s', utc=True).dt.ceil('h')
        k = trades.groupby('t').agg(kraken=('price', 'last'), kraken_usd=('usd', 'sum'))
        m = pd.concat([k, panel[['p_usdt', 'q', 'S', 'basis_log_bps']]], axis=1, join='inner').reset_index()
        m['kraken_bps'] = 1e4 * np.log(m.kraken / m.S)
        rows.append(m.head(12))
    frame = pd.concat(rows)
    save_csv(frame, 'T11_kraken_extremos.csv')
    return frame


if __name__ == '__main__':
    print(run_regime())
    if '--kraken' in sys.argv:
        print(kraken_check())
        print(kraken_extremes())
