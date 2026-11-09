"""Auditorias independentes e relatório de integridade da entrega."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from .common import ROOT,dump_json,finite_or_none,save_csv,sha256,utc_now
from .panel import gold_open_mask


def reference_crosscheck():
    gold=pd.read_parquet(ROOT/'data/interim/gold_1h.parquet')
    gold=gold[gold.quote_active & gold.valid_quotes].copy()
    ny=gold.bar_end.dt.tz_convert('America/New_York')
    gold=gold[ny.dt.hour.eq(16)].copy()
    gold['date']=gold.bar_end.dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d')
    etf=pd.read_excel(ROOT/'data/raw/documents/gld.xlsx',sheet_name='US GLD Historical Archive')
    etf['date']=pd.to_datetime(etf['Date'],format='%d-%b-%Y',errors='coerce').dt.strftime('%Y-%m-%d')
    for col in ['Closing Price','Ounces of Gold per Share']:
        etf[col]=pd.to_numeric(etf[col].astype(str).str.replace(',','',regex=False),errors='coerce')
    joined=gold[['date','mid_close']].merge(etf[['date','Closing Price','Ounces of Gold per Share']],on='date')
    joined=joined.dropna().sort_values('date')
    joined['gold_etf_proxy']=joined['Closing Price']/joined['Ounces of Gold per Share']
    joined['difference_log_bps']=10000*np.log(joined.mid_close/joined.gold_etf_proxy)
    summary={'n_dates':len(joined),'median_abs_level_difference_bps':finite_or_none(joined.difference_log_bps.abs().median()),
             'p95_abs_level_difference_bps':finite_or_none(joined.difference_log_bps.abs().quantile(.95)),
             'daily_return_correlation':finite_or_none(np.log(joined.mid_close).diff().corr(np.log(joined.gold_etf_proxy).diff())),
             'interpretation':'Sanity check: GLD fechamento/onças não é cotação física nem livro; custos e pequenos resíduos do fundo permanecem.',
             'sources':['Dukascopy XAUUSD close at NY16','Official GLD closing price and ounces/share']}
    if len(joined)<100 or summary['daily_return_correlation']<.95 or summary['median_abs_level_difference_bps']>100:
        raise ValueError('Referência de ouro falhou na checagem independente; revisar dados antes de publicar.')
    save_csv(joined,'QA_gold_reference.csv')
    dump_json(ROOT/'results/QA_gold_reference_summary.json',summary)
    return summary


def validate_outputs(config):
    h=pd.read_parquet(ROOT/'data/panel/panel_hourly.parquet')
    w=pd.read_parquet(ROOT/'data/panel/panel_weekends.parquet')
    trades=pd.read_parquet(ROOT/'data/panel/trades_A.parquet')
    claims=pd.read_csv(ROOT/'results/claims.csv')
    usage=pd.read_csv(ROOT/'results/PDF_claim_usage.csv')
    checks={}
    checks['hourly_timestamps_unique']=not h.t.duplicated().any()
    checks['weekend_calendar_count']=len(w)==config['data']['candidate_weekends']
    checks['valid_weekends_regular']=bool(w.loc[w.valid,'calendar_status'].eq('regular_calendar').all())
    checks['no_weekend_future_after_cutoff']=bool((w.t_0<pd.Timestamp(config['data']['end_exclusive_utc'])).all())
    checks['log_identity']=bool(w.loc[w.valid,'identity_residual_bps'].abs().max()<1e-8)
    checks['hourly_observed_currency']=bool(h.currency_method.eq('observed_bitfinex_usdt_usd').all())
    checks['invalid_hourly_basis_is_missing']=bool(h.loc[~h.valid,'basis_log_bps'].isna().all())
    checks['signal_before_entry']=bool((trades.t_signal<trades.t_in).all())
    checks['signal_price_available_before_signal']=bool((trades.loc[trades.signal_available,'signal_price_at']<=trades.loc[trades.signal_available,'t_signal']).all())
    checks['missing_exit_not_evaluated']=bool((~trades.loc[~trades.exit_observed,'evaluated_trade']).all())
    checks['unknown_access_preserved']=bool(trades.short_access_status.eq('not_verified').all())
    checks['no_executable_claim']=bool(trades.execution_status.eq('minute_OHLC_proxy_not_executable_claim').all())
    checks['headline_ids_unique']=not claims.claim_id.duplicated().any()
    checks['every_pdf_claim_exists']=set(usage.claim_id).issubset(set(claims.claim_id))
    checks['every_claim_source_exists']=all((ROOT/path).exists() for path in claims.source_file)
    figures=json.loads((ROOT/'results/figure_manifest.json').read_text())
    checks['figure_hashes_match']=all(sha256(ROOT/'results'/name)==item['sha256'] for name,item in figures.items())
    checks['figure_sources_exist']=all((ROOT/source).exists() for info in figures.values() for source in info['source_files'])
    frozen=json.loads((ROOT/'results/config_frozen.json').read_text())
    checks['all_figures_use_frozen_config']=all(info['config_hash']==frozen['config_hash'] for info in figures.values())
    presentation=json.loads((ROOT/'results/presentation_status.json').read_text())
    checks['presentation_main_within_editorial_limit']=presentation['main_pages']<=config['delivery']['editorial_max_slides']
    checks['presentation_appendices_recorded']=presentation['pages']==presentation['main_pages']+presentation['appendix_pages']
    checks['presentation_design_recorded']=presentation['design'] in ('aureo-v2','relatorio-v5')
    checks['presentation_qa_passed']=json.loads((ROOT/'results/QA_presentation.json').read_text(encoding='utf-8')).get('status')=='passed'
    sim=pd.read_csv(ROOT/'results/T5_sensibilidade.csv')
    primary=trades[trades.horizon_hours.eq(config['convergence']['exit_after_entry_hours'])]
    expected_stochastic=int(primary.path_valid.sum())>=config['scenarios']['min_recent_valid_weekends']
    checks['scenario_gate_honored']=all(('paired_joint' in method)==expected_stochastic for method in sim.method)
    checks['net_unknown_is_not_zero']=bool(trades.net_if_residual_assumed_bps.isna().all())
    checks['selection_not_filtered_on_profit']=bool(trades.evaluated_trade.eq(trades.path_valid & trades.signal_eligible).all())
    checks['no_gold_in_closed_regular_hours']=bool(gold_open_mask(h.bar_start).all())
    refined=json.loads((ROOT/'results/QA_refinement.json').read_text())
    checks['refinement_integrity_passed']=refined['status']=='passed'
    frozen_extension=json.loads((ROOT/'results/refinement_config_frozen.json').read_text())
    checks['refinement_figures_frozen']=all(info.get('refinement_config_hash')==frozen_extension['config_hash'] for info in figures.values() if 'refinement_config_hash' in info)
    failed=[key for key,value in checks.items() if not value]
    report={'status':'passed' if not failed else 'failed','at_utc':utc_now(),'checks':checks,'failed':failed,
            'code_hashes':{str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'src').glob('*.py'))},
            'scope':'deterministic data/output integrity, not proof of market efficiency or execution'}
    dump_json(ROOT/'results/QA_integrity.json',report)
    if failed:raise ValueError('Falhas de integridade: '+', '.join(failed))
    return report
