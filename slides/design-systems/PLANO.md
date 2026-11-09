# Três sistemas visuais para O preço da promessa

## Objetivo

Dar à pesquisa da BitFlow uma identidade ligada ao seu processo: observar preços, normalizar a moeda, respeitar o calendário, medir desvios e testar o que resta após custos. Os protótipos são estudos de direção visual para slides, com fundamentos do sistema e exemplos aplicados aos resultados existentes. Não substituem automaticamente a apresentação original.

## Fundamentos compartilhados

- Tela de 1280 × 720, proporção 16:9, margem de segurança de 56 px (64 px no Áureo revisado) e escala de espaçamento de 8 px.
- Uma mensagem principal por lâmina. Título comunica a conclusão; subtítulo delimita a amostra ou a premissa.
- Tipos locais, sem depender de Google Fonts, CDN, rede ou instalação de fontes.
- Ouro identifica o objeto estudado ou a evidência principal. Cinza, verde ou azul identifica a referência ou a segunda medida. Terracota identifica perda; nunca é o único meio de comunicar o sinal.
- Observado, hipótese e indisponível possuem rótulos escritos e tratamentos distintos. Ausência de dados não vira zero. Limites e fontes permanecem visíveis.
- Eixos começam em zero nas comparações de magnitudes. Séries recebem rótulos diretos. Não há perspectivas 3D, gráficos decorativos ou números inventados.
- Cores com pouco contraste são reservadas a ornamentos. Texto essencial usa pares de pelo menos 4,5:1; texto grande, pelo menos 3:1. As verificações ficam em QA_design.json.
- Cada HTML permite avançar, voltar, abrir uma visão geral, entrar em tela cheia e imprimir em PDF. Setas, Home, End, G e F também funcionam; os controles têm foco visível e rótulos acessíveis.

## 01 — Áureo: o intervalo como assinatura

**Personalidade:** editorial e ligada ao processo de ensaio e apuração. Direção escolhida, refinada na revisão 2.0. O planejamento específico está em [AUREO.md](AUREO.md).

**Símbolo — marca de intervalo:** duas lâminas trapezoidais de mesmo contorno, uma preenchida e outra aberta, deslocadas entre si. A fenda remete à separação entre lastro e preço. Um pequeno traço de aferição completa a assinatura.

**Paleta:** carvão `#171914`, ouro `#CFAD68`, marfim `#F3EEE3`, grafite `#32382F`, verde `#A4B7A4` e terracota `#E69B88`. O ouro pleno fica reservado a momentos específicos; marfim e carvão conduzem a leitura.

**Tipografia:** DM Serif Display, Manrope e IBM Plex Mono. Títulos de conteúdo de 64–78 px; capa e prova tipográfica podem ampliar a escala. Corpo principal de 19–25 px. Margem própria de 64 px.

**Composição:** caderno de ensaio e registro de apuração. Capa com título deslocado, desenho técnico da marca, prova tipográfica, folha de seleção da amostra, régua de distribuição, apuração de custos, calendário e conclusão com faixa deslocada. Cada argumento determina a composição. As fontes, as tintas e o intervalo criam a continuidade.

## 02 — Vértice: mercado e medida

**Personalidade:** analítica, técnica e precisa. Melhor para método, comparações, custos e perguntas da banca sobre os números.

**Símbolo — referência comum:** duas trajetórias, uma dourada e uma azul, chegam a um vértice vazado. Representa colocar token e referência na mesma unidade antes de comparar. É uma marca conceitual, não a previsão de convergência dos preços.

**Paleta:** azul profundo `#0C1522`, painel `#152536`, ouro `#F0C66D`, azul mineral `#8CD1DD`, branco frio `#EDF2F5`, cinza `#ACBAC8` e coral `#F0A18E`.

**Tipografia:** Space Grotesk nos títulos, Manrope no corpo e IBM Plex Mono nos números. Display de 88–104 px, títulos de 50–62 px, corpo de 20–24 px e notas de 13–15 px.

**Composição:** grade explícita de 12 colunas, linhas ortogonais, cantos discretos, tabelas abertas e rótulos diretos. O fundo quadriculado tem contraste baixo e serve apenas como textura.

## 03 — Meridiano: tempo e acesso

**Personalidade:** conceitual, arquitetônica e contemplativa. Melhor para explicar o funcionamento 24/7, construir a narrativa e encerrar com os limites da evidência.

**Símbolo — janela de mercado:** uma órbita contínua e outra interrompida compartilham o centro. Elas representam a negociação contínua do token e as janelas da referência tradicional. A abertura do círculo representa uma janela de calendário, não uma lacuna preenchida com preço.

**Paleta:** verde noturno `#10231F`, verde superfície `#1A342D`, ouro antigo `#D4B06B`, calcário `#F1EDE2`, sálvia `#ABC0AF` e argila `#E7A28B`.

**Tipografia:** Instrument Serif nos títulos, Manrope no corpo e IBM Plex Mono em datas e medidas. Display de 110–128 px, títulos de 60–76 px, corpo de 22–26 px e notas de 13–15 px.

**Composição:** círculos incompletos, linhas de tempo, amplo espaço negativo e alternância de verde e calcário. Arcos do símbolo não codificam porcentagens; dados quantitativos usam escalas explícitas.

## Sequência dos oito slides de cada estudo

1. Capa e promessa visual do sistema.
2. Identidade: conceito do símbolo, paleta e papéis das cores.
3. Tipografia, hierarquia, grade, espaçamento e estados de evidência.
4. Processo de pesquisa: da coleta à comparação sob condições explícitas.
5. Fidelidade de preço: gráfico com resultados reais e fonte.
6. Convergência: resultado bruto, custos modelados, saldo e informações desconhecidas.
7. Custo de manutenção: horizontes condicionais contra GLD e GLDM.
8. Conclusão: tese, limites e identificação da equipe.

## Como as propostas se complementam

São três direções completas e independentes. Áureo favorece argumento e credibilidade; Vértice favorece leitura de dados; Meridiano favorece entendimento do tempo e do acesso. Se houver combinação futura, escolher um sistema principal e manter suas fontes, margens e semântica; aproveitar a composição de outro sem alternar a identidade a cada slide.

## Fontes e escopo dos exemplos

Os valores vêm de `results/summary.json`, `results/T1_fidelidade.csv`, `results/T2_hourly_paired.csv`, `results/T2_baseline_inference.csv` e `results/T3_baseline.csv`. Janela até 08/11/2026 00:00 UTC, exclusiva. Os custos do token são hipóteses; financiamento e empréstimo permanecem desconhecidos. As 44 operações avaliadas não incluem os 16 sinais sem avaliação completa. Os cenários usam a alternativa determinística porque há 55 trajetórias completas para um mínimo de 78.

`build.py` gera os três HTMLs a partir dessas saídas e dos tokens visuais. O código de análise e o PDF original permanecem separados deste estudo visual.
