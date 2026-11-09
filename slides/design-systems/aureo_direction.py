"""Áureo: the interval between the reference and the traded price."""
from __future__ import annotations


def interval_drawing() -> str:
    return '''<svg class="interval-drawing" viewBox="0 0 600 220" role="img" aria-label="Construção conceitual da marca: duas lâminas deslocadas e separadas por um intervalo.">
      <path class="solid-gold" d="M64 38h230l18 55H46z"/>
      <path class="outline-gold" d="M115 114h230l18 55H97z"/>
      <path class="annotation-line" d="M312 66h71m-20 76h20M30 94v20m-5-20h10m-10 20h10"/>
      <text class="drawing-label" x="403" y="72">lastro</text><text class="drawing-label" x="403" y="148">preço</text>
      <text class="drawing-note" x="45" y="207">O deslocamento é conceitual. Não é uma série de preços.</text>
    </svg>'''


def distribution_ruler(data, n) -> str:
    """Two distribution landmarks on a common zero-based scale; not a CI."""
    parts = ['<svg class="chart distribution-ruler" viewBox="0 0 1168 267" role="img" aria-label="Marcos do desvio absoluto em bps log. Horários comuns: mediana 36,4, percentil 95 de 120,1. Reabertura: mediana 48,4, percentil 95 de 164,2. A linha une os marcos, não representa intervalo de confiança.">']
    x = lambda value: 250 + value / 200 * 790
    for tick in [0,50,100,150,200]:
        px=x(tick)
        parts.append(f'<path class="ruler-grid" d="M{px} 35v165"/><text class="ruler-tick" x="{px}" y="225" text-anchor="middle">{tick}</text>')
    for row, prefix, label, sample in [(78,'common_hours','Horários comuns','36.572 horas'),(174,'reopen','Reabertura','301 fins de semana')]:
        median, p95=[data[f'{prefix}_{suffix}'] for suffix in ['median_abs_bps','p95_abs_bps']]
        parts.extend([
            f'<text class="ruler-label" x="0" y="{row-2}">{label}</text><text class="ruler-sample" x="0" y="{row+23}">{sample}</text>',
            f'<path class="ruler-link" d="M{x(0)} {row}H{x(p95)}"/>',
            f'<path class="ruler-end" d="M{x(p95)} {row-10}v20"/>',
            f'<circle class="ruler-median" cx="{x(median)}" cy="{row}" r="7"/>',
            f'<text class="ruler-value" x="{x(median)}" y="{row-23}" text-anchor="middle" data-claim="{prefix}_median_abs_bps" data-raw="{median}">{n(median)}</text>',
            f'<text class="ruler-value" x="{x(p95)+16}" y="{row+5}" data-claim="{prefix}_p95_abs_bps" data-raw="{p95}">{n(p95)}</text>',
        ])
    parts.append('<circle class="ruler-median" cx="666" cy="8" r="4"/><text class="ruler-legend" x="680" y="13">Mediana</text><path class="ruler-end" d="M821 2v12"/><text class="ruler-legend" x="835" y="13">Percentil 95</text><text class="ruler-tick" x="1128" y="225" text-anchor="end">bps log</text><text class="ruler-disclaimer" x="250" y="260">Dois marcos da distribuição; a linha não é um intervalo de confiança.</text></svg>')
    return ''.join(parts)


def horizon_ruler(data, n) -> str:
    parts=['<svg class="chart horizon-ruler" viewBox="0 0 690 430" role="img" aria-label="Marcos de equilíbrio de custo numa escala de zero a 48 meses: 9,3 meses contra GLD e 37,2 contra GLDM, sob a hipótese-base.">']
    x=lambda month: 42+month/48*585
    parts.append('<text class="horizon-caption" x="42" y="27">Marcos de equilíbrio na hipótese-base</text>')
    for key,top,label,fee in [('GLD_crossing_months',88,'GLD','40 bps ao ano'),('GLDM_crossing_months',184,'GLDM','10 bps ao ano')]:
        value=data[key]; px=x(value)
        parts.extend([
            f'<text class="horizon-name" x="{px-16}" y="{top}">{label} · {fee}</text>',
            f'<text class="horizon-number" x="{px-18}" y="{top+79}" data-claim="{key}" data-raw="{value}">{n(value)}</text>',
            f'<path class="horizon-leader" d="M{px} {top+95}V338"/>',
            f'<circle class="horizon-point" cx="{px}" cy="338" r="6"/>',
        ])
    parts.append('<path class="horizon-axis" d="M42 338H627"/>')
    for month in [0,12,24,36,48]:
        parts.append(f'<path class="horizon-axis" d="M{x(month)} 331v14"/><text class="horizon-tick" x="{x(month)}" y="375" text-anchor="middle">{month}</text>')
    parts.append('<text class="horizon-tick" x="627" y="411" text-anchor="end">Meses de manutenção →</text></svg>')
    return ''.join(parts)


def build_aureo(*, slide, symbol, v, n, data, team, waterfall) -> list[str]:
    t='aureo'; out=[]
    out.append(slide(t,1,'a-cover',f'''
      <div class="a-cover-imprint">{symbol(t,False)}<span>BitFlow</span></div>
      <p class="a-cover-event">FGV EESP<br>7º Datathon de Moedas Digitais</p>
      <h1 id="title-1" class="a-cover-title"><span>O preço</span><span class="a-cover-second"><small>da</small> <em>promessa.</em></span></h1>
      <div class="a-cover-mark">{symbol(t)}</div><div class="a-cover-registration" aria-hidden="true"><i></i><i></i></div>
      <p class="a-cover-description">Fidelidade, custos e acesso 24/7<br>no ouro tokenizado.</p>
      <p class="a-cover-question">O que separa o lastro<br>do preço negociado?</p>
      <span class="a-cover-date">PAXG / 2020—2026</span>
    ''',team))
    palette=[('background','Carvão','Base e profundidade',300),('paper','Marfim','Páginas de leitura',250),('gold','Ouro','Evidência e assinatura',205),('reference','Verde','Segunda medida',145),('negative','Terracota','Perda e fricção',100)]
    colors=data_colors()
    palette_rows=''.join(f'<div class="a-ink-row"><div class="a-ink-sample" style="width:{width}px;background:{colors[key]}"></div><div><b>{name}</b><span>{colors[key]}</span><small>{role}</small></div></div>' for key,name,role,width in palette)
    out.append(slide(t,2,'a-identity light',f'''
      <p class="a-section-note">Áureo / A marca</p><h1 id="title-2" class="slide-title">O intervalo<br>é a assinatura.</h1>
      <div class="a-brand-study">{interval_drawing()}</div>
      <p class="a-brand-description">Duas lâminas com o mesmo contorno.<br>Uma preenchida, outra aberta, ligeiramente deslocada.<br>O espaço entre elas torna o desvio parte da identidade.</p>
      <div class="a-ink-register"><p class="a-register-caption">Cinco tintas. Cada uma com uma função.</p>{palette_rows}</div>
    '''))
    out.append(slide(t,3,'a-type light','''
      <p class="a-section-note">Áureo / Notas de composição</p><h1 id="title-3" class="slide-title">O dado pede<br><em>espaço.</em></h1>
      <span class="a-type-caption">DM Serif Display · argumento e números de destaque</span>
      <p class="a-type-paragraph">O título entrega a leitura.<br>O texto dá o contexto.<br>A nota delimita o que foi medido.</p>
      <div class="a-type-settings"><div><b>01</b><h2>DM Serif Display</h2><p>60–78 px nos títulos.<br>Itálico com função, em trechos pontuais.</p></div><div><b>02</b><h2>Manrope</h2><p>20–24 px no corpo.<br>Texto que cabe no tempo de uma leitura.</p></div><div><b>03</b><h2>IBM Plex Mono</h2><p>13–15 px em medidas e notas.<br>Unidades e fontes sempre próximas do dado.</p></div></div>
      <div class="a-margin-mark" aria-hidden="true"><span>56</span><i></i></div>
      <div class="a-evidence-register"><span>Leitura da evidência</span><b class="a-observed">Observado</b><b class="a-assumed">Hipótese</b><b class="a-missing">Indisponível</b></div>
    '''))
    excluded=data['candidate_weekends']-data['valid_weekends']
    method_rows=[('01','Origem','Fontes públicas e arquivos com hash.'),('02','Moeda','Conversão com câmbio observado.'),('03','Relógio','Calendário e atividade do ouro.'),('04','Comparação','Desvio de preço, custos e restrições.')]
    register=''.join(f'<div class="a-assay-row"><span>{i}</span><h2>{title}</h2><p>{text}</p></div>' for i,title,text in method_rows)
    out.append(slide(t,4,'a-method',f'''
      <aside class="a-sample-sheet"><p>RECORTE / 2020—2026</p><h2>O que entra<br>na amostra<br>importa.</h2><div class="a-sample-arithmetic"><div><strong>{v('candidate_weekends',0)}</strong><span>fins de semana<br>candidatos</span></div><div class="a-sample-exclusions"><strong>−{excluded}</strong><span>exclusões<br>documentadas</span></div><div class="a-sample-total"><strong>{v('valid_weekends',0)}</strong><span>fins de semana<br>válidos</span></div></div></aside>
      <p class="a-section-note">Método / Registro de apuração</p><h1 id="title-4" class="slide-title">A comparação<br>começa no método.</h1><div class="a-assay-register">{register}</div>
      <div class="a-method-coverage"><strong>{v('valid_hours',0)}</strong><p>horas válidas em USD.<br>Câmbio ausente e ouro inativo ficam fora da comparação.</p></div>
    ''','Fontes: coverage.csv e exclusions.csv · calendário, câmbio e atividade preservados'))
    out.append(slide(t,5,'a-data light',f'''
      <p class="a-section-note">Fidelidade / Amostra completa</p><div class="a-data-lead"><strong>{v('reopen_median_abs_bps')}</strong><span>mediana · bps log</span></div>
      <h1 id="title-5" class="slide-title">Na reabertura,<br>o desvio é maior.</h1><p class="a-data-reading">Uma comparação descritiva de preços em USD.<br>A negociação contínua convive com desvios da referência.</p>
      <div class="a-distribution-figure">{distribution_ruler(data,n)}</div>
    ''','Fonte: T1_fidelidade.csv · 28/08/2020 a 08/11/2026 00:00 UTC, exclusivo · sem inferência causal'))
    out.append(slide(t,6,'a-pnl',f'''
      <p class="a-section-note">Convergência / Apuração condicional</p><h1 id="title-6" class="slide-title">O custo fica<br>com a diferença.</h1><div class="a-waterfall-figure">{waterfall()}</div>
      <aside class="a-settlement-sheet"><span class="a-settlement-code">HIPÓTESE-BASE / 6 HORAS</span><h2>Apuração<br>por operação</h2><div class="a-account-row"><span>Ganho bruto</span><b>{v('mean_gross_mid_bps',1,True)}</b></div><div class="a-account-row"><span>Custos modelados</span><b>−{v('mean_total_modeled_cost_bps')}</b></div><div class="a-account-total"><span>Saldo médio modelado</span><strong>{v('mean_trade_model_bps')}</strong><small>bps por perna de ouro</small></div><p class="a-account-sample">{v('evaluated_trades',0)} operações avaliadas.<br>{v('signals_unassessed',0)} sinais sem avaliação completa.</p><p class="a-account-unknown">Empréstimo e financiamento<br>continuam desconhecidos.</p></aside>
      <p class="a-pnl-assumptions">Token: 10 bps/execução + spread cheio 10; ouro: 1/execução;<br>FX: 2/ida e volta; slippage: 2/execução. Custos sob hipóteses explícitas.</p>
    ''','T2_baseline_inference.csv · execução simultânea e acesso a short não comprovados'))
    out.append(slide(t,7,'a-cost light',f'''
      <p class="a-section-note">Manutenção / Token e ETFs</p><h1 id="title-7" class="slide-title">Quando o prazo<br>muda a conta.</h1><p class="a-horizon-reading">O mesmo custo inicial do token.<br>Dois ritmos de cobrança anual.<br>Dois horizontes de equilíbrio.</p><p class="a-horizon-scope">Comparação em USD, antes de impostos,<br>com igual possibilidade de acesso.</p>
      <div class="a-horizon-figure">{horizon_ruler(data,n)}</div><div class="a-cost-premises"><span>Rota-base</span><p>Token: 32 bps de ida e volta e armazenamento zero suposto. ETF: 1 bp de ida e volta.<br>Sem retirada na rota-base. As mudanças de premissas alteram os horizontes.</p></div>
    ''','Fonte: T3_baseline.csv · taxas e spread corrente dos ETFs; custos do token supostos'))
    out.append(slide(t,8,'a-close',f'''
      <p class="a-section-note">O preço da promessa / Conclusão</p><h1 id="title-8" class="slide-title">Acesso contínuo.</h1><div class="a-closing-cut" aria-hidden="true"></div><p class="a-closing-answer"><em>Vantagem condicional.</em></p>
      <p class="a-closing-reading">O saldo depende de custos e condições de acesso.<br>A diferença de preço, sozinha, não comprova arbitragem.</p><div class="a-closing-limit"><span>55 / 78</span><p>Trajetórias abaixo do mínimo.<br>Cenários com sensibilidade<br>determinística, conforme o plano.</p></div>
    ''',team))
    return out


def data_colors() -> dict[str,str]:
    # Load the same local palette used by the generated identity register.
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parent/'tokens.json').read_text(encoding='utf-8'))['aureo']['colors']
