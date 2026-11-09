"""Scientific deck in Áureo v2: local HTML, vector figures and matching PDF."""
from __future__ import annotations

import html
import json
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from .common import ROOT, dump_json, sha256, utc_now


LABELS={'persistence':'Persistência','zero_basis':'Desvio zero','historical_mean':'Média histórica',
        'linear_adjustment':'Ajuste linear','linear_adjustment_context':'Linear + contexto'}


def n(value,decimals=1):
    if pd.isna(value):return '—'
    return ('−' if float(value)<0 else '')+f'{abs(float(value)):,.{decimals}f}'.replace(',','_').replace('.',',').replace('_','.')


def table(name):return pd.read_csv(ROOT/'results'/name)


def symbol():
    return '<svg class="symbol" viewBox="0 0 100 100" aria-hidden="true"><path d="M18 23h55l8 22H10z" fill="currentColor"/><path d="M31 55h55l8 22H23z" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9 47v7m-3-7h6m-6 7h6" fill="none" stroke="currentColor"/></svg>'


class Book:
    def __init__(self,config):
        self.config=config;self.claims=table('claims.csv').set_index('claim_id');self.page=0;self.usage=[]
        self.figures=json.loads((ROOT/'results/figure_manifest.json').read_text())
        self.base_hash=json.loads((ROOT/'results/config_frozen.json').read_text())['config_hash']
        self.refined_hash=json.loads((ROOT/'results/refinement_config_frozen.json').read_text())['config_hash']

    def v(self,key,decimals=1,percent=False,plus=False):
        raw=self.claims.loc[key,'value'];value=float(raw)
        self.usage.append({'page':self.page,'claim_id':key,'source':self.claims.loc[key,'source_file']})
        text=n(value*100 if percent else value,decimals)
        if plus and value>0:text='+'+text
        if percent:text+='%'
        return f'<span data-claim="{key}" data-raw="{value}">{text}</span>'

    def figure(self,name,svg,sources):
        directory=ROOT/'results/figures_refined';directory.mkdir(exist_ok=True)
        path=directory/(name+'.svg');path.write_text(svg,encoding='utf-8')
        key='figures_refined/'+path.name
        self.figures[key]={'source_files':sources,'sha256':sha256(path),'config_hash':self.base_hash,'refinement_config_hash':self.refined_hash}
        return svg


def svg_open(width,height,label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" class="plot" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(label,quote=True)}">'


def fidelity_figure():
    data=table('T1_fidelidade.csv');data=data[data.period.eq('full')].set_index('sample')
    parts=[svg_open(760,310,'Mediana e percentil 95 do desvio absoluto: 36,4 e 120,1 bps log em horários comuns; 48,4 e 164,2 na reabertura.')]
    x=lambda value:168+value/200*510
    for tick in [0,50,100,150,200]:parts.append(f'<path class="grid" d="M{x(tick)} 25v216"/><text class="tick" x="{x(tick)}" y="265" text-anchor="middle">{tick}</text>')
    for row,(key,label,sample) in enumerate([('common_hours','Horários comuns','36.572 horas'),('reopen','Reabertura','301 fins de semana')]):
        y=63+row*114;d=data.loc[key]
        parts.append(f'<text class="plot-label" x="0" y="{y+6}">{label}</text><text class="minor" x="0" y="{y+28}">{sample}</text>')
        for dy,col,cls in [(0,'median_abs_bps','primary'),(34,'p95_abs_bps','reference')]:
            value=d[col]
            parts.append(f'<rect class="{cls}" x="168" y="{y+dy-12}" width="{value/200*510}" height="20" stroke="none"/><text class="value" x="{x(value)+10}" y="{y+dy+3}">{n(value)}</text>')
    parts.append('<rect class="primary" x="168" y="291" width="11" height="8"/><text class="minor" x="188" y="300">Mediana</text><rect class="reference" x="316" y="291" width="11" height="8"/><text class="minor" x="336" y="300">Percentil 95</text><text class="tick" x="678" y="300" text-anchor="end">bps log →</text></svg>')
    return ''.join(parts)


def model_figure():
    data=table('T8_forecast_summary.csv').set_index('model');parts=[svg_open(780,290,'Erro absoluto médio de previsão: persistência 16,46 bps; ajuste linear 17,72; linear com contexto 18,21. Menor é melhor.')]
    x=lambda value:246+value/25*430
    for tick in [0,5,10,15,20,25]:parts.append(f'<path class="grid" d="M{x(tick)} 25v199"/><text class="tick" x="{x(tick)}" y="250" text-anchor="middle">{tick}</text>')
    for i,model in enumerate(['persistence','linear_adjustment','linear_adjustment_context']):
        value=data.loc[model,'mae_bps'];y=62+i*70
        parts.append(f'<text class="plot-label" x="0" y="{y+6}">{LABELS[model]}</text><rect class="{"primary" if i==0 else "reference"}" x="246" y="{y-15}" width="{value/25*430}" height="25"/><text class="value" x="{x(value)+15}" y="{y+6}">{n(value)}</text>')
    parts.append('<text class="tick" x="676" y="281" text-anchor="end">MAE · bps log →</text></svg>')
    return ''.join(parts)


def calendar_figure():
    return svg_open(650,270,'Esquema sem escala temporal: o token negocia continuamente; a referência de ouro fecha no fim de semana.')+'''
    <text class="minor" x="52" y="30">Sexta / fechamento</text><text class="minor" x="316" y="30" text-anchor="middle">Fim de semana</text><text class="minor" x="595" y="30" text-anchor="end">Domingo / reabertura</text>
    <rect x="192" y="55" width="255" height="152" fill="var(--light-gold)" opacity=".06"/>
    <path d="M192 49v165M447 49v165" stroke="var(--light-gold)" stroke-width="1" stroke-dasharray="3 5"/>
    <text class="plot-label" x="52" y="88">PAXG</text><path d="M52 111H595" fill="none" stroke="var(--light-ref)" stroke-width="2"/>
    <circle cx="52" cy="111" r="4" fill="var(--light-ref)"/><circle cx="595" cy="111" r="4" fill="var(--light-ref)"/>
    <text class="plot-label" x="52" y="166">XAUUSD</text><path d="M52 188H192M447 188H595" fill="none" stroke="var(--light-gold)" stroke-width="2"/>
    <text class="minor" x="319" y="192" text-anchor="middle">referência fechada</text><circle cx="447" cy="188" r="5" fill="var(--light-gold)"/>
    <text class="tick" x="52" y="255">Esquema de calendário, sem escala temporal.</text></svg>'''


def waterfall_figure():
    s=json.loads((ROOT/'results/summary.json').read_text());gross=s['mean_gross_mid_bps'];cost=s['mean_total_modeled_cost_bps'];net=s['mean_trade_model_bps']
    y=lambda value:100-value*3
    parts=[svg_open(710,342,'Média em bps por perna de ouro: ganho bruto 4,53; custos modelados 44,54; saldo antes de financiamento e empréstimo desconhecidos, menos 40,01.')]
    for tick in [0,-20,-40,-60]:parts.append(f'<path class="grid" d="M58 {y(tick)}H690"/><text class="tick" x="43" y="{y(tick)+4}" text-anchor="end">{n(tick,0)}</text>')
    parts.append(f'<rect class="primary" x="91" y="{y(gross)}" width="132" height="{gross*3}"/><rect class="reference" x="292" y="{y(gross)}" width="132" height="{cost*3}"/><rect class="loss" x="493" y="100" width="132" height="{-net*3}"/>')
    parts.append(f'<path d="M223 {y(gross)}H292M424 {y(net)}H493" fill="none" stroke="var(--muted)" stroke-dasharray="4 5" opacity=".5"/>')
    for x,value,label,ty in [(157,gross,'Bruto',61),(358,-cost,'Custos modelados',61),(559,net,'Saldo modelado',y(net)+28)]:
        parts.append(f'<text class="value" x="{x}" y="{ty}" text-anchor="middle">{"+" if value>0 else ""}{n(value)}</text><text x="{x}" y="310" text-anchor="middle" style="font:15px Manrope">{label}</text>')
    parts.append('<text class="tick" x="58" y="20">Média · bps por perna de ouro</text></svg>')
    return ''.join(parts)


def holding_figure():
    parts=[svg_open(690,430,'Equilíbrio de custo sob hipóteses: 9,3 meses contra GLD, 37,2 meses contra GLDM. Eixo de zero a 48 meses.').replace('class="plot"','class="plot horizon-ruler"')]
    x=lambda m:42+m/48*585
    for months,top,name in [(9.3,88,'GLD · 40 bps ao ano'),(37.2,184,'GLDM · 10 bps ao ano')]:
        p=x(months)
        parts.append(f'<text class="horizon-name" x="{p-16}" y="{top}">{name}</text><text class="horizon-number" x="{p-18}" y="{top+79}">{n(months)}</text><path class="horizon-leader" d="M{p} {top+95}V338"/><circle class="horizon-point" cx="{p}" cy="338" r="6"/>')
    parts.append('<text class="horizon-caption" x="42" y="27">Marcos de equilíbrio na hipótese-base</text><path class="horizon-axis" d="M42 338H627"/>')
    for m in [0,12,24,36,48]:parts.append(f'<path class="horizon-axis" d="M{x(m)} 331v14"/><text class="horizon-tick" x="{x(m)}" y="375" text-anchor="middle">{m}</text>')
    parts.append('<text class="horizon-tick" x="627" y="411" text-anchor="end">Meses de manutenção →</text></svg>')
    return ''.join(parts)


def frame(index,title,classes,body,source):
    label=f'{index:02d} / 10' if index<=10 else f'A{index-10} / 03'
    return f'<section class="slide-shell" data-title="{html.escape(title,quote=True)}" aria-label="{html.escape(title,quote=True)}"><article class="slide {classes}" aria-labelledby="title-{index}">{body}<footer class="slide-footer"><span class="footer-brand">{symbol()} BitFlow</span><span class="source">{source}</span><span class="slide-index">{label}</span></footer></article></section>'


def build_slides(b):
    profile=json.loads((ROOT/'config/presentation.json').read_text(encoding='utf-8'));team=' · '.join(profile['members']);out=[]
    b.page=1
    out.append(frame(1,'O preço da promessa','a-cover',f'''<div class="a-cover-imprint">{symbol()}<span>BitFlow</span></div><p class="a-cover-event">FGV EESP<br>7º Datathon de Moedas Digitais</p><h1 id="title-1" class="a-cover-title"><span>O preço</span><span class="a-cover-second"><small>da</small> <em>promessa.</em></span></h1><div class="a-cover-mark">{symbol()}</div><div class="a-cover-registration" aria-hidden="true"><i></i><i></i></div><p class="a-cover-description">Fidelidade, custos e acesso 24/7<br>no ouro tokenizado.</p><p class="a-cover-question">O desvio se ajusta.<br>Quanto disso pode ser capturado?</p><span class="a-cover-date">PAXG / 2020—2026</span>''',html.escape(team)))
    b.page=2
    calendar=b.figure('V0_calendario',calendar_figure(),['config/params.json'])
    out.append(frame(2,'O problema do acesso contínuo','s-problem light',f'''<p class="a-section-note">Problema / Acesso e referência</p><h1 id="title-2" class="section-heading">O token não fecha.<br>A referência tem janelas.</h1><p class="problem-reading">Negociar a qualquer hora<br>não assegura o mesmo preço<br>nem a captura de uma diferença.</p><div class="problem-calendar">{calendar}</div><p class="problem-caption">Perguntamos quando o desvio aumenta, quanto dele se ajusta e o que resta após custos.</p><p class="problem-definition">Desvio = 10.000 × ln(PAXG em USD / XAUUSD).<br>XAUUSD é uma referência de cotação, não prova de resgate físico ou de acesso ao hedge.</p>''','PAXG/USDT × USDT/USD observados · XAUUSD Dukascopy · unidade: bps log'))
    b.page=3
    out.append(frame(3,'Dados, amostra e qualidade','a-method s-sample',f'''<aside class="a-sample-sheet"><p>RECORTE / 2020—2026</p><h2>O que entra<br>na amostra<br>importa.</h2><div class="a-sample-arithmetic"><div><strong>{b.v('candidate_weekends',0)}</strong><span>fins de semana<br>candidatos</span></div><div class="a-sample-exclusions"><strong>−22</strong><span>exclusões<br>documentadas</span></div><div class="a-sample-total"><strong>{b.v('valid_weekends',0)}</strong><span>fins de semana<br>válidos</span></div></div></aside><p class="a-section-note">Método / Registro de apuração</p><h1 id="title-3" class="slide-title">Moeda, relógio<br>e atividade observados.</h1><div class="a-assay-register"><div class="a-assay-row"><span>01</span><h2>Preço do token</h2><p>Binance PAXG/USDT; arquivos e hashes.</p></div><div class="a-assay-row"><span>02</span><h2>Moeda</h2><p>Bitfinex USDT/USD; checagem com Coinbase.</p></div><div class="a-assay-row"><span>03</span><h2>Referência</h2><p>Dukascopy bid/ask; ouro inativo excluído.</p></div><div class="a-assay-row"><span>04</span><h2>Verificação</h2><p>Calendário NY; ouro comparado com GLD/onças.</p></div></div><div class="a-method-coverage"><strong>{b.v('valid_hours',0)}</strong><p>horas válidas. Janela: 28/08/2020 a 08/11/2026 00:00 UTC, exclusiva.<br>Preço agregado não reconstrói livro, impacto ou simultaneidade.</p></div>''','coverage.csv; exclusions.csv; QA_gold_reference_summary.json · ouro/GLD é checagem, não equivalência de instrumentos'))
    b.page=4
    fig=b.figure('V1_fidelidade',fidelity_figure(),['results/T1_fidelidade.csv'])
    out.append(frame(4,'Fidelidade e ajuste pareado','s-fidelity light',f'''<p class="a-section-note">Evidência / Preço e reabertura</p><h1 id="title-4" class="section-heading">O desvio aumenta.<br>Depois, cede em média.</h1><div class="fidelity-figure">{fig}</div><aside class="paired-reading"><h2>Dentro dos mesmos<br>301 fins de semana</h2><strong>{b.v('refined_b_0_to_b_1h_mean_abs_change_bps')}</strong><span>bps log · mudança após 1h</span><p>IC exploratório de 95%:<br>[{b.v('refined_b_0_to_b_1h_mean_lo')}; {b.v('refined_b_0_to_b_1h_mean_hi')}].</p><div class="paired-later"><b>{b.v('refined_b_0_to_b_7h_mean_abs_change_bps')} bps após 7h</b>IC: [{b.v('refined_b_0_to_b_7h_mean_lo')}; {b.v('refined_b_0_to_b_7h_mean_hi')}].</div></aside><p class="footnote">Contraste pareado: média da mudança em |desvio| dentro de cada semana. Ajuste de preço observado não é lucro de uma operação.</p>''','T1_fidelidade.csv; T7_paired_changes.csv · blocos de 4 semanas do calendário · intervalos exploratórios, sem interpretação causal'))
    b.page=5
    fig=b.figure('V2_modelo',model_figure(),['results/T8_forecast_summary.csv'])
    out.append(frame(5,'Modelagem e validação temporal','s-model',f'''<p class="a-section-note">Modelo / Validação temporal retrospectiva</p><h1 id="title-5" class="section-heading">Prever é diferente<br>de zerar o desvio.</h1><div class="model-figure">{fig}</div><aside class="model-validation"><strong>{b.v('refined_linear_adjustment_n_test',0)}</strong><span>previsões avaliadas</span><p>Alvo: desvio em +7h.<br>Informação disponível em +1h.<br>Treino expansivo, começando<br>com 104 semanas de calendário.</p><p class="model-nogain">O modelo não demonstrou<br>melhora sobre a persistência.</p></aside><p class="footnote">MAE menor é melhor. Linear: {b.v('refined_linear_adjustment_mae_bps')} bps; persistência: {b.v('refined_persistence_mae_bps')} bps. Diferença: {b.v('refined_linear_adjustment_mae_difference_vs_persistence')} bps; IC [{b.v('refined_linear_adjustment_difference_lo')}; {b.v('refined_linear_adjustment_difference_hi')}].</p>''','T8_forecast_summary.csv · cinco referências/modelos no anexo A2 · extensão posterior à análise original, sem busca de hiperparâmetros'))
    b.page=6
    fig=b.figure('V3_custos',waterfall_figure(),['results/T2_baseline_inference.csv'])
    out.append(frame(6,'Convergência e custos','a-pnl',f'''<p class="a-section-note">Convergência / Apuração condicional</p><h1 id="title-6" class="slide-title">O custo fica<br>com a diferença.</h1><div class="a-waterfall-figure">{fig}</div><aside class="a-settlement-sheet"><span class="a-settlement-code">HIPÓTESE-BASE / 6 HORAS</span><h2>Apuração<br>por operação</h2><div class="a-account-row"><span>Ganho bruto</span><b>{b.v('mean_gross_mid_bps',plus=True)}</b></div><div class="a-account-row"><span>Custos modelados</span><b>−{b.v('mean_total_modeled_cost_bps')}</b></div><div class="a-account-total"><span>Saldo médio modelado</span><strong>{b.v('mean_trade_model_bps')}</strong><small>bps por perna de ouro</small></div><p class="a-account-sample">{b.v('evaluated_trades',0)} operações avaliadas.<br>{b.v('signals_unassessed',0)} sinais sem avaliação completa.</p><p class="a-account-unknown">Empréstimo e financiamento<br>continuam desconhecidos.</p></aside><p class="a-pnl-assumptions">Token: 10 bps/execução + spread cheio 10; ouro: 1/execução;<br>FX: 2/ida e volta; slippage: 2/execução. Sinal em +1h; entrada no minuto seguinte.</p>''','T2_baseline_inference.csv · preço de minuto é proxy; execução simultânea e short não comprovados'))
    b.page=7
    out.append(frame(7,'Cobertura e dados ausentes','s-coverage light',f'''<p class="a-section-note">Robustez / Alinhamento e cobertura</p><div class="coverage-lead">{b.v('refined_fx1_evaluated_trades',0)} → {b.v('refined_fx5_evaluated_trades',0)}</div><p class="coverage-subtitle">operações avaliadas · janelas cambiais de 1 e 5 minutos</p><h1 id="title-7" class="section-heading">Mais dados.<br>O mesmo sinal econômico.</h1><table class="coverage-table"><thead><tr><th>Janela de busca</th><th>Sinais</th><th>Avaliados</th><th>Sem avaliação</th><th>Saldo médio / bps</th></tr></thead><tbody><tr><td>1 minuto · primário</td><td>{b.v('refined_fx1_signals',0)}</td><td>{b.v('refined_fx1_evaluated_trades',0)}</td><td>{b.v('refined_fx1_unassessed_signals',0)}</td><td>{b.v('refined_fx1_mean_model_bps')}</td></tr><tr><td>5 minutos · sensibilidade</td><td>{b.v('refined_fx5_signals',0)}</td><td>{b.v('refined_fx5_evaluated_trades',0)}</td><td>{b.v('refined_fx5_unassessed_signals',0)}</td><td>{b.v('refined_fx5_mean_model_bps')}</td></tr></tbody></table><p class="coverage-clock-note">Cinco minutos permitem carregar apenas FX já concluído por até quatro minutos. Token e ouro seguem no minuto exato e ativo.<br>Na mesma amostra original, o saldo é idêntico; a diferença vem da inclusão de novas trajetórias.</p><p class="coverage-missing-note">Os 16 sinais originais não avaliados precisariam de média <b>+{b.v('refined_missing_tipping_mean_bps')} bps</b> para zerar os 60 sinais. É um limiar hipotético, não imputação.</p>''','T9_fx_coverage.csv; T9_fx_common_sample.csv; T9_missingness_summary.csv · 6h, antes de financiamento desconhecido'))
    b.page=8
    fig=b.figure('V4_horizontes',holding_figure(),['results/T3_baseline.csv'])
    out.append(frame(8,'Custo de manutenção e horizonte','a-cost s-holding light',f'''<p class="a-section-note">Manutenção / Token e ETFs</p><h1 id="title-8" class="slide-title">Quando o prazo<br>muda a conta.</h1><p class="a-horizon-reading">O mesmo custo inicial do token.<br>Dois ritmos de cobrança anual.<br>Dois horizontes de equilíbrio.</p><p class="a-horizon-scope">Com armazenamento do token de 10 bps/ano,<br>desaparece o cruzamento favorável contra GLDM.<br>USD, antes de impostos; igual possibilidade de acesso.</p><div class="a-horizon-figure">{fig}</div><div class="a-cost-premises"><span>Rota-base</span><p>Token: 32 bps de ida e volta e armazenamento zero suposto. ETF: 1 bp de ida e volta.<br>Sem retirada. Taxas e spread corrente dos ETFs; taxas e spread do token são hipóteses.</p></div>''','T3_baseline.csv · equilíbrios: GLD '+b.v('GLD_crossing_months')+' meses; GLDM '+b.v('GLDM_crossing_months')+' meses · custo menor não implica risco menor'))
    b.page=9
    out.append(frame(9,'Tese, limites e decisão','s-synthesis',f'''<p class="a-section-note">Interpretação / Evidência e condições</p><h1 id="title-9" class="section-heading">O que a evidência<br>permite afirmar.</h1><div class="synthesis-register"><div class="synthesis-row"><span>01</span><h2>Há ajuste observado.</h2><p>O desvio absoluto cai, em média, após a reabertura.<br>Essa mudança não equivale ao retorno de uma operação.</p></div><div class="synthesis-row"><span>02</span><h2>O desvio persiste.</h2><p>Zerar o desvio foi uma previsão pior que mantê-lo.<br>Os modelos lineares não demonstraram ganho de previsão.</p></div><div class="synthesis-row"><span>03</span><h2>A captura é condicional.</h2><p>Custos modelados excederam o ganho bruto.<br>Short, financiamento, impacto e execução seguem limitados.</p></div><div class="synthesis-row"><span>04</span><h2>Maturidade não provada.</h2><p>O intervalo da tendência em 24 trimestres inclui zero.<br>Cenários anuais primários: 55/78; sensibilidade determinística.</p></div></div>''','T7; T8; T9; T4_trend.csv; T5_sensibilidade.csv · sem identificação causal de infraestrutura ou competição'))
    b.page=10
    out.append(frame(10,'Acesso contínuo, vantagem condicional','a-close',f'''<p class="a-section-note">O preço da promessa / Conclusão</p><h1 id="title-10" class="slide-title">Acesso contínuo.</h1><div class="a-closing-cut" aria-hidden="true"></div><p class="a-closing-answer"><em>Vantagem condicional.</em></p><p class="a-closing-reading">O desvio se ajusta, mas não desaparece de imediato.<br>Nas condições testadas, o atrito supera o ganho bruto.</p><div class="a-closing-limit"><p>Preço observado.<br>Custo sob hipóteses.<br>Execução não comprovada.</p></div>''',html.escape(team)))
    b.page=11
    grid=table('T10_grid_summary.csv')
    rows=''.join(f'<tr><td>{int(r.horizon_hours)} {"hora" if r.horizon_hours==1 else "horas"}</td><td>{int(r.configurations)}</td><td>{int(r.evaluated_trades)}</td><td>{n(r.best_mean_model_bps,2)}</td></tr>' for r in grid.itertuples())
    out.append(frame(11,'A1: Grade econômica e orçamento de custo','s-grid light',f'''<p class="a-section-note">Anexo A1 / Robustez econômica</p><h1 id="title-11" class="section-heading">Até a grade favorável<br>teve média negativa.</h1><table class="grid-table"><thead><tr><th>Horizonte</th><th>Configurações</th><th>Operações</th><th>Melhor média / bps</th></tr></thead><tbody>{rows}</tbody></table><aside class="grid-budget"><strong>{b.v('refined_grid_positive_means',0)} / {b.v('refined_grid_configurations',0)}</strong><span>configurações com média positiva</span><p>Em 6h, o ganho bruto médio<br>de {b.v('mean_gross_mid_bps')} bps é o orçamento<br>contábil para todos os custos.</p><p class="budget-secondary">{b.v('refined_cost_reduction_to_zero_fraction',percent=True)}</p><p>de redução do custo médio-base<br>seria necessária para zerar o saldo.<br>É uma conta amostral, não previsão.</p></aside><p class="footnote">Grade original com FX de 1 minuto. Melhor caso escolhido retrospectivamente; não é uma estratégia validada fora da amostra.<br>As 1.458 combinações não são evidências independentes. Custos financeiros desconhecidos permanecem fora do saldo.</p>''','T10_grid_summary.csv; T10_cost_budget.csv · o intervalo do ganho bruto médio em 6h inclui zero'))
    b.page=12
    models=table('T8_forecast_summary.csv')
    rows=''.join(f'<tr class="{"best-observed" if r.model=="persistence" else ""}"><td>{LABELS[r.model]}</td><td>{n(r.mae_bps,2)}</td><td>{n(r.rmse_bps,2)}</td><td>{n(r.mae_difference_vs_persistence,2)}</td><td>[{n(r.difference_lo,2)}; {n(r.difference_hi,2)}]</td></tr>' for r in models.itertuples())
    out.append(frame(12,'A2: Comparação completa dos modelos','s-model-table',f'''<p class="a-section-note">Anexo A2 / Comparação completa das previsões</p><h1 id="title-12" class="section-heading">Modelo simples, comparação exigente.</h1><div class="model-timeline"><span>104 semanas iniciais de treino</span><i></i><span>Origens expansivas / 2022–2026</span><i></i><span>204 previsões na mesma amostra</span></div><table class="model-comparison"><thead><tr><th>Referência / modelo</th><th>MAE</th><th>RMSE</th><th>Δ MAE vs. persistência</th><th>IC 95% da diferença</th></tr></thead><tbody>{rows}</tbody></table><p class="footnote">Unidade: bps log. Linear: b(+7h) = α + ρ b(+1h). Contexto acrescenta salto do ouro e volatilidade anterior.<br>Alvos do treino concluídos antes da previsão; blocos de semanas do calendário. Extensão retrospectiva, sem holdout prospectivo inédito.</p>''','T8_forecast_summary.csv; T8_forecast_coefficients.csv · MAE menor é melhor; nenhuma busca de hiperparâmetros'))
    b.page=13
    out.append(frame(13,'A3: Fontes e reprodução','s-references light','''<p class="a-section-note">Anexo A3 / Fontes e reprodução</p><h1 id="title-13" class="section-heading">O resultado precisa ser verificável.</h1><div class="references-grid"><div><h2>Dados e instrumentos</h2><p><a href="https://github.com/binance/binance-public-data">Binance Public Data</a> · preços e volume PAXG/USDT.<br><a href="https://docs.bitfinex.com/reference/rest-public-candles">Bitfinex</a> e <a href="https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles">Coinbase</a> · câmbio observado.</p><p><a href="https://www.dukascopy.com/swiss/english/marketwatch/historical/">Dukascopy</a> · referência XAUUSD bid/ask.<br><a href="https://www.spdrgoldshares.com/usa/">GLD</a> e <a href="https://www.spdrgoldshares.com/gldm/">GLDM</a> · taxas e dados dos emissores.</p><p><a href="https://www.paxos.com/terms-and-conditions/pax-gold-terms-conditions">Paxos / termos do PAXG</a> · direitos e condições.<br>Preços não auditam reservas físicas ou custódia.</p></div><div><h2>Método e limites</h2><p><a href="https://otexts.com/fpp3/toolbox.html#time-series-cross-validation">Hyndman &amp; Athanasopoulos</a> · validação temporal.<br><a href="https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf">Bailey et al.</a> · risco de selecionar backtests.</p><p><a href="https://www.nber.org/papers/w2960">Lo &amp; MacKinlay</a> · preços não simultâneos.<br><a href="https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html">pandas / asof backward</a> · alinhamento sem futuro.</p><p>Configuração-base preservada; extensão com snapshot próprio.<br>Claims, figuras vetoriais, testes e hashes no pacote.<br>Pesquisa assistida por IA, com limitações documentadas.</p></div></div><div class="references-command">python run_all.py --all --offline<span>Usa o cache local. Uma instalação nova exige coleta online e Chrome ou Chromium para gerar o PDF.<br>Fontes completas: auditoria/MODELAGEM_REVISAO.md · resultados: results/REFINAMENTO.md.</span></div>''','BitFlow · 10 slides principais + 3 anexos técnicos · código e fontes no pacote de reprodução'))
    return out


def viewer(slides):
    dots=''.join(f'<button class="slide-dot" type="button" aria-label="Ir para slide {i}" aria-current="false"></button>' for i in range(1,len(slides)+1))
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Pesquisa da BitFlow sobre PAXG: fidelidade, ajuste, previsibilidade e captura econômica. Áureo v2."><title>O preço da promessa — BitFlow</title><link rel="icon" href="design-systems/assets/aureo-symbol.svg" type="image/svg+xml"><link rel="stylesheet" href="design-systems/assets/presentation.css"><link rel="stylesheet" href="design-systems/assets/aureo.css"><link rel="stylesheet" href="assets/entrega.css"><script src="design-systems/assets/presentation.js" defer></script></head><body class="theme-aureo science"><header class="viewer-header"><a class="viewer-brand" href="../README.md">{symbol()}<b>BitFlow</b><span>O preço da promessa</span></a><nav class="direction-links" aria-label="Apresentação"><a href="entrega.html" aria-current="page">Pesquisa / Áureo v2</a><a href="entrega.pdf">Abrir PDF</a></nav><div class="viewer-actions"><button class="ui-button" data-overview aria-pressed="false" title="Visão geral (G)">Visão geral</button><button class="ui-button" data-fullscreen aria-pressed="false" title="Tela cheia (F)">Apresentar</button><button class="ui-button" data-print aria-label="Imprimir apresentação">PDF</button><button class="ui-button icon-button" data-help aria-label="Atalhos de teclado">?</button></div></header><main class="viewer"><div class="stage" aria-label="Dez slides científicos e três anexos">{''.join(slides)}</div><div class="viewer-footer"><div class="slide-meta" aria-live="polite"><strong data-counter>01 / 13</strong><span data-current-title>Capa</span></div><nav class="slide-dots" aria-label="Escolher slide">{dots}</nav><div class="arrow-controls"><button class="ui-button icon-button" data-prev aria-label="Slide anterior">←</button><button class="ui-button icon-button" data-next aria-label="Próximo slide">→</button></div></div><p class="viewer-note">10 slides principais + 3 anexos · setas para navegar · G para visão geral · F para tela cheia</p></main><div class="sr-only" data-announcement aria-live="polite"></div><dialog aria-labelledby="help-title"><h2 id="help-title">Atalhos de apresentação</h2><dl><dt>← / →</dt><dd>Anterior / próximo</dd><dt>Home / End</dt><dd>Primeiro / último</dd><dt>G</dt><dd>Visão geral</dd><dt>F</dt><dd>Tela cheia</dd><dt>Ctrl + P</dt><dd>Imprimir com anexos</dd></dl><button class="ui-button" data-close-help>Fechar</button></dialog></body></html>'''


INK_BOUNDS=r'''() => {
 const s=document.querySelector('.slide-shell.is-active .slide'),f=s.getBoundingClientRect(),scale=f.width/1280;
 const ctx=document.createElement('canvas').getContext('2d'),texts=[];const w=document.createTreeWalker(s,NodeFilter.SHOW_TEXT);
 while(w.nextNode()){const node=w.currentNode;if(!node.textContent.trim()||node.parentElement.closest('svg'))continue;
 const st=getComputedStyle(node.parentElement);ctx.font=`${st.fontStyle} ${st.fontWeight} ${st.fontSize} ${st.fontFamily}`;
 const m=ctx.measureText(node.textContent.trim()),range=document.createRange();range.selectNodeContents(node);
 for(const box of range.getClientRects()){if(!box.width||!box.height)continue;texts.push({text:node.textContent.trim().slice(0,80),x:(box.left-f.left)/scale,y:(box.top-f.top)/scale+m.fontBoundingBoxAscent-m.actualBoundingBoxAscent,w:box.width/scale,h:m.actualBoundingBoxAscent+m.actualBoundingBoxDescent});}}
 const outside=texts.filter(r=>r.x<-.5||r.y<-.5||r.x+r.w>1280.5||r.y+r.h>720.5),overlaps=[];
 for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){const a=texts[i],b=texts[j],ix=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x),iy=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);if(ix>5&&iy>5&&ix*iy>Math.min(a.w*a.h,b.w*b.h)*.16)overlaps.push([a,b]);}
 return {outside,overlaps};}'''


def browser_export(profile):
    from playwright.sync_api import sync_playwright
    chrome_candidates=[os.getenv('CHROME_PATH',''),r'C:\Program Files\Google\Chrome\Application\chrome.exe',r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',shutil.which('google-chrome') or '',shutil.which('chromium') or '']
    executable=next((str(Path(p)) for p in chrome_candidates if p and Path(p).is_file()),None)
    previews=ROOT/'slides/previews';previews.mkdir(exist_ok=True)
    report={'at_utc':utc_now(),'design':'aureo-v2','main_pages':10,'appendix_pages':3,'slides':[],'errors':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=executable,headless=True)
        context=browser.new_context(viewport={'width':1440,'height':910},device_scale_factor=1,offline=True,reduced_motion='reduce')
        page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)))
        page.goto((ROOT/'slides/entrega.html').as_uri());page.evaluate('document.fonts.ready')
        assert page.locator('.slide-shell').count()==13
        for i in range(13):
            if i:page.locator('[data-next]').click()
            report['slides'].append({'page':i+1,**page.evaluate(INK_BOUNDS)})
            page.locator('.slide-shell.is-active').screenshot(path=str(previews/f'entrega-{i+1:02d}.png'))
        page.keyboard.press('Home');assert page.locator('[data-prev]').is_disabled()
        page.keyboard.press('ArrowRight');assert page.locator('[data-counter]').inner_text().startswith('02')
        page.locator('[data-overview]').click();assert page.locator('body').evaluate("b=>b.classList.contains('is-overview')")
        page.locator('.slide-shell').nth(5).click();assert page.locator('[data-counter]').inner_text().startswith('06')
        page.locator('[data-fullscreen]').click();page.wait_for_function('Boolean(document.fullscreenElement)')
        page.keyboard.press('f');page.wait_for_function('!document.fullscreenElement')
        page.pdf(path=str(ROOT/'slides/entrega.pdf'),print_background=True,prefer_css_page_size=True)
        report['responsive']=[]
        for width,height in [(1920,1080),(1024,768),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(80)
            overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
            report['responsive'].append({'width':width,'height':height,'horizontal_overflow':overflow})
        browser.close()
    import pymupdf
    pdf=ROOT/'slides/entrega.pdf'
    with pymupdf.open(pdf) as doc:
        assert len(doc)==13
        doc.set_metadata({'title':'O preço da promessa — fidelidade, previsão e custos no PAXG','author':profile['team_name']+' — '+', '.join(profile['members']),'subject':'Pesquisa empírica, extensão retrospectiva e Áureo v2','creator':'BitFlow / pipeline de pesquisa'})
        doc.saveIncr()
    report['status']='passed' if not report['errors'] and not any(s['outside'] or s['overlaps'] for s in report['slides']) and not any(s['horizontal_overflow'] for s in report['responsive']) else 'needs_review'
    report['scope']='Glyph bounds, controls, PDF page count and viewport overflow. SVG charts and overall composition also reviewed visually.'
    dump_json(ROOT/'results/QA_presentation.json',report)
    if report['status']!='passed':raise ValueError('Apresentação precisa de revisão: results/QA_presentation.json')
    return report


def build_final(config):
    b=Book(config);slides=build_slides(b)
    (ROOT/'slides/entrega.html').write_text(viewer(slides),encoding='utf-8')
    dump_json(ROOT/'results/figure_manifest.json',b.figures)
    save=pd.DataFrame(b.usage);save.to_csv(ROOT/'results/PDF_claim_usage.csv',index=False,encoding='utf-8-sig')
    profile=json.loads((ROOT/'config/presentation.json').read_text(encoding='utf-8'))
    browser_export(profile)
    dump_json(ROOT/'results/presentation_status.json',{'pages':13,'main_pages':10,'appendix_pages':3,'design':'aureo-v2','pdf':'slides/entrega.pdf','html':'slides/entrega.html','generated_at_utc':utc_now(),'team_identity_provided':True,'claim_usages':len(b.usage)})
    print('Apresentação científica Áureo v2: 10 slides principais + 3 anexos, HTML e PDF.',flush=True)
