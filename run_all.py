"""Executa a pesquisa; --all inclui aquisição e pacote; --offline proíbe rede."""
from __future__ import annotations
import argparse
import traceback
import subprocess
import sys
from src.common import ROOT, dump_json, freeze_config, load_config, utc_now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ['all', 'fetch', 'build', 'minutes', 'analyze', 'refine', 'v5', 'figures', 'package', 'offline']:
        parser.add_argument('--' + flag, action='store_true')
    args = parser.parse_args()
    if not any([args.all, args.fetch, args.build, args.minutes, args.analyze, args.refine, args.v5, args.figures, args.package]):
        parser.error('Escolha --all ou pelo menos uma etapa.')
    config = load_config()
    freeze_config(config)
    for name in ['data/raw', 'data/interim', 'data/panel', 'results', 'slides', 'scripts_txt']:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    stages = []
    try:
        if args.all or args.fetch:
            from src.fetch import fetch_base
            fetch_base(config, offline=args.offline)
            stages.append('fetch_base')
        if args.all or args.build:
            from src.panel import build_panels
            build_panels(config)
            stages.append('build_panels')
        if args.all or args.minutes:
            import pandas as pd
            from src.fetch import fetch_minutes
            from src.panel import build_minute_panels
            weekends = pd.read_parquet(ROOT / 'data/panel/panel_weekends.parquet')
            fetch_minutes(config, weekends, offline=args.offline)
            build_minute_panels(config)
            stages.append('minutes')
        if args.all or args.analyze:
            from src.analysis import analyze_all
            analyze_all(config)
            stages.append('analysis')
        if args.all or args.analyze or args.refine:
            from src.refinement import run_refinement
            run_refinement(config)
            stages.append('refinement')
        if args.all or args.figures:
            from src.report import build_report
            build_report(config)
            stages.append('figures_pdf')
        if args.v5 and not (args.all or args.figures):
            # Extensão v5 (posterior aos resultados originais): regime, rotação, fim de semana e relatório final.
            from src.regime import run_regime
            from src.rotation import run_all_v5
            from src.report_v5_build import main as build_v5
            run_regime()
            run_all_v5()
            build_v5()
            import shutil
            shutil.copyfile(ROOT / 'slides/relatorio_final.pdf', ROOT / 'slides/entrega.pdf')
            shutil.copyfile(ROOT / 'slides/relatorio_final.html', ROOT / 'slides/entrega.html')
            shutil.copyfile(ROOT / 'slides/material_suplementar.pdf', ROOT / 'slides/entrega_suplementar.pdf')
            stages.append('v5')
        if args.all or args.package:
            from src.report import package_delivery
            subprocess.run([sys.executable,'-m','pytest','-q','--junitxml',str(ROOT/'results/pytest.xml')],cwd=ROOT,check=True)
            stages.append('tests')
            package_delivery(config)
            stages.append('package')
        dump_json(ROOT / 'results/run_status.json', {'status': 'completed_requested_stages', 'finished_at_utc': utc_now(), 'stages': stages, 'offline': args.offline})
        print('Etapas concluídas: ' + ', '.join(stages), flush=True)
    except Exception as error:
        dump_json(ROOT / 'results/run_status.json', {'status': 'failed', 'at_utc': utc_now(), 'stages_completed': stages, 'error': str(error), 'traceback': traceback.format_exc()})
        raise


if __name__ == '__main__':
    main()
