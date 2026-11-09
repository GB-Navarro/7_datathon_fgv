"""Entrega v3: pacote próprio em entrega/v3/, sem tocar nos pacotes da v1 e da v2.

Uso: python -m src.v3_package
"""
from __future__ import annotations

import json
import zipfile

from .common import ROOT, dump_json, sha256, utc_now

OUT = ROOT / 'entrega' / 'v3'
OMIT = {'T2_trade_ledger.csv', 'T9_fx_trade_ledger.csv', 'QA_three_weekends.csv', 'QA_fx_source_comparison.csv', 'QA_gold_reference.csv', 'run_status.json'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    txt = OUT / 'scripts_txt'
    code = [ROOT / 'run_all.py', *sorted((ROOT / 'src').glob('*.py')), *sorted((ROOT / 'tests').glob('*.py'))]
    for path in code:
        target = txt / (str(path.relative_to(ROOT)) + '.txt')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
    files = [ROOT / 'README.md', ROOT / 'PLANO_ENTREGA_V2.md', ROOT / 'PLANO_ENTREGA_V3.md', ROOT / 'plano-ajustes-paxg-datathon.md', ROOT / 'requirements.txt', ROOT / 'pytest.ini',
             *(ROOT / 'config').glob('*.json'), *code, *txt.rglob('*.txt'),
             ROOT / 'slides/entrega_v3.pdf', ROOT / 'slides/entrega_v3.html', ROOT / 'slides/entrega_v3_suplementar.pdf',
             *(ROOT / 'slides/design-systems/assets/fonts').glob('*'),
             *(p for p in (ROOT / 'results').glob('*') if p.is_file() and p.suffix in {'.csv', '.json', '.md', '.xml', '.png'} and p.name not in OMIT),
             *(p for p in (ROOT / 'results' / 'v2').glob('*') if p.is_file() and not p.name.startswith('_')),
             *(p for p in (ROOT / 'results' / 'v3').glob('*') if p.is_file()),
             *(ROOT / 'data/raw/bitfinex_xaut').glob('*.meta.json'), *(ROOT / 'data/raw/blockscout').glob('*.meta.json')]
    files = sorted({p for p in files if p.exists()})
    manifest = [{'path': str(p.relative_to(ROOT)).replace('\\', '/'), 'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in files]
    dump_json(OUT / 'manifest_v3.json', {'generated_at_utc': utc_now(), 'entrega': 'v3',
                                         'data_policy': 'sem dados brutos de preço; só metadados dos downloads novos', 'files': manifest})
    zpath = OUT / 'preco_da_promessa_v3.zip'
    assert zpath != ROOT / 'entrega' / 'preco_da_promessa.zip'
    with zipfile.ZipFile(zpath, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, str(p.relative_to(ROOT)))
        z.write(OUT / 'manifest_v3.json', 'manifest_v3.json')
    print(f'Pacote v3 pronto: {zpath.relative_to(ROOT)} ({len(files)} arquivos)')


if __name__ == '__main__':
    main()
