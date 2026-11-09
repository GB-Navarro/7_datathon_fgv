"""Configuração, rastreabilidade e operações sem dependência de rede."""
from __future__ import annotations

import hashlib
import json
import platform
import threading
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_config():
    return json.loads((ROOT / 'config/params.json').read_text(encoding='utf-8'))


def sources():
    return json.loads((ROOT / 'config/sources.json').read_text(encoding='utf-8'))


def dump_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str, allow_nan=False) + '\n', encoding='utf-8')


def append_log(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with LOCK, path.open('a', encoding='utf-8') as file:
        file.write(json.dumps(obj, default=str, ensure_ascii=False) + '\n')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_frame(frame, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def save_csv(frame, name):
    path = ROOT / 'results' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding='utf-8-sig', float_format='%.10g')


def freeze_config(config):
    target = ROOT / 'results/config_frozen.json'
    signature = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    if target.exists():
        frozen = json.loads(target.read_text(encoding='utf-8'))
        if frozen['config_hash'] != signature:
            raise RuntimeError('Parâmetros diferem do snapshot congelado. Versione a alteração explicitamente antes de continuar.')
        return frozen
    frozen = {'frozen_at_utc': utc_now(), 'config_hash': signature, 'config': config,
              'note': 'Congelamento de implementação; pesquisa prévia e amostras já haviam sido vistas.',
              'python': platform.python_version()}
    dump_json(target, frozen)
    return frozen


def week_start(timestamps):
    t = pd.DatetimeIndex(timestamps)
    return t.normalize() - pd.to_timedelta((t.weekday + 1) % 7, unit='D')


def normalize_times(values):
    """Uma unidade por arquivo; rejeita unidades misturadas ou datas implausíveis."""
    raw = pd.to_numeric(pd.Series(values), errors='raise')
    if raw.empty:
        return pd.DatetimeIndex([], tz='UTC')
    magnitude = float(raw.median())
    unit = 'us' if magnitude > 1e14 else 'ms' if magnitude > 1e11 else 's'
    t = pd.DatetimeIndex(pd.to_datetime(raw, unit=unit, utc=True))
    if t.min() < pd.Timestamp('1990-01-01', tz='UTC') or t.max() > pd.Timestamp('2030-01-01', tz='UTC'):
        raise ValueError('Unidade de timestamp inconsistente ou data fora do intervalo plausível.')
    return t


def basis(token, fx, gold):
    p, q, s = np.asarray(token, dtype=float), np.asarray(fx, dtype=float), np.asarray(gold, dtype=float)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where((p > 0) & (q > 0) & (s > 0), 10000 * np.log(p * q / s), np.nan)


def finite_or_none(value):
    return float(value) if pd.notna(value) and np.isfinite(value) else None
