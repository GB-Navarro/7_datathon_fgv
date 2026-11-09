import assert from 'node:assert/strict';
import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

// Verifica o desenho e sua documentação; não executa o estudo empírico.
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const params = JSON.parse(readFileSync(resolve(root, 'config/params.json'), 'utf8'));
const passed = [];
function check(name, fn) {
  fn();
  passed.push(name);
}
function near(actual, expected, tolerance = 1e-9) {
  assert.ok(Math.abs(actual - expected) <= tolerance,
    `Valor ${actual} diferente de ${expected} (tolerância ${tolerance})`);
}
function holdingStatus(a, b) {
  if (b === 0) return a === 0 ? 'equal' : a < 0 ? 'token_always_lower' : 'token_always_higher';
  if (b < 0) return a <= 0 ? 'token_always_lower' : 'token_lower_after_crossing';
  return a < 0 ? 'token_lower_before_crossing' : 'token_always_higher';
}
function pairPnl(s, pin, pout, sin, sout) {
  return s * ((pin - pout) + (sout - sin));
}

check('config_json_e_estado_real', () => {
  assert.ok(['plan_only', 'implementation', 'completed'].includes(params.study_status));
  assert.equal(params.plan_frozen_at_utc, null);
  assert.equal(params.scenarios.professional_desk_conclusion_enabled, false);
  assert.equal(params.delivery.slide_limit_confirmed_in_regulation, false);
});
check('323_candidatos_com_corte_anterior_ao_domingo_de_entrega', () => {
  const first = Date.parse(params.data.first_candidate_reopen_date);
  const last = Date.parse(params.data.last_candidate_reopen_date);
  near((last - first) / (7 * 86400000) + 1, 323);
  assert.equal(params.data.candidate_weekends, 323);
  assert.equal(new Date(first).getUTCDay(), 0);
  assert.equal(new Date(last).getUTCDay(), 0);
  assert.ok(last < Date.parse(params.data.end_exclusive_utc));
  assert.ok(last + 7 * 86400000 >= Date.parse(params.data.end_exclusive_utc));
});
check('inicio_binance_e_fuso_do_prazo', () => {
  assert.equal(new Date(1598616000000).toISOString(), '2020-08-28T12:00:00.000Z');
  assert.equal(new Date(params.data.start_utc).toISOString(), '2020-08-28T12:00:00.000Z');
  assert.equal(new Date(params.delivery.deadline_brasilia).toISOString(), '2026-11-09T02:59:00.000Z');
});
check('identidade_logaritmica_inclusive_em_saltos_grandes', () => {
  const pc = 1990, qc = 1.001, sc = 2000, p0 = 2120, q0 = 0.998, s0 = 2100;
  const bc = 10000 * Math.log(pc * qc / sc);
  const b0 = 10000 * Math.log(p0 * q0 / s0);
  const m = 10000 * Math.log((p0 * q0) / (pc * qc));
  const g = 10000 * Math.log(s0 / sc);
  near(b0 - bc, m - g);
});
check('C_duas_execucoes_com_inventario_pre_posicionado', () => {
  const fb = 5, fc = 5, sb = 4, sc = 6;
  near(fb + fc + sb / 2 + sc / 2, 15);
  near(2 * fb + 2 * fc + sb + sc, 30); // Ciclo com recomposição, custos constantes.
});
check('A_quatro_execucoes_e_spread_cheio_uma_vez_por_perna', () => {
  const ft = 5, fg = 1, st = 4, sg = 6, conversion = 2;
  near(2 * ft + 2 * fg + st + sg + conversion, 24);
  const mid = 100, tokenBid = mid * (1 - st / 20000), tokenAsk = mid * (1 + st / 20000);
  const goldBid = mid * (1 - sg / 20000), goldAsk = mid * (1 + sg / 20000);
  near(10000 * ((tokenBid - tokenAsk) + (goldBid - goldAsk)) / mid, -(st + sg));
});
check('pnl_quantidades_fixas_convergencia_e_divergencia', () => {
  near(pairPnl(1, 101, 100, 100, 100), 1);
  near(pairPnl(-1, 99, 100, 100, 100), 1);
  near(pairPnl(1, 101, 102, 100, 100), -1);
});
check('cruzamento_de_zero_nao_e_queda_do_desvio_absoluto', () => {
  const pnlBps = 10000 * pairPnl(1, 101, 99.5, 100, 100) / 100;
  const absReduction = 10000 * (Math.abs(Math.log(101 / 100)) - Math.abs(Math.log(99.5 / 100)));
  near(pnlBps, 150);
  assert.ok(Math.abs(pnlBps - absReduction) > 100);
});
check('reconstrucao_de_precos_e_pnl_dos_cenarios', () => {
  const sin = 2000, sout = 2040, pin = 2020, pout = 2030;
  const bi = 10000 * Math.log(pin / sin), bo = 10000 * Math.log(pout / sout);
  const r = sout / sin - 1;
  const reconstructed = Math.exp(bi / 10000) - (1 + r) * Math.exp(bo / 10000) + r;
  near(reconstructed, pairPnl(1, pin, pout, sin, sout) / sin);
});
check('perdas_nao_podem_virar_filtro_de_lucro', () => {
  const outcomes = [-5, 10];
  near(outcomes.reduce((a, b) => a + b, 0), 5);
  near(outcomes.reduce((a, b) => a + Math.max(b, 0), 0), 10);
  assert.equal(params.convergence.include_negative_pnl, true);
  assert.equal(params.convergence.drop_trade_based_on_realized_pnl, false);
});
check('equilibrio_GLD_6_6_e_GLDM_26_4_meses_exemplo', () => {
  near(12 * (25 - 3) / params.holding_cost.gld_fee_bps_per_year, 6.6);
  near(12 * (25 - 3) / params.holding_cost.gldm_fee_bps_per_year, 26.4);
});
check('equilibrio_todos_os_casos_e_reversao_da_vantagem', () => {
  assert.equal(holdingStatus(22, -40), 'token_lower_after_crossing');
  assert.equal(holdingStatus(-2, -40), 'token_always_lower');
  assert.equal(holdingStatus(0, -40), 'token_always_lower');
  assert.equal(holdingStatus(22, 0), 'token_always_higher');
  assert.equal(holdingStatus(-2, 0), 'token_always_lower');
  assert.equal(holdingStatus(0, 0), 'equal');
  assert.equal(holdingStatus(-2, 10), 'token_lower_before_crossing');
  assert.equal(holdingStatus(22, 10), 'token_always_higher');
  near(-12 * (-2) / 10, 2.4);
});
check('custos_fixos_dependem_do_notional', () => {
  near(10000 * 10 / 1000, 100);
  near(10000 * 10 / 100000, 1);
});
check('moeda_e_financiamento_desconhecidos_nao_sao_zero', () => {
  assert.equal(params.data.q_missing_policy, 'exclude_from_primary_usd_sample');
  assert.equal(params.data.use_usdc_as_usd, false);
  assert.equal(params.data.carry_across_market_closure, false);
  assert.equal(params.convergence.token_borrow_bps_per_day, null);
  assert.equal(params.convergence.gold_financing_bps_per_day, null);
  assert.equal(params.convergence.short_access_verified, false);
});
check('sequencia_sinal_entrada_saida_e_cortes', () => {
  assert.ok(params.convergence.entry_delay_from_signal_minutes > 0);
  assert.equal(params.convergence.exit_after_entry_hours, 6);
  assert.ok(params.scenarios.min_recent_valid_weekends <= params.analysis.recent_window_weeks);
  assert.ok(params.convergence.min_valid_weekends_for_aggregate_inference <= params.convergence.recent_window_weeks);
});
check('versoes_recebidas_preservadas', () => {
  assert.equal(statSync(resolve(root, 'historico/projeto_agentes_original.md')).size, 60826);
  assert.equal(statSync(resolve(root, 'historico/projeto_humanos_original.md')).size, 28379);
});
check('regulamento_preservado_com_hash', () => {
  const pdf = readFileSync(resolve(root, 'auditoria/fontes/regulamento_fgv_2026.pdf'));
  assert.equal(createHash('sha256').update(pdf).digest('hex'),
    '446b97ccbd1a9634d8882d81fa5bb827377547b11e76bc927e436b4bc1161218');
});
check('links_locais_dos_documentos_atuais', () => {
  for (const name of ['README.md', 'projeto_humanos (1).md', 'projeto_agentes (1).md', 'AUDITORIA.md', 'auditoria/fontes_verificadas.md']) {
    const full = resolve(root, name);
    const text = readFileSync(full, 'utf8');
    assert.ok(!text.includes('\uFFFD'), `Caractere de substituição em ${name}`);
    for (const match of text.matchAll(/\[[^\]]*\]\((<[^>]+>|[^)\s]+)\)/g)) {
      const link = match[1].replace(/^<|>$/g, '');
      if (/^(https?:|mailto:|#)/.test(link)) continue;
      assert.ok(existsSync(resolve(dirname(full), link.split('#')[0])), `Link local ausente: ${name}: ${link}`);
    }
  }
});

const sampleIndex = process.argv.indexOf('--sample-dir');
let sample = null;
if (sampleIndex !== -1) {
  const directory = process.argv[sampleIndex + 1];
  assert.ok(directory, 'Informe o diretório após --sample-dir');
  function readSample(side) {
    const file = readdirSync(directory).find(x => x === `xauusd-h1-${side}-2026-10-30-2026-11-03.csv`);
    assert.ok(file, `Amostra ${side} ausente`);
    const rows = readFileSync(resolve(directory, file), 'utf8').trim().split(/\r?\n/);
    assert.equal(rows.shift(), 'timestamp,open,high,low,close');
    return rows.map(row => row.split(',').map(Number));
  }
  check('amostra_Dukascopy_bid_ask_alinhada', () => {
    const bid = readSample('bid'), ask = readSample('ask');
    assert.equal(bid.length, 69);
    assert.equal(ask.length, bid.length);
    for (let i = 0; i < bid.length; i++) {
      assert.equal(ask[i][0], bid[i][0]);
      assert.ok(bid[i].every(Number.isFinite) && ask[i].every(Number.isFinite));
      assert.ok(ask[i][1] >= bid[i][1] && ask[i][4] >= bid[i][4]);
      if (i) assert.ok(bid[i][0] > bid[i - 1][0]);
    }
    sample = { rows: bid.length, first: new Date(bid[0][0]).toISOString(), last: new Date(bid.at(-1)[0]).toISOString() };
  });
}

console.log(JSON.stringify({ status: 'passed', scope: 'plan_and_algebra_only', checks: passed.length, passed, sample }, null, 2));
