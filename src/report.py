"""Figuras com dados reais, PDF 16:9 e pacote sem dados brutos restritos."""
from __future__ import annotations

import importlib.metadata
import json
import shutil
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .common import ROOT,dump_json,sha256,sources,utc_now

PAPER='#FAF9F5'; BLUE='#28649A'; GOLD='#B68A32'; RED='#B65343'; INK='#183044'; GRAY='#66757D'


def read(name):
    return pd.read_csv(ROOT/'results'/name)


def fmt(value,kind='number'):
    if value is None or (isinstance(value,(float,np.floating)) and not np.isfinite(value)):
        return 'indisponível'
    if kind=='count': return f'{int(value):,}'.replace(',','.')
    if kind=='percent': return f'{float(value)*100:.1f}%'.replace('.',',')
    if isinstance(value,(float,np.floating,int,np.integer)): return f'{float(value):.1f}'.replace('.',',')
    return str(value)


def setup_plot():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'axes.titlesize':15,
                         'axes.labelsize':13,'xtick.labelsize':11,'ytick.labelsize':11,
                         'figure.facecolor':PAPER,'axes.facecolor':PAPER,'text.color':INK,
                         'axes.labelcolor':INK,'xtick.color':GRAY,'ytick.color':GRAY,
                         'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#B8C1C4',
                         'grid.color':'#DEE2E1','grid.alpha':.75,'axes.axisbelow':True,'legend.frameon':False})


def newfig(ncols=1):
    fig,axes=plt.subplots(1,ncols,figsize=(12.8,7.2),squeeze=False)
    fig.subplots_adjust(left=.09,right=.97,top=.80,bottom=.28,wspace=.30)
    return fig,axes[0]


def build_figures(config):
    setup_plot(); manifest={}
    def save(fig,name,source_files):
        path=ROOT/'results'/name
        fig.savefig(path,dpi=200,facecolor=PAPER)
        plt.close(fig)
        manifest[name]={'source_files':source_files,'sha256':sha256(path),'config_hash':json.loads((ROOT/'results/config_frozen.json').read_text())['config_hash']}
    cov=read('coverage.csv'); fig,(ax,)=newfig()
    for source,g in cov.groupby('source'):
        ax.plot(pd.to_datetime(g.month),g.coverage_active_fraction*100,label=source,lw=1.8)
    ax.set(ylabel='Horas ativas / horas previstas (%)',xlabel='Mês; calendário regular do ouro é limite superior')
    ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(axis='y');ax.legend(loc='lower right',fontsize=12);ax.set_ylim(0,105)
    save(fig,'F0_cobertura.png',['results/coverage.csv'])

    q=read('T4_evolucao.csv'); dates=pd.to_datetime(q.quarter_start)
    fig,(ax,)=newfig()
    ax.plot(dates,q.median_abs_bps,'o-',color=BLUE,label='Mediana absoluta',lw=2)
    ax.plot(dates,q.p95_abs_bps,'o-',color=GOLD,label='Percentil 95 absoluto',lw=2)
    partial=~q.complete_quarter.astype(bool)
    ax.scatter(dates[partial],q.p95_abs_bps[partial],s=100,facecolors=PAPER,edgecolors=GOLD,zorder=5,label='Trimestre parcial')
    ax.set(xlabel='Trimestre',ylabel='Desalinhamento absoluto (bps log)');ax.grid(axis='y');ax.legend()
    ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    save(fig,'F1_fidelidade.png',['results/T4_evolucao.csv'])

    paired=read('T2_hourly_paired.csv');fig,(ax,)=newfig()
    x=np.arange(len(paired));width=.33
    ax.bar(x-width/2,paired.median_abs_bps,width,color=BLUE,label='Mediana absoluta')
    ax.bar(x+width/2,paired.p95_abs_bps,width,color=GOLD,label='Percentil 95 absoluto')
    for k,metric in [(-width/2,'median_abs_bps'),(width/2,'p95_abs_bps')]:
        if metric+'_lo' in paired:
            ax.vlines(x+k,paired[metric+'_lo'],paired[metric+'_hi'],color=INK,lw=1.6)
    ax.set_xticks(x,['Reabertura','Uma hora depois','Sete horas depois']);ax.set_ylabel('Desalinhamento absoluto (bps log)')
    ax.grid(axis='y');ax.legend();ax.set_title(f'Mesmos {int(paired.iloc[0]["n"])} fins de semana nos três instantes',loc='left')
    save(fig,'F2_reabertura.png',['results/T2_hourly_paired.csv'])

    trades=read('T2_convergencia.csv');b=config['convergence']['baseline']
    select=trades[trades.horizon_hours.eq(config['convergence']['exit_after_entry_hours']) & trades.token_full_spread_bps.eq(b['token_full_spread_bps']) & trades.gold_commission_bps_per_fill.eq(b['gold_commission_bps_per_fill']) & trades.conversion_roundtrip_bps.eq(b['conversion_roundtrip_bps']) & trades.slippage_bps_per_fill.eq(b['slippage_bps_per_fill'])]
    fig,(ax,)=newfig(); fees=config['convergence']['token_fee_bps_per_fill_grid']; x=np.arange(len(fees))
    for i,carry in enumerate(config['convergence']['residual_carry_roundtrip_bps_grid']):
        g=select[select.assumed_residual_carry_bps.eq(carry)].set_index('token_fee_bps_per_fill').reindex(fees)
        ax.bar(x+(i-1)*.24,g.mean_model_bps,width=.23,color=[BLUE,GOLD,RED][i],label=f'Custo residual suposto: {carry} bps')
    ax.axhline(0,color=INK,lw=1);ax.set_xticks(x,[str(f) for f in fees])
    ax.set(xlabel='Taxa do token por execução (bps; cenários)',ylabel='Saldo médio por operação (bps por perna de ouro)')
    ax.grid(axis='y');ax.legend(fontsize=12)
    save(fig,'F3_convergencia_custos.png',['results/T2_convergencia.csv','config/params.json'])

    cost=read('T3_baseline.csv');fig,axes=newfig(2)
    for ax,etf in zip(axes,['GLD','GLDM']):
        g=cost[cost.etf.eq(etf)]
        ref=g[g.token_storage_bps_year.eq(0)]
        ax.plot(ref.horizon_months,ref.etf_cost_bps,'o-',color=GOLD,label=etf,lw=2)
        for storage,style in [(0,'-'),(20,'--')]:
            z=g[g.token_storage_bps_year.eq(storage)]
            ax.plot(z.horizon_months,z.token_cost_bps,style,color=BLUE,label='PAXG: custos-base supostos' if storage==0 else 'PAXG + armazenamento suposto',lw=2)
        ax.set(title=f'PAXG × {etf}',xlabel='Horizonte (meses)',ylabel='Custo acumulado (bps)');ax.grid(axis='y');ax.legend(fontsize=10)
    save(fig,'F4_token_gld_gldm.png',['results/T3_baseline.csv'])

    sim=read('T5_sensibilidade.csv');fig,axes=newfig(2)
    labels=['Referência','Menor atrito','Estresse']
    for ax,col,label in [(axes[0],'p95_abs_bps','P95 absoluto na reabertura (bps log)'),(axes[1],'mean_trade_model_before_unknown_carry_bps','Saldo por operação (bps)\nantes de custos financeiros desconhecidos')]:
        ax.bar(np.arange(3),sim[col],color=[BLUE,GOLD,RED],width=.6)
        ci='p95_abs_bps' if col=='p95_abs_bps' else 'mean_trade_model_bps'
        if ci+'_lo' in sim:ax.vlines(np.arange(3),sim[ci+'_lo'],sim[ci+'_hi'],color=INK,lw=1.5)
        ax.set_xticks(np.arange(3),labels,rotation=12);ax.set_ylabel(label,fontsize=12);ax.grid(axis='y');ax.axhline(0,color=INK,lw=.7)
    save(fig,'F5_sensibilidade.png',['results/T5_sensibilidade.csv','config/params.json'])

    worst=read('T1_worst_weekends.csv');risk=read('T_riscos.csv');fig,axes=newfig(2)
    measured=risk[risk.metric.eq('reopen_p95_abs_log_bps')]
    axes[0].bar(['Saltos grandes','Demais saltos'],measured.value,color=[RED,BLUE])
    axes[0].set_ylabel('P95 absoluto na reabertura (bps log)');axes[0].grid(axis='y')
    for i,r in enumerate(measured.itertuples()):axes[0].annotate(f'N={int(r.n)}',(i,r.value),xytext=(0,8),textcoords='offset points',ha='center',fontsize=11)
    axes[1].barh(worst.id.astype(str).iloc[::-1],worst.abs_basis.iloc[::-1],color=GOLD)
    axes[1].set_xlabel('Cinco maiores desalinhamentos absolutos (bps log)');axes[1].grid(axis='x')
    save(fig,'F6_riscos.png',['results/T_riscos.csv','results/T1_worst_weekends.csv'])
    dump_json(ROOT/'results/figure_manifest.json',manifest)
    return manifest


class Presentation:
    def __init__(self,config):
        for name,file in [('Body','arial.ttf'),('Strong','arialbd.ttf')]:
            path=Path('C:/Windows/Fonts')/file
            if path.exists():pdfmetrics.registerFont(TTFont(name,str(path)))
        self.body='Body' if 'Body' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
        self.bold='Strong' if 'Strong' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
        self.config=config;self.claims=json.loads((ROOT/'results/summary.json').read_text(encoding='utf-8'))
        self.canvas=canvas.Canvas(str(ROOT/'slides/entrega.pdf'),pagesize=(960,540))
        self.canvas.setTitle('O preço da promessa — PAXG, custos e acesso 24/7')
        identity=json.loads((ROOT/'config/presentation.json').read_text(encoding='utf-8'))
        self.canvas.setAuthor((identity.get('team_name') or 'Projeto de pesquisa')+' — '+', '.join(identity.get('members',[])))
        self.page=0;self.usage=[]

    def value(self,key,kind='number'):
        self.usage.append({'page':self.page,'claim_id':key,'source':'results/claims.csv'})
        return fmt(self.claims.get(key),kind)

    def text(self,text,x,y,width=880,size=16,color=INK,bold=False):
        text=text.replace('P&L','P&amp;L')
        style=ParagraphStyle('slide',fontName=self.bold if bold else self.body,fontSize=size,leading=size*1.3,textColor=HexColor(color))
        para=Paragraph(text,style)
        _,height=para.wrap(width,1000)
        if height>y-15:raise ValueError(f'Texto excede a página {self.page}: {text[:80]}')
        para.drawOn(self.canvas,x,y-height)
        return y-height

    def start(self,title,image=None):
        self.page+=1;c=self.canvas
        c.setFillColor(HexColor(PAPER));c.rect(0,0,960,540,fill=1,stroke=0)
        if image:c.drawImage(str(ROOT/'results'/image),0,0,width=960,height=540)
        self.text(title,36,514,width=890,size=25,bold=True)
        c.setFillColor(HexColor(GOLD));c.rect(36,466,56,3,fill=1,stroke=0)

    def footer(self,source,caption=''):
        if caption:self.text(caption,36,93,width=885,size=13)
        self.text(source,36,27,width=860,size=9,color=GRAY)
        self.canvas.setFillColor(HexColor(GRAY));self.canvas.setFont(self.body,10);self.canvas.drawRightString(925,18,str(self.page))
        self.canvas.showPage()

    def finish(self):
        self.canvas.save()
        pd.DataFrame(self.usage).to_csv(ROOT/'results/PDF_claim_usage.csv',index=False,encoding='utf-8-sig')


def build_legacy_report(config):
    build_figures(config)
    p=Presentation(config);profile=json.loads((ROOT/'config/presentation.json').read_text(encoding='utf-8'))
    p.start('O preço da promessa')
    p.text('Fidelidade, custos e acesso 24/7 no PAXG',36,437,size=28,color=BLUE,bold=True)
    p.text('Quanto o token acompanha o ouro — e quais custos e condições limitam a captura de uma diferença de preços?',36,365,width=850,size=22)
    cards=[(p.value('valid_hours','count'),'horas válidas em USD'),(p.value('valid_weekends','count'),'fins de semana válidos'),(p.value('reopen_p95_abs_bps'),'bps log: P95 na reabertura')]
    for i,(number,label) in enumerate(cards):
        x=36+i*300
        p.text(number,x,240,width=285,size=36,color=BLUE,bold=True)
        p.text(label,x,184,width=280,size=15)
    team=profile.get('team_name')
    if team:p.text(escape(team)+'<br/>'+escape(' • '.join(profile.get('members',[]))),36,135,width=880,size=13)
    p.footer('Pesquisa aplicada • FGV EESP • Fontes e código no pacote de reprodução.', 'Preços observados; execução e custos do token sob hipóteses explícitas. Sem conclusão causal sobre infraestrutura ou competição.')

    p.start('Dados rastreáveis, moeda observada e calendário explícito','F0_cobertura.png')
    p.footer('Fontes: Binance; Bitfinex/Coinbase; Dukascopy. coverage.csv; panel_status.json; QA_currency_robustness.csv.',
             f"{p.value('valid_weekends','count')} de {p.value('candidate_weekends','count')} fins de semana passaram o filtro principal. Diferença mediana entre fontes de câmbio: {p.value('fx_source_median_abs_difference_bps')} bps; sensibilidade publicada.")

    p.start('Fidelidade em horários comuns: nível e evolução observados','F1_fidelidade.png')
    p.footer('Fontes: preços Binance × Bitfinex USDT/USD × Dukascopy. T1_fidelidade.csv; T4_evolucao.csv.',
             f"Mediana absoluta: {p.value('common_hours_median_abs_bps')} bps log; P95: {p.value('common_hours_p95_abs_bps')} bps log. Barras horárias são proxies; trimestres parciais não entram na regressão principal.")

    p.start('A trajetória após reabrir é comparada na mesma amostra','F2_reabertura.png')
    p.footer('Fonte: T2_hourly_paired.csv. Intervalos exploratórios por blocos semanais; amostra pareada nos três instantes.',
             'Desalinhamento contra uma referência não identifica preço verdadeiro. A queda do desvio absoluto também não equivale ao P&L de uma operação.')

    p.start('A cauda de preço e os limites de acesso precisam aparecer','F6_riscos.png')
    p.footer('Fontes: T_riscos.csv; T1_worst_weekends.csv. Regime: salto acima do p90 calculado com histórico anterior.',
             'O percentil de um estrato curto depende de poucos extremos. Custódia, resgate, contraparte e empréstimo são riscos documentais; não foram convertidos em bps de risco total.')

    p.start('Convergência: o resultado depende dos custos e do acesso','F3_convergencia_custos.png')
    p.footer('Fontes: T2_convergencia.csv; T2_baseline_inference.csv. Cenários de custo, não trades reais.',
             f"Base: {p.value('evaluated_trades','count')} operações avaliadas e {p.value('signals_unassessed','count')} sinais sem avaliação completa. Saldo médio: {p.value('mean_trade_model_bps')} bps antes de custos financeiros desconhecidos. Preços de minuto são aproximações.")

    p.start('O custo de manter ouro depende do ETF e da rota escolhida','F4_token_gld_gldm.png')
    p.footer('Fontes: T3_baseline.csv; config congelado; taxas e spread mediano corrente dos emissores GLD/GLDM.',
             f"Hipótese-base: token ida/volta {p.value('token_rt_bps')} bps. Equilíbrio de custos: GLD {p.value('GLD_crossing_months')} meses; GLDM {p.value('GLDM_crossing_months')} meses. USD, antes de impostos; custos do token supostos.")

    p.start('Cenários mostram sensibilidade, sem prever maturidade','F5_sensibilidade.png')
    method=p.claims.get('baseline_method','')
    status='Reamostragem conjunta pareada de semanas.' if 'blocks' in str(method) else 'Amostra conjunta insuficiente: sensibilidade determinística.'
    p.footer('Fonte: T5_sensibilidade.csv e T5_scenario_assumptions.csv. Não há extrapolação causal ou poça de lucro de mercado.',
             status+' Menor atrito mantém os preços e reduz custos. Estresse altera bases, custos e volume por hipóteses; financiamento segue desconhecido.')

    p.start('A decisão depende da necessidade, do prazo e do acesso')
    items=[('Acesso fora do horário','O token oferece negociação contínua; preço de execução e profundidade precisam ser verificados.'),
           ('Fidelidade ao ouro',f"Mediana absoluta de {p.value('common_hours_median_abs_bps')} bps log em horários comuns; isso não demonstra reserva de valor secular."),
           ('Custo de manutenção',f"O cruzamento depende do ETF: {p.value('GLD_crossing_months')} meses contra GLD e {p.value('GLDM_crossing_months')} contra GLDM na hipótese-base."),
           ('Captura de convergência','Exige duas pernas, inventário ou short, margem e financiamento. A simulação não demonstra arbitragem executável.')]
    y=431
    for title,body in items:
        p.text(title,36,y,width=225,size=17,color=BLUE,bold=True)
        p.text(body,278,y,width=640,size=17)
        y-=78
    p.footer('Fonte: T6_decisao.csv. Conclusões limitadas a PAXG, venues observados e hipóteses de custo.', 'Menor custo não implica menor risco; os produtos têm direitos, custódia e condições de acesso diferentes.')

    p.start('O que a evidência permite — e o que continua desconhecido')
    p.text('Observamos',36,433,width=420,size=20,color=BLUE,bold=True)
    p.text('Fidelidade e cauda contra uma referência; trajetória na reabertura; custos sob premissas declaradas; sensibilidade a preços e atritos.',36,392,width=420,size=18)
    p.text('Continuam limitados',510,433,width=410,size=20,color=RED,bold=True)
    p.text('Execução simultânea, livro histórico integral, acesso a empréstimo, financiamento e identidade de arbitradores. Tendência não identifica sua causa.',510,392,width=410,size=18)
    p.text('Reprodução',36,269,width=880,size=20,color=BLUE,bold=True)
    p.text('Código, parâmetros congelados, hashes, testes e tabelas acompanham a entrega. Os brutos permanecem locais; cada headline é rastreável em claims.csv e cada figura possui manifesto.',36,228,width=880,size=18)
    p.text('Fontes primárias',36,157,width=880,size=15,bold=True)
    links=[('Binance',sources()['binance_documentation']),('Bitfinex',sources()['bitfinex_documentation']),('Dukascopy',sources()['dukascopy_documentation']),('GLD',sources()['gld']),('GLDM',sources()['gldm'])]
    p.text(' • '.join(f'<link href="{escape(url)}">{label}</link>' for label,url in links),36,130,width=880,size=13)
    p.footer('Pesquisa e desenvolvimento assistidos por ferramentas de IA; decisões metodológicas e limitações documentadas.',
             f"Corte exclusivo: {escape(p.value('cutoff_utc','text'))}. Ver detalhes e resultados completos em RESULTS.md e no README.")
    p.finish()
    dump_json(ROOT/'results/presentation_status.json',{'pages':p.page,'pdf':'slides/entrega.pdf','generated_at_utc':utc_now(),'team_identity_provided':bool(profile.get('team_name')),'claim_usages':len(p.usage)})
    print('Figuras e apresentação PDF de 10 páginas geradas.',flush=True)


def build_report(config):
    """Figuras agregadas e relatório final v5 (o deck Áureo v2 antigo fica em src/presentation.py e historico/)."""
    build_figures(config)
    import shutil
    from .regime import run_regime
    from .rotation import run_all_v5
    from .report_v5_build import main as build_v5
    run_regime()
    run_all_v5()
    build_v5()
    shutil.copyfile(ROOT / 'slides/relatorio_final.pdf', ROOT / 'slides/entrega.pdf')
    shutil.copyfile(ROOT / 'slides/relatorio_final.html', ROOT / 'slides/entrega.html')
    shutil.copyfile(ROOT / 'slides/material_suplementar.pdf', ROOT / 'slides/entrega_suplementar.pdf')


def package_delivery(config):
    from .quality import validate_outputs
    validate_outputs(config)
    (ROOT/'entrega').mkdir(exist_ok=True)
    raw_manifest=ROOT/'data/raw/manifest.jsonl'
    public_records=[]
    for line in raw_manifest.read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        if 'command' in row:row['command']=[str(arg).replace(str(ROOT),'.') for arg in row['command']]
        public_records.append(json.dumps(row,ensure_ascii=False))
    (ROOT/'results/download_manifest.jsonl').write_text('\n'.join(public_records)+'\n',encoding='utf-8')
    code=[ROOT/'run_all.py',*sorted((ROOT/'src').glob('*.py')),*sorted((ROOT/'tests').glob('*.py'))]
    for path in code:
        target=ROOT/'scripts_txt'/str(path.relative_to(ROOT))
        target=target.with_name(target.name+'.txt');target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(path.read_text(encoding='utf-8'),encoding='utf-8')
    # Pacote público sem painéis de preços ou cotações brutas de provedores.
    files=[ROOT/'README.md',ROOT/'.gitignore',ROOT/'requirements.txt',ROOT/'pytest.ini',ROOT/'run_all.py',ROOT/'projeto_humanos (1).md',ROOT/'projeto_agentes (1).md',
           ROOT/'AUDITORIA.md',*list((ROOT/'auditoria').rglob('*.md')),*list((ROOT/'auditoria').glob('*.mjs')),
           *list((ROOT/'auditoria/fontes').glob('*.pdf')),*list((ROOT/'historico').glob('*.md')),
           *list((ROOT/'config').glob('*.json')),*code[1:],*list((ROOT/'scripts_txt').rglob('*.txt')),
           ROOT/'slides/entrega.pdf',ROOT/'slides/entrega.html',ROOT/'slides/entrega_suplementar.pdf',ROOT/'slides/relatorio_final.html',ROOT/'slides/material_suplementar.html',ROOT/'PLANO_V5.md',*list((ROOT/'slides/assets').glob('*.css')),
           ROOT/'slides/design-systems/AUREO.md',ROOT/'slides/design-systems/tokens.json',
           *list((ROOT/'slides/design-systems/assets').glob('*.css')),*list((ROOT/'slides/design-systems/assets').glob('*.js')),
           *list((ROOT/'slides/design-systems/assets').glob('*.svg')),*list((ROOT/'slides/design-systems/assets/fonts').glob('*')),
           *list((ROOT/'results/figures_refined').glob('*.svg')),*list((ROOT/'results').glob('*.png')),*list((ROOT/'results').glob('*.md')),
           *list((ROOT/'results').glob('*.json')),*list((ROOT/'results').glob('*.jsonl')),*list((ROOT/'results').glob('*.csv')),*list((ROOT/'results').glob('*.xml'))]
    omit={'T2_trade_ledger.csv','T9_fx_trade_ledger.csv','QA_three_weekends.csv','QA_fx_source_comparison.csv','QA_gold_reference.csv','run_status.json'}
    files=sorted(set(p for p in files if p.exists() and p.name not in omit))
    manifest=[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha256(p)} for p in files]
    dump_json(ROOT/'entrega/manifest.json',{'generated_at_utc':utc_now(),'data_policy':'no raw data, no price panels, no detailed quote ledgers','files':manifest})
    with zipfile.ZipFile(ROOT/'entrega/preco_da_promessa.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for path in files:z.write(path,str(path.relative_to(ROOT)))
        z.write(ROOT/'entrega/manifest.json','manifest.json')
    with zipfile.ZipFile(ROOT/'entrega/preco_da_promessa.zip') as z:
        if any(name.startswith(('data/','data\\')) or Path(name).name in omit for name in z.namelist()):
            raise ValueError('Pacote inclui dado bruto/painel/ledger que deveria permanecer local.')
        names=set(name.replace('\\','/') for name in z.namelist())
        required=set(pd.read_csv(ROOT/'results/claims.csv').source_file.str.replace('\\','/',regex=False))
        if not required.issubset(names):raise ValueError('Falta fonte agregada de headline no pacote público.')
    print(f'Pacote pronto: entrega/preco_da_promessa.zip ({len(files)} arquivos)',flush=True)
