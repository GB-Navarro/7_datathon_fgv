import hashlib, json, pathlib, sys, datetime
root = pathlib.Path('.')
files = ['slides/entrega.pdf', 'slides/entrega.html', 'slides/entrega_suplementar.pdf', 'slides/relatorio_final.pdf', 'slides/relatorio_final.html',
         'slides/material_suplementar.pdf', 'slides/material_suplementar.html', 'entrega/preco_da_promessa.zip', 'entrega/manifest.json',
         'src/report_v5.py', 'src/report_v5_pages.py', 'src/report_v5_build.py', 'src/rotation.py', 'src/regime.py']
files += [p.as_posix() for p in sorted(root.glob('results/*')) if p.is_file()]
files += [p.as_posix() for p in sorted(root.glob('scripts_txt/**/*')) if p.is_file()]
h = {f: hashlib.sha256(open(f, 'rb').read()).hexdigest() for f in files}
target = pathlib.Path('entrega/v1_final_2026-11-08/hashes_v1.json')
if sys.argv[1:] == ['criar']:
    json.dump({'criado_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'arquivos': h}, open(target, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(len(h), 'arquivos congelados')
else:
    ref = json.load(open(target, encoding='utf-8'))['arquivos']
    diff = [f for f in ref if h.get(f) != ref[f]]
    print('arquivos conferidos', len(ref), 'diferentes', diff)
