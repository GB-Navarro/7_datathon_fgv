"""Aquisição pública com cache, hashes, checksums e limites de requisições."""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import io
import json
import os
import re
import subprocess
import threading
import time
import zipfile
from pathlib import Path
from html import unescape

import numpy as np
import pandas as pd
import requests

from .common import ROOT, append_log, dump_json, normalize_times, save_frame, sha256, sources, utc_now

RAW = ROOT / 'data/raw'
INTERIM = ROOT / 'data/interim'
_pace_locks = {'bitfinex': threading.Lock(), 'coinbase': threading.Lock()}
_last = {'bitfinex': 0., 'coinbase': 0.}


def paced(provider):
    with _pace_locks[provider]:
        gap = 2.1 if provider == 'bitfinex' else .24
        remaining = gap - (time.monotonic() - _last[provider])
        if remaining > 0:
            time.sleep(remaining)
        _last[provider] = time.monotonic()


def download(url, path, *, offline=False, provider=None):
    path = Path(path)
    sidecar = path.with_name(path.name + '.meta.json')
    if path.exists() and sidecar.exists():
        info = json.loads(sidecar.read_text(encoding='utf-8'))
        if info['url'] != url or sha256(path) != info['sha256']:
            raise ValueError(f'Cache alterado ou URL divergente: {path}')
        return path
    if offline:
        raise FileNotFoundError(f'Cache ausente no modo offline: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        if provider:
            paced(provider)
        response = requests.get(url, timeout=(15, 90), headers={'User-Agent': 'FGV-PAXG-research/2.1'})
        if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
            time.sleep(min(float(response.headers.get('Retry-After', 2 ** attempt + 1)), 30))
            continue
        response.raise_for_status()
        break
    if not response.content:
        raise ValueError(f'Resposta vazia: {url}')
    tmp = path.with_name(path.name + '.part')
    tmp.write_bytes(response.content)
    tmp.replace(path)
    info = {'url': url, 'downloaded_at_utc': utc_now(), 'sha256': sha256(path),
            'bytes': path.stat().st_size, 'content_type': response.headers.get('Content-Type')}
    dump_json(sidecar, info)
    append_log(RAW / 'manifest.jsonl', {'path': str(path.relative_to(ROOT)), **info})
    return path


KLINE_NAMES = ['raw_time', 'open', 'high', 'low', 'close', 'base_volume', 'raw_close',
               'quote_volume_quote_ccy', 'trades', 'taker_base', 'taker_quote', 'ignore']


def read_kline(path, resolution):
    with zipfile.ZipFile(path) as z:
        member = next(x for x in z.namelist() if x.endswith('.csv'))
        df = pd.read_csv(z.open(member), names=KLINE_NAMES, header=None)
    df = df[pd.to_numeric(df.raw_time, errors='coerce').notna()].copy()
    df['bar_start'] = normalize_times(df.raw_time)
    for c in KLINE_NAMES[1:]:
        df[c] = pd.to_numeric(df[c], errors='raise')
    df['bar_end'] = df.bar_start + pd.Timedelta(resolution)
    df['has_trade'] = (df.trades > 0) & (df.base_volume > 0)
    df['source'] = 'Binance PAXGUSDT'
    df['resolution'] = resolution
    df['download_id'] = Path(path).name
    bad = (df[['open', 'high', 'low', 'close']] <= 0).any(axis=1)
    bad |= (df.high < df[['open', 'close', 'low']].max(axis=1)) | (df.low > df[['open', 'close', 'high']].min(axis=1))
    if bad.any():
        raise ValueError(f'OHLC inválido: {path}, {bad.sum()} linhas')
    return df.drop(columns=['raw_time', 'raw_close', 'ignore'])


def fetch_binance(config, interval, start, *, offline=False):
    end = pd.Timestamp(config['data']['end_exclusive_utc'])
    start = pd.Timestamp(start)
    jobs = []
    for month in pd.date_range(start.normalize().replace(day=1), end.normalize().replace(day=1), freq='MS', tz='UTC'):
        if month >= end:
            continue
        next_month = month + pd.offsets.MonthBegin(1)
        if next_month <= end:
            date = month.strftime('%Y-%m')
            key = f'data/spot/monthly/klines/PAXGUSDT/{interval}/PAXGUSDT-{interval}-{date}.zip'
            jobs.append(key)
        else:
            for day in pd.date_range(month, end - pd.Timedelta(days=1), freq='D'):
                key = f'data/spot/daily/klines/PAXGUSDT/{interval}/PAXGUSDT-{interval}-{day:%Y-%m-%d}.zip'
                jobs.append(key)

    def one(key):
        path = RAW / 'binance' / key.split('/')[-1]
        url = sources()['binance_archive'] + key
        download(url, path, offline=offline)
        checksum = download(url + '.CHECKSUM', path.with_name(path.name + '.CHECKSUM'), offline=offline)
        expected = checksum.read_text(encoding='utf-8').split()[0].lower()
        if expected != sha256(path):
            raise ValueError(f'Checksum Binance inválido: {path}')
        return read_kline(path, '1h' if interval == '1h' else '1min')

    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        frames = list(pool.map(one, jobs))
    df = pd.concat(frames, ignore_index=True).sort_values('bar_start')
    if df.bar_start.duplicated().any():
        raise ValueError('Duplicatas Binance entre arquivos: verificar bordas.')
    df = df[(df.bar_start >= start) & (df.bar_end <= end)].reset_index(drop=True)
    save_frame(df, INTERIM / f'token_{interval}.parquet')
    print(f'Binance {interval}: {len(df):,} barras', flush=True)
    return df


def fetch_bitfinex(config, interval='1h', windows=None, *, offline=False):
    if windows is None:
        windows = [(pd.Timestamp(config['data']['start_utc']), pd.Timestamp(config['data']['end_exclusive_utc']))]
    labels = download(sources()['bitfinex_api'] + 'conf/pub:map:currency:label', RAW / 'bitfinex/currencies.json', offline=offline, provider='bitfinex')
    mapping = dict(json.loads(labels.read_text())[0])
    if 'Tether' not in mapping.get('UST', ''):
        raise ValueError('Símbolo UST Bitfinex não identificado como Tether.')
    parts = []
    for start, end in windows:
        a, b = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
        cursor = a
        while cursor < b:
            url = sources()['bitfinex_api'] + f'candles/trade:{interval}:tUSTUSD/hist?start={cursor}&end={b-1}&limit=10000&sort=1'
            path = RAW / 'bitfinex' / f'USTUSD-{interval}-{cursor}-{b}.json'
            download(url, path, offline=offline, provider='bitfinex')
            rows = json.loads(path.read_text())
            if not rows:
                break
            if not isinstance(rows[0], list):
                raise ValueError(f'Formato Bitfinex inesperado: {rows}')
            df = pd.DataFrame(rows, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume'])
            df = df[(df.timestamp >= a) & (df.timestamp < b)].copy()
            if df.empty:
                break
            parts.append(df)
            new_cursor = int(df.timestamp.max()) + 1
            if new_cursor <= cursor:
                raise ValueError('Paginação Bitfinex sem progresso.')
            cursor = new_cursor
            if len(rows) < 10000:
                break
    result = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=['timestamp', 'open', 'close', 'high', 'low', 'volume'])
    result = result.drop_duplicates('timestamp').sort_values('timestamp')
    result['bar_start'] = pd.to_datetime(result.timestamp, unit='ms', utc=True)
    result['bar_end'] = result.bar_start + pd.Timedelta(hours=1) if interval == '1h' else result.bar_start + pd.Timedelta(minutes=1)
    result['has_trade'] = result.volume > 0
    result['source'] = 'Bitfinex tUSTUSD (Tether USDt/USD)'
    result['resolution'] = interval
    result['currency_method'] = 'observed_usdt_usd'
    result['download_id'] = f'bitfinex-{interval}-paginated'
    save_frame(result, INTERIM / f'fx_{interval}.parquet')
    print(f'Bitfinex {interval}: {len(result):,} barras', flush=True)
    return result


def dukascopy(config, resolution, start, end, side, *, offline=False):
    name = f'xauusd-{resolution}-{side}-{start:%Y-%m-%d}-{end:%Y-%m-%d}-volume'
    path = RAW / 'dukascopy' / (name + '.csv')
    meta = path.with_name(path.name + '.meta.json')
    if path.exists() and meta.exists():
        if sha256(path) != json.loads(meta.read_text())['sha256']:
            raise ValueError(f'Cache ouro alterado: {path}')
        return path
    if offline:
        raise FileNotFoundError(f'Ouro ausente: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    package = 'dukascopy-node@' + sources()['dukascopy_package_version']
    args = ['npx.cmd' if os.name == 'nt' else 'npx', '--yes', package, '-i', 'xauusd',
            '-from', f'{start:%Y-%m-%d}', '-to', f'{end:%Y-%m-%d}', '-t', resolution,
            '-p', side, '-v', '-fl', '-f', 'csv', '-fn', name, '-dir', str(path.parent),
            '--waf-mode', 'off', '--no-waf-token-cache']
    cmd = ['cmd.exe', '/d', '/c', *args] if os.name == 'nt' else args
    for attempt in range(3):
        run = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace',
                             timeout=300, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if run.returncode == 0 and path.exists():
            break
        if '403' in run.stdout + run.stderr:
            raise RuntimeError(f'Acesso recusado pelo provedor: {name}: {run.stdout[-500:]}')
        if attempt == 2:
            raise RuntimeError(f'Falha Dukascopy {name}: {run.stdout[-1000:]} {run.stderr[-1000:]}')
        time.sleep(2)
    info = {'url': sources()['dukascopy_documentation'], 'command': args, 'downloaded_at_utc': utc_now(),
            'sha256': sha256(path), 'bytes': path.stat().st_size}
    dump_json(meta, info)
    append_log(RAW / 'manifest.jsonl', {'path': str(path.relative_to(ROOT)), **info})
    return path


def fetch_gold(config, resolution='h1', start=None, *, offline=False):
    start = pd.Timestamp(start or config['data']['start_utc']).normalize()
    end = pd.Timestamp(config['data']['end_exclusive_utc'])
    # Blocos limitam a memória da CLI no download de minutos.
    bounds = [start]
    while bounds[-1] < end:
        bounds.append(min(bounds[-1] + pd.DateOffset(months=6 if resolution == 'm1' else 120), end))
    jobs = [(a, b, side) for a, b in zip(bounds[:-1], bounds[1:]) for side in ('bid', 'ask')]

    def one(job):
        a, b, side = job
        path = dukascopy(config, resolution, a, b, side, offline=offline)
        df = pd.read_csv(path)
        if 'volume' not in df:
            raise ValueError('Ouro sem volume: impossível distinguir barras sintéticas.')
        df['bar_start'] = normalize_times(df.timestamp)
        df['download_id'] = path.name
        return side, df

    with cf.ThreadPoolExecutor(max_workers=1) as pool:
        frames = list(pool.map(one, jobs))
    sides = {}
    for side in ('bid', 'ask'):
        df = pd.concat([frame for typ, frame in frames if typ == side], ignore_index=True).sort_values('bar_start')
        if df.bar_start.duplicated().any():
            raise ValueError('Ouro com duplicatas entre blocos.')
        df = df.drop(columns='timestamp').rename(columns={c: side+'_'+c for c in ['open', 'high', 'low', 'close', 'volume', 'download_id']})
        sides[side] = df
    df = sides['bid'].merge(sides['ask'], on='bar_start', how='outer', validate='one_to_one').sort_values('bar_start')
    df['bar_end'] = df.bar_start + pd.Timedelta(hours=1 if resolution == 'h1' else 0, minutes=1 if resolution == 'm1' else 0)
    df['quote_active'] = (df.bid_volume > 0) & (df.ask_volume > 0)
    df['valid_quotes'] = (df.bid_open > 0) & (df.ask_open >= df.bid_open) & (df.bid_close > 0) & (df.ask_close >= df.bid_close)
    df['mid_open'] = (df.bid_open + df.ask_open) / 2
    df['mid_close'] = (df.bid_close + df.ask_close) / 2
    df['spread_open_bps'] = 10000 * (df.ask_open - df.bid_open) / df.mid_open
    df['spread_close_bps'] = 10000 * (df.ask_close - df.bid_close) / df.mid_close
    df['source'] = 'Dukascopy XAUUSD bid/ask'
    df['resolution'] = '1h' if resolution == 'h1' else '1min'
    df['download_id'] = df.bid_download_id.fillna('') + '|' + df.ask_download_id.fillna('')
    df = df[(df.bar_start >= pd.Timestamp(config['data']['start_utc'])) & (df.bar_end <= end)].reset_index(drop=True)
    save_frame(df, INTERIM / ('gold_1h.parquet' if resolution == 'h1' else 'gold_1m.parquet'))
    print(f'Ouro {resolution}: {len(df):,} barras; {int(df.quote_active.sum()):,} ativas', flush=True)
    return df


def fetch_coinbase_validation(config, *, offline=False):
    end = pd.Timestamp(config['data']['end_exclusive_utc'])
    # Sobreposição sistemática: primeiros dois dias de cada mês, sem escolher por resultado.
    starts = list(pd.date_range(pd.Timestamp('2021-05-01', tz='UTC'), end, freq='MS'))
    chunks = []
    def one(t):
        e = min(t + pd.Timedelta(days=2), end)
        url = sources()['coinbase_api'] + f'products/USDT-USD/candles?granularity=3600&start={t.isoformat()}&end={e.isoformat()}'
        path = RAW / 'coinbase' / f'USDT-USD-validation-{t:%Y-%m}.json'
        download(url, path, offline=offline, provider='coinbase')
        rows = json.loads(path.read_text())
        df = pd.DataFrame(rows, columns=['timestamp', 'low', 'high', 'open', 'close', 'volume'])
        df['bar_start'] = pd.to_datetime(df.timestamp, unit='s', utc=True)
        return df[(df.bar_start >= t) & (df.bar_start < e)]
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        chunks = list(pool.map(one, starts))
    df = pd.concat(chunks, ignore_index=True).drop_duplicates('bar_start').sort_values('bar_start')
    save_frame(df, INTERIM / 'fx_coinbase_validation.parquet')
    return df


def fetch_reference_documents(*, offline=False):
    facts = {}
    for product in ('gld', 'gldm'):
        url = sources()[product]
        path = download(url, RAW / 'documents' / f'{product}.html', offline=offline)
        html = path.read_text(encoding='utf-8')
        text = re.sub(r'<[^>]+>', ' ', re.sub(r'<script\b[^>]*>.*?</script>', ' ', html, flags=re.S))
        text = re.sub(r'\s+', ' ', unescape(text))
        spread = re.search(r'30[-\s]*Day Median Bid/Ask Spread.{0,1800}?(\d+(?:\.\d+)?)\s*%', text, re.I)
        fee = re.search(r'Gross Expense Ratio.{0,900}?(\d+(?:\.\d+)?)\s*%', text, re.I)
        asof = re.search(r'Fund Market Price as of\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})', text)
        facts[product] = {'url': url, 'retrieved_at_utc': json.loads(path.with_name(path.name+'.meta.json').read_text())['downloaded_at_utc'],
                          'market_asof_text': asof.group(1) if asof else None,
                          'spread_30d_bps': float(spread.group(1))*100 if spread else None,
                          'expense_bps_year': float(fee.group(1))*100 if fee else None,
                          'status': 'official_page_parsed' if spread else 'spread_not_parsed_use_scenario'}
        archive = sources()['etf_archive'] + f'?product={product}&exchange=NYSE&lang=en'
        download(archive, RAW / 'documents' / f'{product}.xlsx', offline=offline)
    download(sources()['paxos_conditions'], RAW / 'documents/paxos.html', offline=offline)
    download(sources()['gold_trading_hours'], RAW / 'documents/gold_hours.html', offline=offline)
    dump_json(INTERIM / 'reference_facts.json', facts)
    return facts


def fetch_base(config, *, offline=False):
    jobs = [lambda: fetch_binance(config, '1h', config['data']['start_utc'], offline=offline),
            lambda: fetch_bitfinex(config, offline=offline), lambda: fetch_gold(config, offline=offline),
            lambda: fetch_coinbase_validation(config, offline=offline), lambda: fetch_reference_documents(offline=offline)]
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for future in [pool.submit(fn) for fn in jobs]:
            future.result()


def fetch_minutes(config, weekends, *, offline=False):
    recent = weekends.tail(config['convergence']['recent_window_weeks'])
    start = recent.t_0.min().normalize().replace(day=1)
    windows = [(r.t_0 - pd.Timedelta(minutes=6), r.t_0 + pd.Timedelta(hours=25, minutes=7)) for r in recent.itertuples() if pd.notna(r.t_0)]
    jobs = [lambda: fetch_binance(config, '1m', start, offline=offline),
            lambda: fetch_gold(config, 'm1', start, offline=offline),
            lambda: fetch_bitfinex(config, '1m', windows=windows, offline=offline)]
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for future in [pool.submit(fn) for fn in jobs]:
            future.result()
