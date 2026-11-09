"""Build local design studies. Reads published aggregates; never reruns the study."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOKENS = json.loads((HERE / "tokens.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / "results/summary.json").read_text(encoding="utf-8"))
PAIRED = list(csv.DictReader((ROOT / "results/T2_hourly_paired.csv").open(encoding="utf-8")))
TEAM = "Gabriel Navarro · Lorenzo Cavalcante · Rodrigo Menin"
TITLES = ["Capa", "Identidade & paleta", "Tipografia & componentes", "Processo de pesquisa", "Fidelidade de preço", "Convergência & custos", "Horizonte de manutenção", "Tese & conclusão"]


def n(value: float, digits: int = 1, signed: bool = False) -> str:
    text = f"{abs(value):,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return ("−" if value < 0 else "+" if signed else "") + text


def v(key: str, digits: int = 1, signed: bool = False) -> str:
    value = DATA[key]
    return f'<span data-claim="{key}" data-raw="{value}">{n(value, digits, signed)}</span>'


def symbol(theme: str, label: bool = True) -> str:
    attrs = f'role="img" aria-label="{TOKENS[theme]["symbol"]}"' if label else 'aria-hidden="true"'
    paths = {
        "aureo": '<path d="M18 23h55l8 22H10z" fill="currentColor"/><path d="M31 55h55l8 22H23z" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9 47v7m-3-7h6m-6 7h6" fill="none" stroke="currentColor" stroke-width="1"/>',
        "vertice": '<path d="M7 18h23l27 32h35" fill="none" stroke="currentColor" stroke-width="4"/><path d="M7 82h23l27-32" fill="none" stroke="var(--reference,#8CD1DD)" stroke-width="4"/><path d="m57 38 12 12-12 12-12-12z" fill="var(--bg,#0C1522)" stroke="currentColor" stroke-width="3"/><path d="M7 8v84M92 8v84" stroke="currentColor" stroke-width="1" opacity=".25"/>',
        "meridiano": '<circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="2"/><path d="M28.1 28.1a31 31 0 1 0 43.8 0" fill="none" stroke="var(--reference,#ABC0AF)" stroke-width="2"/><path d="M50 3v13M50 84v13M3 50h13M84 50h13M28 28l-9-9m53 9 9-9" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="50" cy="50" r="4" fill="currentColor"/>',
    }
    return f'<svg class="symbol" viewBox="0 0 100 100" {attrs}>{paths[theme]}</svg>'


def footer(theme: str, index: int, source: str = "Estudo de identidade · O preço da promessa") -> str:
    return f'<footer class="slide-footer"><span class="footer-brand">{symbol(theme,False)} BitFlow</span><span class="source">{source}</span><span class="slide-index">{index:02d} / 08</span></footer>'


def slide(theme: str, index: int, classes: str, content: str, source: str = "Estudo de identidade · O preço da promessa") -> str:
    return f'<section class="slide-shell" data-title="{TITLES[index-1]}" aria-label="Slide {index}: {TITLES[index-1]}"><article class="slide {classes}" aria-labelledby="title-{index}">{content}{footer(theme,index,source)}</article></section>'


def eyebrow(text: str) -> str:
    return f'<p class="eyebrow">{text}</p>'


def palette(theme: str) -> str:
    roles = [("background", "Base"), ("gold", "Ouro"), ("paper", "Texto / claro"), ("reference", "Referência"), ("negative", "Perda")]
    return '<div class="palette">' + ''.join(f'<div class="swatch"><div class="swatch-color" style="background:{TOKENS[theme]["colors"][key]}"></div><div class="swatch-name">{name}</div><div class="swatch-hex">{TOKENS[theme]["colors"][key]}</div></div>' for key, name in roles) + '</div>'


def chips() -> str:
    return '<div class="evidence-chips"><span class="chip">Observado</span><span class="chip assumed">Hipótese</span><span class="chip unknown">Indisponível</span></div>'


def fidelity_chart() -> str:
    # Horizontal paired bars; shared zero and scale, exact reported aggregates.
    parts = ['<svg class="chart fidelity-chart" viewBox="0 0 730 330" role="img" aria-label="Desvio absoluto em bps log: mediana 36,4 em horários comuns e 48,4 na reabertura; percentil 95 de 120,1 e 164,2, respectivamente.">']
    x0, width = 158, 510
    for tick in [0, 50, 100, 150, 200]:
        x = x0 + tick / 200 * width
        parts += [f'<line class="gridline" x1="{x}" x2="{x}" y1="41" y2="258"/>', f'<text class="axis-label" x="{x}" y="282" text-anchor="middle">{tick}</text>']
    for y, prefix, label, count in [(70, "common_hours", "Horários comuns", "36.572 horas"), (183, "reopen", "Reabertura", "301 fins de semana")]:
        parts += [f'<text class="chart-label" x="0" y="{y+7}">{label}</text><text class="axis-label" x="0" y="{y+30}">{count}</text>']
        for dy, metric, cls in [(0, "median_abs_bps", "series-primary"), (35, "p95_abs_bps", "series-reference")]:
            key = f"{prefix}_{metric}"
            value = DATA[key]
            w = value / 200 * width
            parts += [f'<rect class="{cls}" x="{x0}" y="{y+dy-12}" width="{w}" height="22"/>', f'<text class="chart-value" data-claim="{key}" data-raw="{value}" x="{x0+w+11}" y="{y+dy+5}">{n(value)}</text>']
    parts += ['<rect class="series-primary" x="158" y="312" width="12" height="8"/><text class="caption" x="178" y="320">Mediana</text><rect class="series-reference" x="306" y="312" width="12" height="8"/><text class="caption" x="326" y="320">Percentil 95</text><text class="axis-label" x="668" y="320" text-anchor="end">bps log →</text></svg>']
    return ''.join(parts)


def waterfall() -> str:
    gross, cost, net = [DATA[k] for k in ("mean_gross_mid_bps", "mean_total_modeled_cost_bps", "mean_trade_model_bps")]
    y = lambda value: 100 - value * 3.0
    parts = ['<svg class="chart waterfall" viewBox="0 0 710 342" role="img" aria-label="Decomposição média: ganho bruto de 4,53 bps, menos 44,54 bps de custos modelados, saldo de menos 40,01 bps por perna de ouro. Financiamento e empréstimo desconhecidos.">']
    for tick in [0, -20, -40, -60]:
        parts += [f'<line class="gridline" x1="58" x2="690" y1="{y(tick)}" y2="{y(tick)}"/><text class="axis-label" x="43" y="{y(tick)+4}" text-anchor="end">{str(tick).replace("-","−")}</text>']
    parts += [f'<rect class="series-primary" x="91" y="{y(gross)}" width="132" height="{gross*3}"/><line class="waterfall-connector" x1="223" x2="292" y1="{y(gross)}" y2="{y(gross)}" stroke="currentColor" stroke-dasharray="4 5" opacity=".4"/>', f'<rect class="series-reference" x="292" y="{y(gross)}" width="132" height="{cost*3}"/><line x1="424" x2="493" y1="{y(net)}" y2="{y(net)}" stroke="currentColor" stroke-dasharray="4 5" opacity=".4"/>', f'<rect class="series-negative" x="493" y="100" width="132" height="{-net*3}"/>']
    for x, value, label, key, above in [(157,gross,"Bruto","mean_gross_mid_bps",True),(358,-cost,"Custos modelados","mean_total_modeled_cost_bps",True),(559,net,"Saldo modelado","mean_trade_model_bps",False)]:
        ty = 61 if above else y(net)+28
        parts += [f'<text class="chart-value" x="{x}" y="{ty}" text-anchor="middle" data-claim="{key}" data-raw="{DATA[key]}">{n(value,1,True)}</text>',f'<text class="chart-label" x="{x}" y="310" text-anchor="middle">{label}</text>']
    parts += ['<text class="axis-label" x="58" y="20">Média · bps por perna de ouro</text></svg>']
    return ''.join(parts)


def cost_chart() -> str:
    # Algebra matches the declared baseline: token 32 + 0*t; ETF 1 + annual fee*t/12.
    x = lambda month: 68 + month / 48 * 595
    y = lambda bps: 340 - bps / 180 * 295
    parts = ['<svg class="chart costs-chart" viewBox="0 0 760 410" role="img" aria-label="Custos-base modelados em bps ao longo de 48 meses: PAXG constante em 32; GLD começa em 1 e soma 40 por ano; GLDM começa em 1 e soma 10 por ano. Cruzamentos em 9,3 e 37,2 meses.">']
    for tick in [0, 40, 80, 120, 160]:
        parts += [f'<line class="gridline" x1="68" x2="663" y1="{y(tick)}" y2="{y(tick)}"/><text class="axis-label" x="50" y="{y(tick)+4}" text-anchor="end">{tick}</text>']
    for tick in [0,12,24,36,48]:
        parts += [f'<text class="axis-label" x="{x(tick)}" y="365" text-anchor="middle">{tick}</text>']
    parts += [f'<path d="M{x(0)} {y(32)}H{x(48)}" fill="none" stroke="var(--chart-gold,var(--gold))" stroke-width="3"/>', f'<path d="M{x(0)} {y(1)}L{x(48)} {y(161)}" fill="none" stroke="var(--chart-ref,var(--reference))" stroke-width="2.5"/>',f'<path d="M{x(0)} {y(1)}L{x(48)} {y(41)}" fill="none" stroke="currentColor" stroke-width="2.5" stroke-dasharray="6 5"/>']
    for month in [DATA['GLD_crossing_months'],DATA['GLDM_crossing_months']]:
        parts += [f'<circle cx="{x(month)}" cy="{y(32)}" r="5" fill="var(--chart-gold,var(--gold))"/><line x1="{x(month)}" x2="{x(month)}" y1="{y(32)+10}" y2="340" stroke="currentColor" opacity=".3" stroke-dasharray="3 5"/><text class="axis-label" x="{x(month)}" y="{y(32)-15}" text-anchor="middle">{n(month)} m</text>']
    parts += [f'<text class="chart-label" x="679" y="{y(161)+6}">GLD</text>',f'<text class="chart-label" x="679" y="{y(41)-5}">GLDM</text>',f'<text class="chart-label" x="679" y="{y(32)+17}">PAXG</text>','<text class="axis-label" x="68" y="20">Custo modelado · bps</text><text class="axis-label" x="663" y="397" text-anchor="end">Meses →</text></svg>']
    return ''.join(parts)


def trajectory_chart() -> str:
    values = [float(row['median_abs_bps']) for row in PAIRED]
    xs = [96,350,604]
    y = lambda value: 300 - value/60*240
    parts = ['<svg class="chart trajectory-chart" viewBox="0 0 690 380" role="img" aria-label="Trajetória da mediana do desvio absoluto nos mesmos 301 fins de semana: 48,4 na reabertura, 37,1 uma hora depois e 38,0 sete horas depois. Valores em bps log.">']
    for tick in [0,20,40,60]:
        parts += [f'<line class="gridline" x1="65" x2="638" y1="{y(tick)}" y2="{y(tick)}"/><text class="axis-label" x="42" y="{y(tick)+4}">{tick}</text>']
    parts += [f'<path d="M{xs[0]} {y(values[0])}L{xs[1]} {y(values[1])}L{xs[2]} {y(values[2])}" fill="none" stroke="var(--gold)" stroke-width="3"/>']
    for px,value,label in zip(xs, values, ['Reabertura','+1 hora','+7 horas']):
        parts += [f'<circle cx="{px}" cy="{y(value)}" r="7" fill="var(--bg)" stroke="var(--gold)" stroke-width="3"/><text class="chart-value" x="{px}" y="{y(value)-26}" text-anchor="middle">{n(value)}</text><text class="chart-label" x="{px}" y="340" text-anchor="middle">{label}</text>']
    parts += ['<text class="axis-label" x="65" y="20">Mediana absoluta · bps log</text></svg>']
    return ''.join(parts)


def orbit_art() -> str:
    import math
    ticks = []
    for i in range(60):
        a=math.radians(i*6-90)
        r1=186 if i%5==0 else 192
        ticks.append(f'<line x1="{220+math.cos(a)*r1:.2f}" y1="{220+math.sin(a)*r1:.2f}" x2="{220+math.cos(a)*198:.2f}" y2="{220+math.sin(a)*198:.2f}" stroke="currentColor" opacity="{.65 if i%5==0 else .2}"/>')
    return '<svg class="orbit-art" viewBox="0 0 440 440" role="img" aria-label="Símbolo conceitual: órbita contínua do token e órbita interrompida da referência."><circle cx="220" cy="220" r="166" fill="none" stroke="currentColor" stroke-width="1.3"/>'+''.join(ticks)+'<circle cx="220" cy="220" r="141" fill="none" stroke="var(--reference)" stroke-width="2" stroke-dasharray="641 245" transform="rotate(-40 220 220)"/><path d="M220 15v44M220 381v44" stroke="currentColor"/><circle cx="328" cy="129" r="5" fill="var(--reference)"/><text x="220" y="235" text-anchor="middle" class="orbit-number">24/7</text><text x="220" y="268" text-anchor="middle" class="orbit-label">ACESSO CONTÍNUO</text><text x="220" y="323" text-anchor="middle" class="orbit-small">REFERÊNCIA COM JANELAS</text></svg>'


def reference_art() -> str:
    return '<svg class="reference-art" viewBox="0 0 440 390" role="img" aria-label="Diagrama conceitual de token e ouro normalizados em USD para uma comparação comum."><path d="M20 66H130L235 195H415" fill="none" stroke="var(--gold)" stroke-width="2"/><path d="M20 324H130L235 195" fill="none" stroke="var(--reference)" stroke-width="2"/><path d="M20 28V357M415 28V357" stroke="currentColor" opacity=".15"/><path d="m235 176 19 19-19 19-19-19z" fill="var(--bg)" stroke="var(--gold)" stroke-width="2"/><circle cx="20" cy="66" r="4" fill="var(--gold)"/><circle cx="20" cy="324" r="4" fill="var(--reference)"/><circle cx="415" cy="195" r="4" fill="var(--gold)"/><text x="20" y="45" class="diagram-label">TOKEN / CÂMBIO</text><text x="20" y="354" class="diagram-label">REFERÊNCIA / OURO</text><text x="281" y="180" class="diagram-unit">USD</text><text x="235" y="249" text-anchor="middle" class="diagram-label">BASE COMUM</text><text x="235" y="380" text-anchor="middle" class="diagram-small">NORMALIZAR → COMPARAR → TESTAR</text></svg>'


def aureo() -> list[str]:
    from aureo_direction import build_aureo
    return build_aureo(
        slide=slide, symbol=symbol, v=v, n=n, data=DATA, team=TEAM, waterfall=waterfall
    )

def vertice() -> list[str]:
    t='vertice'; out=[]
    out.append(slide(t,1,'v-cover grid-texture',f'''<div class="v-cover-top"><span>{symbol(t,False)} BITFLOW / RESEARCH</span><span class="mono">FGV EESP · 2026</span></div><p class="v-cover-tags mono">PAXG / XAUUSD / GLD / GLDM</p><h1 id="title-1" class="v-cover-title">O preço<br>da promessa<span>.</span></h1><p class="v-cover-subtitle">Preço é sinal. Custo é filtro.<br>Fidelidade e acesso 24/7 no ouro tokenizado.</p><div class="v-cover-diagram">{reference_art()}</div><div class="v-cover-metrics"><div><span class="mono">01 / AMOSTRA EM USD</span><strong>{v('valid_hours',0)}</strong><small>horas válidas</small></div><div><span class="mono">02 / REABERTURA</span><strong>{v('valid_weekends',0)}</strong><small>fins de semana válidos</small></div><div><span class="mono">03 / CAUDA DO DESVIO</span><strong>{v('reopen_p95_abs_bps')}</strong><small>bps log · percentil 95</small></div></div>''',TEAM))
    out.append(slide(t,2,'v-identity',f'''{eyebrow('02 / VÉRTICE · LÓGICA VISUAL')}<h1 id="title-2" class="slide-title">Uma referência. Duas trajetórias.</h1><div class="v-identity-grid"><div class="v-symbol-board">{symbol(t)}<span class="mono">REFERÊNCIA COMUM</span><p>Normalizar a unidade antes de comparar.<br>O vértice é uma base comum,<br>não uma promessa de convergência.</p></div><div class="v-palette-board">{palette(t)}<div class="v-design-principles"><div><span class="mono">GRADE</span><b>12 colunas</b><p>Alinhamento constante.</p></div><div><span class="mono">GEOMETRIA</span><b>Linhas e vértices</b><p>Relações explícitas.</p></div><div><span class="mono">SEMÂNTICA</span><b>Cor + rótulo</b><p>Leitura independente da cor.</p></div></div></div></div>'''))
    out.append(slide(t,3,'v-type grid-texture',f'''{eyebrow('TIPOGRAFIA / ESCALA / ESTADOS')}<h1 id="title-3" class="slide-title">Precisão também é composição.</h1><div class="v-type-grid"><div><span class="eyebrow">SPACE GROTESK / DISPLAY</span><p class="v-type-heading">Comparar.<br>Medir. Questionar.</p><div class="v-type-numbers mono">0123456789<br><span>−40,0 bps</span></div><p class="small-copy muted">IBM Plex Mono: unidades, timestamps e medidas.<br>Manrope: explicação, contexto e ressalvas.</p></div><div class="v-token-table"><div><span>Display</span><b>88–104 px</b></div><div><span>Títulos</span><b>50–62 px</b></div><div><span>Corpo</span><b>20–24 px</b></div><div><span>Notas</span><b>13–15 px</b></div><div><span>Margem</span><b>56 px</b></div><div><span>Espaçamento</span><b>8 / 16 / 24 / 32</b></div></div></div><div class="v-evidence-bar"><span class="eyebrow">CONTRATO DE LEITURA</span>{chips()}<span class="fine muted">Indisponível ≠ zero.</span></div>'''))
    nodes=[('01','Fontes','PAXG · FX · XAU'),('02','Unidade','USD observado'),('03','Calendário','Ouro ativo'),('04','Comparação','Desvio e custos')]
    out.append(slide(t,4,'v-method grid-texture',f'''{eyebrow('MÉTODO / ANTES DA ESTATÍSTICA')}<h1 id="title-4" class="slide-title">Normalizar antes de comparar.</h1><p class="v-method-lede">Uma amostra sincronizada, com exclusões explícitas e sem preencher informação ausente.</p><div class="v-flow">{''.join(f'<div><span class="mono">{a} /</span><h2>{b}</h2><p>{c}</p></div>' for a,b,c in nodes)}</div><div class="v-selection"><div><span class="eyebrow">FINS DE SEMANA CANDIDATOS</span><strong>{v('candidate_weekends',0)}</strong></div><span class="v-select-arrow">→</span><div><span class="eyebrow">FINS DE SEMANA VÁLIDOS</span><strong class="gold">{v('valid_weekends',0)}</strong></div><p>Calendário, câmbio e atividade<br>da referência determinam a entrada.<br>O resultado não determina a seleção.</p></div><div class="v-method-note mono">REGRA: SINAL CONCLUÍDO → ENTRADA NO MINUTO SEGUINTE</div>''','Fontes: results/coverage.csv e results/exclusions.csv · janela e parâmetros congelados'))
    out.append(slide(t,5,'v-data',f'''{eyebrow('EVIDÊNCIA 01 / FIDELIDADE EM USD')}<h1 id="title-5" class="slide-title">Na reabertura, a cauda se amplia.</h1><div class="v-data-grid"><div><div class="v-plot-heading mono">DESVIO ABSOLUTO / bps log</div>{fidelity_chart()}</div><aside><div class="v-terminal-label mono">LEITURA DA REABERTURA</div><div class="v-table-row"><span>Mediana</span><b>{v('reopen_median_abs_bps')}</b></div><div class="v-table-row"><span>Percentil 95</span><b>{v('reopen_p95_abs_bps')}</b></div><div class="v-table-row"><span>Amostra</span><b>{v('valid_weekends',0)}</b></div><p>Diferenças descritivas.<br>Sem atribuição de causa<br>à infraestrutura ou à competição.</p></aside></div><div class="v-source-strip"><span class="chip">Preços observados</span><span class="mono">36.572 horas / 301 fins de semana / escala comum</span></div>''','Fonte: results/T1_fidelidade.csv · comparação descritiva, sem teste causal'))
    out.append(slide(t,6,'v-pnl',f'''{eyebrow('EVIDÊNCIA 02 / CONVERGÊNCIA CONDICIONAL')}<h1 id="title-6" class="slide-title">O bruto é pequeno. O atrito é decisivo.</h1><div class="v-pnl-grid"><div><div class="v-plot-heading mono">P&L MÉDIO / HIPÓTESE-BASE</div>{waterfall()}</div><aside><span class="eyebrow">APÓS CUSTOS MODELADOS</span><strong class="negative">{v('mean_trade_model_bps')}</strong><span class="mono">bps / perna de ouro</span><div class="v-pnl-counts"><div><b>{v('evaluated_trades',0)}</b><span>operações avaliadas</span></div><div><b>{v('signals_unassessed',0)}</b><span>sinais não avaliados</span></div></div><span class="chip unknown">Financiamento desconhecido</span></aside></div><p class="v-pnl-foot">Custos supostos: token 10 bps/execução + spread cheio 10; ouro 1/execução; FX 2/ida e volta; slippage 2/execução.<br>OHLC não comprova execução simultânea, liquidez ou acesso a empréstimo.</p>''','Fonte: results/T2_baseline_inference.csv · saldo antes de financiamento e empréstimo não observados'))
    out.append(slide(t,7,'v-cost',f'''{eyebrow('EVIDÊNCIA 03 / CUSTO E HORIZONTE')}<h1 id="title-7" class="slide-title">O prazo altera o custo relativo.</h1><div class="v-cost-grid"><div>{cost_chart()}</div><aside><span class="eyebrow">EQUILÍBRIO MODELADO</span><div><span>GLD</span><strong>{v('GLD_crossing_months')}<small>meses</small></strong></div><div><span>GLDM</span><strong>{v('GLDM_crossing_months')}<small>meses</small></strong></div><p>USD · antes de impostos.<br>Igual possibilidade de acesso.<br>Sem retirada na rota-base.</p></aside></div><div class="v-cost-note mono">PAXG: 32 bps / GLD e GLDM: 1 bp inicial + 40 e 10 bps/ano / armazenamento do token: zero suposto</div>''','Fonte: results/T3_baseline.csv · curvas algébricas da hipótese-base, não preços ou retornos previstos'))
    out.append(slide(t,8,'v-close grid-texture',f'''{eyebrow('CONCLUSÃO / O QUE A EVIDÊNCIA PERMITE')}<h1 id="title-8" class="slide-title">Diferença de preço<br>não garante captura.</h1><div class="v-close-equation"><div><strong>{v('mean_gross_mid_bps',1,True)}</strong><span>BRUTO</span></div><b>−</b><div><strong>{v('mean_total_modeled_cost_bps')}</strong><span>CUSTOS MODELADOS</span></div><b>=</b><div class="negative"><strong>{v('mean_trade_model_bps')}</strong><span>SALDO / bps</span></div></div><div class="v-close-notes"><p><span class="mono">LIMITE 01</span>Execução, financiamento e acesso<br>a short não foram comprovados.</p><p><span class="mono">LIMITE 02</span>55 trajetórias &lt; mínimo de 78.<br>Cenários com sensibilidade determinística.</p><p><span class="mono">TESE</span>Acesso contínuo.<br>Vantagem econômica condicional.</p></div>''',TEAM))
    return out


def meridiano() -> list[str]:
    t='meridiano'; out=[]
    out.append(slide(t,1,'m-cover',f'''<div class="m-cover-top"><span>{symbol(t,False)} BITFLOW</span><span class="mono">OURO / TEMPO / ACESSO</span><span>FGV EESP · 2026</span></div><h1 id="title-1" class="m-cover-title">O preço<br>da <em>promessa.</em></h1><p class="m-cover-copy">Um token contínuo.<br>Um mercado com janelas.<br>Uma vantagem a ser medida.</p><div class="m-cover-orbit">{orbit_art()}</div><div class="m-cover-bottom"><span class="mono">FIDELIDADE, CUSTOS E ACESSO 24/7 NO PAXG</span><span>Pesquisa aplicada ao ouro tokenizado.</span></div>''',TEAM))
    out.append(slide(t,2,'m-identity light',f'''{eyebrow('03 / MERIDIANO · LÓGICA VISUAL')}<div class="m-identity-grid"><div class="m-symbol-board">{symbol(t)}<span class="mono">JANELA DE MERCADO</span></div><div><h1 id="title-2" class="slide-title">O tempo é a forma<br>do sistema.</h1><p class="body-copy">Uma órbita contínua e outra interrompida.<br>O token e a referência compartilham<br>um centro, mas não o mesmo calendário.</p><p class="small-copy muted">Arcos criam a identidade. Eixos e rótulos medem os dados.<br>O símbolo não representa porcentagem ou retorno.</p></div></div><div class="m-palette-row">{palette(t)}</div>'''))
    out.append(slide(t,3,'m-type',f'''{eyebrow('CONTRASTE / RITMO / CLAREZA')}<h1 id="title-3" class="slide-title">O espaço também explica.</h1><div class="m-type-grid"><div><p class="m-type-specimen">Tempo para ler.<br>Espaço para <em>entender.</em></p><p class="small-copy muted">Instrument Serif conduz a narrativa.<br>Manrope organiza a explicação.<br>IBM Plex Mono ancora medidas e datas.</p></div><div class="m-type-scale"><div><span class="mono">TÍTULO</span><strong>60–76</strong><small>px</small></div><div><span class="mono">CORPO</span><strong>22–26</strong><small>px</small></div><div><span class="mono">MARGEM</span><strong>56</strong><small>px</small></div></div></div><div class="m-type-bottom"><span class="mono">BASE 8 PX / CANVAS 16:9 / UMA MENSAGEM POR LÂMINA</span>{chips()}</div>'''))
    out.append(slide(t,4,'m-method light',f'''{eyebrow('CALENDÁRIO / DA OBSERVAÇÃO À COMPARAÇÃO')}<h1 id="title-4" class="slide-title">O token não fecha.<br>A referência tem janelas.</h1><div class="m-calendar"><div class="m-calendar-labels"><span>Sexta<br><b>Fechamento</b></span><span>Fim de semana<br><b>Referência fechada</b></span><span>Domingo<br><b>Reabertura</b></span></div><div class="m-time-track"><span class="mono">TOKEN</span><i></i><b>CONTÍNUO</b></div><div class="m-time-track gold-track"><span class="mono">OURO</span><i></i><b>COM JANELAS</b></div><div class="m-calendar-window"></div></div><div class="m-method-steps"><span>01<br><b>Coletar</b></span><span>02<br><b>Converter em USD</b></span><span>03<br><b>Respeitar o calendário</b></span><span>04<br><b>Medir e testar custos</b></span></div><p class="m-calendar-note">Esquema de calendário, sem escala temporal. Preços ausentes durante o fechamento não são preenchidos.</p>''','Processo: fontes → câmbio observado → atividade do ouro → comparação sob hipóteses explícitas'))
    out.append(slide(t,5,'m-data',f'''{eyebrow('REABERTURA / A TRAJETÓRIA DO DESVIO')}<h1 id="title-5" class="slide-title">O preço reencontra a referência.</h1><div class="m-data-grid"><aside><strong>{v('reopen_median_abs_bps')}</strong><span class="mono">bps log / MEDIANA INICIAL</span><p>A mediana cai após uma hora.<br>Isso descreve o desvio;<br>não mede lucro de uma operação.</p><span class="chip">Mesmos 301 fins de semana</span></aside><div>{trajectory_chart()}</div></div><div class="m-data-caption"><span>Tempo relativo à reabertura da referência</span><span class="mono">T₀ / T₀ + 1h / T₀ + 7h</span></div>''','Fonte: results/T2_hourly_paired.csv · mesma amostra nos três instantes · sem interpretação causal'))
    out.append(slide(t,6,'m-pnl',f'''{eyebrow('CONVERGÊNCIA / ENTRE O SINAL E A CAPTURA')}<h1 id="title-6" class="slide-title">O atrito permanece no caminho.</h1><div class="m-pnl-grid"><div><div class="m-entry-timeline"><div><span class="mono">01 / SINAL</span><h2>Minuto concluído</h2><p>A informação precisa estar disponível.</p></div><div><span class="mono">02 / ENTRADA</span><h2>Minuto seguinte</h2><p>Sem antecipar o preço de execução.</p></div><div><span class="mono">03 / SAÍDA</span><h2>Após 6 horas</h2><p>Quantidades fixas nas duas pernas.</p></div></div></div><aside><span class="eyebrow">SALDO MÉDIO MODELADO</span><strong class="negative">{v('mean_trade_model_bps')}</strong><span class="mono">bps / PERNA DE OURO</span><div class="m-pnl-decomposition"><div><b>{v('mean_gross_mid_bps',1,True)}</b><span>bruto médio</span></div><div><b>{v('mean_total_modeled_cost_bps')}</b><span>custos modelados</span></div></div><p>44 operações avaliadas; 16 sinais incompletos.<br>Antes de financiamento e empréstimo desconhecidos.</p></aside></div><p class="m-pnl-note">Hipótese-base: token 10 bps/execução + spread cheio 10; ouro 1/execução; FX 2/ida e volta; slippage 2/execução.</p>''','Fonte: results/T2_baseline_inference.csv · preços de minuto não comprovam execução simultânea'))
    out.append(slide(t,7,'m-cost light',f'''{eyebrow('HORIZONTE / O TEMPO NA CONTA')}<h1 id="title-7" class="slide-title">O custo também tem calendário.</h1><p class="m-cost-lede">Marcos de equilíbrio na comparação de custo-base com ETFs.</p><div class="m-horizons"><div><span class="mono">PAXG × GLD</span><strong>{v('GLD_crossing_months')}</strong><em>meses</em><span class="m-horizon-line"></span><p>40 bps ao ano no ETF.</p></div><div><span class="mono">PAXG × GLDM</span><strong>{v('GLDM_crossing_months')}</strong><em>meses</em><span class="m-horizon-line"></span><p>10 bps ao ano no ETF.</p></div></div><div class="m-cost-assumptions"><span class="chip assumed">Hipótese-base</span><p>Token: 32 bps de ida e volta; ETF: 1 bp. Armazenamento do token: zero suposto.<br>USD, antes de impostos, sem retirada e com igual possibilidade de acesso.</p></div>''','Fonte: results/T3_baseline.csv · taxas e spread corrente dos ETFs; custos do token supostos'))
    out.append(slide(t,8,'m-close',f'''{eyebrow('O PREÇO DA PROMESSA / CONCLUSÃO')}<h1 id="title-8" class="slide-title">Acesso contínuo.<br>Vantagem <em>condicional.</em></h1><div class="m-close-symbol">{symbol(t)}</div><p class="m-close-copy">Medir a fidelidade. Explicitar o custo.<br>Respeitar o que os dados não mostram.</p><div class="m-close-notes"><div><span class="mono">PREÇO</span><p>Desvios observados<br>não são lucro garantido.</p></div><div><span class="mono">ACESSO</span><p>Livro, latência e empréstimo<br>permanecem limitações.</p></div><div><span class="mono">CENÁRIOS</span><p>55 trajetórias de um mínimo de 78.<br>Sensibilidade determinística aplicada.</p></div></div>''',TEAM))
    return out


ICONS = {
    'grid':'<rect x="3" y="3" width="6" height="6"/><rect x="15" y="3" width="6" height="6"/><rect x="3" y="15" width="6" height="6"/><rect x="15" y="15" width="6" height="6"/>',
    'full':'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5"/>',
    'print':'<path d="M7 8V3h10v5M7 17H4V9h16v8h-3M7 13h10v8H7z"/>',
    'left':'<path d="m14 6-6 6 6 6"/>',
    'right':'<path d="m10 6 6 6-6 6"/>',
    'help':'<circle cx="12" cy="12" r="9"/><path d="M9.4 9a2.7 2.7 0 0 1 5.2 1c0 2-2.6 2-2.6 4m0 2.5v.5"/>',
}


def icon(name: str) -> str:
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'


def page(theme: str, slides: list[str]) -> str:
    token=TOKENS[theme]
    nav=''.join(f'<a href="{TOKENS[t]["file"]}" '+('aria-current="page"' if t==theme else '')+f'>{TOKENS[t]["number"]} / {TOKENS[t]["name"]}</a>' for t in ['aureo','vertice','meridiano'])
    dots=''.join(f'<button class="slide-dot" type="button" aria-label="Ir para slide {i+1}: {title}" aria-current="false"></button>' for i,title in enumerate(TITLES))
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><meta name="description" content="{token['name']}: {token['descriptor']}. Sistema visual de slides para O preço da promessa, da BitFlow."><title>{token['number']} / {token['name']} — BitFlow Design Studies</title><link rel="icon" href="assets/{theme}-symbol.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/presentation.css"><link rel="stylesheet" href="assets/{theme}.css"><script src="assets/presentation.js" defer></script></head>
<body class="theme-{theme}"><header class="viewer-header"><a class="viewer-brand" href="index.html" aria-label="Voltar à biblioteca de sistemas visuais">{symbol(theme,False)}<b>BitFlow</b><span>Design studies</span></a><nav class="direction-links" aria-label="Direções visuais">{nav}</nav><div class="viewer-actions"><button type="button" class="ui-button" data-overview aria-pressed="false" title="Visão geral (G)">{icon('grid')}<span class="button-text">Visão geral</span></button><button type="button" class="ui-button" data-fullscreen aria-pressed="false" title="Tela cheia (F)">{icon('full')}<span class="button-text">Apresentar</span></button><button type="button" class="ui-button icon-button" data-print title="Imprimir ou salvar PDF" aria-label="Imprimir ou salvar PDF">{icon('print')}</button><button type="button" class="ui-button icon-button" data-help title="Atalhos de teclado" aria-label="Abrir atalhos de teclado">{icon('help')}</button></div></header><main class="viewer"><div class="stage" aria-label="Protótipo com oito slides">{''.join(slides)}</div><div class="viewer-footer"><div class="slide-meta" aria-live="polite"><strong data-counter>01 / 08</strong><span data-current-title>Capa</span></div><nav class="slide-dots" aria-label="Escolher slide">{dots}</nav><div class="arrow-controls"><button type="button" class="ui-button icon-button" data-prev aria-label="Slide anterior">{icon('left')}</button><button type="button" class="ui-button icon-button" data-next aria-label="Próximo slide">{icon('right')}</button></div></div><p class="viewer-note"><a href="../entrega.html">Abrir apresentação científica final ↗</a> · setas para navegar · G para visão geral</p></main><div class="sr-only" data-announcement aria-live="polite"></div><dialog aria-labelledby="help-title"><h2 id="help-title">Atalhos de apresentação</h2><dl><dt>← / →</dt><dd>Slide anterior / próximo</dd><dt>Home / End</dt><dd>Primeiro / último slide</dd><dt>G</dt><dd>Alternar visão geral</dd><dt>F</dt><dd>Alternar tela cheia</dd><dt>Esc</dt><dd>Sair da visão geral ou tela cheia</dd><dt>Ctrl + P</dt><dd>Imprimir os oito slides</dd></dl><button type="button" class="ui-button" data-close-help>Fechar</button></dialog></body></html>'''


def build() -> None:
    for theme, build_slides in [('aureo',aureo),('vertice',vertice),('meridiano',meridiano)]:
        slides=build_slides()
        assert len(slides)==8
        (HERE/TOKENS[theme]['file']).write_text(page(theme,slides),encoding='utf-8')
        standalone=symbol(theme).replace('class="symbol"','xmlns="http://www.w3.org/2000/svg"').replace('var(--reference,#8CD1DD)',TOKENS[theme]['colors']['reference']).replace('var(--reference,#ABC0AF)',TOKENS[theme]['colors']['reference']).replace('var(--bg,#0C1522)',TOKENS[theme]['colors']['background']).replace('currentColor',TOKENS[theme]['colors']['gold'])
        (HERE/f'assets/{theme}-symbol.svg').write_text(standalone,encoding='utf-8')
        print(TOKENS[theme]['file'],len(slides),'slides')


if __name__=='__main__':
    build()
