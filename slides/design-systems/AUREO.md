# Áureo — o intervalo como assinatura

Direção escolhida para O preço da promessa, da BitFlow. Revisão 2.0.

A identidade parte de uma situação concreta da pesquisa: lastro e preço negociado compartilham uma referência, mas podem se separar. Esse intervalo aparece na marca, no deslocamento da tipografia, nas réguas dos gráficos e no encontro entre páginas de apuração. A referência visual é um caderno de ensaio de ouro e um registro editorial de preços.

## Marca

Duas lâminas trapezoidais de mesmo contorno. A superior é preenchida; a inferior é aberta e deslocada lateralmente. Um pequeno traço de aferição marca a fenda. O desenho funciona como uma assinatura pequena, sem precisar ocupar o centro de todas as páginas. A construção é conceitual; não representa uma série de preços.

[SVG da marca](assets/aureo-symbol.svg)

## Paleta e tipografia

A paleta mantém o carvão `#171914`, o ouro `#CFAD68` e o marfim `#F3EEE3`. Verde `#A4B7A4` identifica a segunda medida; terracota `#E69B88`, a perda. Nos fundos claros, ouro e verde recebem versões mais escuras para leitura. O contraste de texto essencial é pelo menos 4,5:1 nos pares verificados.

DM Serif Display conduz os argumentos e os grandes números; Manrope explica; IBM Plex Mono identifica unidade, escala e fonte. O itálico destaca uma mudança de leitura em lugares escolhidos. Títulos de conteúdo usam 64–78 px; a capa e os espécimes tipográficos admitem escalas maiores. O corpo principal fica em torno de 19–25 px. Notas e rótulos secundários usam 11–15 px; a apresentação final deve ampliar notas que precisem ser lidas à distância.

## Composições

1. **Capa:** título em duas alturas, segunda linha deslocada, marca pequena fora do eixo e dois segmentos de aferição. A pergunta da pesquisa ocupa uma posição própria.
2. **Marca e tintas:** desenho de ensaio aberto, com linhas de chamada; registro de cores com funções escritas. Sem moldura em torno da marca.
3. **Tipografia:** página de prova com um argumento grande, notas laterais numeradas e marcação da margem. Estados da evidência aparecem por símbolo e texto.
4. **Método:** folha dourada de seleção da amostra à esquerda e registro de procedimentos à direita. A conta 323 − 22 = 301 comunica a exclusão diretamente.
5. **Fidelidade:** a estatística abre a página. Mediana e percentil 95 são colocados numa régua comum com zero e unidades explícitos. A linha entre marcos não é um intervalo de confiança.
6. **Convergência:** gráfico em carvão e folha de apuração em marfim. Bruto, custo, saldo e informações indisponíveis têm lugares distintos na leitura.
7. **Manutenção:** uma escala de calendário situa os dois horizontes de equilíbrio; as premissas ficam abaixo da figura. Alturas diferentes servem à composição, enquanto o eixo horizontal codifica os meses.
8. **Conclusão:** fundo ouro e faixa de carvão deslocada retomam as duas lâminas da marca. A tese ocupa a faixa; as condições de interpretação acompanham o encerramento.

## Regras de continuidade

O canvas permanece em 16:9, com 1280 × 720 px. A margem principal do Áureo passa a 64 px. A folha lateral e a faixa da conclusão podem alcançar a borda; texto essencial permanece dentro da área segura. Reutilizar a marca, as fontes, as tintas e os deslocamentos cria continuidade entre composições diferentes.

A composição deve partir do argumento de cada slide. Não repetir uma mesma distribuição de título, número e três colunas em toda a apresentação. Reservar o ouro pleno para momentos específicos de abertura da amostra ou de conclusão.

Os exemplos mantêm os resultados e limitações do estudo. A implementação está em `aureo_direction.py` e `assets/aureo.css`; `build.py` gera o HTML. A visualização atualizada está em [01-aureo.html](01-aureo.html), e a [prancha](previews/aureo-prancha.png) mostra as oito composições.
