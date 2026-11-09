# Plano de ajuste da apresentação (v4)

Data: 08/11/2026. Prazo de entrega: 23h59 (Brasília). Meta de envio: 22h.

## Diagnóstico da v3 (Áureo v2)

| Problema | Evidência | Efeito na banca |
| --- | --- | --- |
| Linguagem de slide "poético" | Títulos como "O token não fecha. A referência tem janelas.", "O custo fica com a diferença.", "Acesso contínuo. Vantagem condicional." Frases em pares/trios de fragmentos ("Preço observado. Custo sob hipóteses. Execução não comprovada.") | Soa gerado por IA e esconde a mensagem. |
| Jargão sem tradução | "bps log", "IC exploratório", "MAE", "persistência", "apuração", "trajetórias", "gate" | O jurado de economia/finanças não decodifica em 10 s. |
| Hedge em toda linha | "condicional", "exploratório", "não comprovado" em quase todo slide | A conclusão se perde; parece que o trabalho não afirma nada. |
| Texto minúsculo | Rodapés de 10 px com nomes de CSV (T7_paired_changes.csv) | Ilegível em PDF/tela; nomes de arquivo não ajudam o jurado. |
| Gráficos fracos | Slide 8 tem dois pontos soltos; cascata do slide 6 pinta "custos" de verde; o slide 3 de dados é só texto; falta o gráfico de evolução no tempo | Perde-se a melhor evidência visual. |
| Estrutura | Sem slide de motivação, sem resumo executivo, sem implicações por público; robustez cambial (44→66) ocupa slide principal | Regulamento recomenda motivação, delimitação, dados/método, resultados, discussão/implicações. |
| Achado central não explorado | Mediana mensal do desvio vai de −103 a +95 bps; 64% da variância horária é o nível mensal (80% o semanal) | A tese de "desvio que se ajusta" fica fraca; o dado mostra um prêmio/desconto que muda de regime. |
| Erro de renderização | "|desvio|" aparece como "Idesvioi" no slide 4 | Erro visível. |

## Achados novos (validados nos dados antes de entrar no deck)

1. Nível, não ruído: em 76 meses, a mediana mensal do desvio varia de −103 a +95 bps; o nível mensal explica 64% da variância das 36.572 horas, o semanal 80%. Em torno do nível semanal, a mediana absoluta é 11,6 bps.
2. A Kraken (PAXG/USD) mostra o mesmo sinal e tamanho em três janelas (−87, −107 e +84 bps contra o ouro). Logo não é artefato de USDT nem da Binance. Checagem pontual (140 horas), não série completa.
3. Melhora recente: 74% das horas de 2026 ficam a ≤25 bps do ouro (2020: 5%; 2023: 16%). Mediana absoluta de 14,8 bps em 2026.
4. Isso explica os resultados negativos: se o desvio é um nível que dura semanas (autocorrelação horária 0,98 em 2026), uma operação de 6 h não o captura. Tese reescrita sem causalidade.

## Decisões

- Mantemos todos os resultados originais e seus números. Os achados novos entram como análise descritiva posterior, marcada como tal (src/regime.py, tabelas T11).
- Nenhum parâmetro congelado é alterado. Nenhuma simulação nova de lucro (evita busca retrospectiva).
- Português direto: sujeito, verbo, número. Sem pares de fragmentos, sem metáforas, sem "não é X, é Y" repetido. Um termo técnico por vez, definido na primeira vez ("bps" = 0,01%).
- Títulos são a conclusão do slide, em frase completa.
- Corpo ≥ 20 px, notas ≥ 14 px (slide de 1280×720). Fonte dos dados em linguagem humana ("Binance, Bitfinex, Dukascopy"), nomes de arquivo só no anexo.
- Visual: fundo claro, uma cor de destaque (dourado), uma cor de contraste (azul-petróleo), vermelho só para perda. Um gráfico por slide, rotulado direto.

## Estrutura nova (10 + 4 anexos)

1. Capa: pergunta em linguagem simples.
2. Resposta em uma página: quatro achados com números.
3. Por que importa: ouro tokenizado, 24/7, volume negociado; o que o ouro de referência faz no fim de semana.
4. Dados e método: três fontes, 36.572 horas, 301 fins de semana, como medimos e como checamos.
5. Achado 1: o desvio é um nível que muda de regime (mediana mensal, 2020–2026).
6. Achado 2: ficou mais perto do ouro (fração de horas a ≤25 bps por ano; mediana trimestral).
7. Achado 3: reabertura e previsão (48→37→38 bps; queda pareada de 11 e 15 bps; modelos não superam persistência).
8. Achado 4: capturar o desvio custa mais do que paga (cascata; 44 operações; 0 de 1.458 combinações positivas).
9. Achado 5: PAXG versus GLD e GLDM (custo acumulado ao longo do tempo; cruzamentos 9,3 e 37,2 meses).
10. Conclusões, limites e próximos passos (por público: investidor, plataforma, pesquisa/Brasil).
A1 grade econômica · A2 modelos de previsão · A3 robustez cambial e dados ausentes · A4 fontes e reprodução.

## Validação do plano

| Critério | Como verificamos |
| --- | --- |
| Regulamento: motivação, delimitação, dados e método, resultados, discussão/implicações | Slides 3, 3/4, 4, 5–9, 10 |
| Critérios da banca: qualidade, relevância, criatividade | Qualidade: números rastreáveis e checagens independentes; relevância: slide 3 e 10; criatividade: leitura do desvio como regime e ligação com custo de resgate |
| Todo número do deck vem de arquivo em results/ | O gerador lê CSV/JSON; teste de PDF confere os números-chave |
| Texto sem artefato | Extração de texto do PDF, busca de "|", "?" e "nan"; inspeção visual das 14 páginas a 100 dpi |
| Prazo | Build ≤ 2 h; revisão visual 45 min; folga de 3 h |
| Risco: reinterpretar o desvio como "nível" é pós-hoc | Rotulado como análise descritiva posterior; checagem Kraken; sem teste de hipótese nova |
| Risco: afirmar causa (custo de resgate) | Escrito como "consistente com", citando as condições da Paxos; sem identificação causal |

## Execução

1. Rodar src/regime.py (feito). 2. Escrever src/deck_v4.py (HTML autônomo + SVG). 3. Gerar PDF com Chrome. 4. Testes de conteúdo e leitura visual. 5. Substituir slides/entrega.pdf e .html; guardar a v3 em historico/slides_v3. 6. Atualizar README e pacote.

## Atualização (mesmo dia)

- Cenário de custos: a equipe optou por apresentar um cenário intermediário (taxa 5 bps, spread 2 bps), escolhido na grade original depois dos resultados. Os números vêm de T2_convergencia.csv e T3_custos_etfs.csv; o original continua visível nos slides 8, 9 e A1.
- Visual: deck refeito no sistema Áureo (carvão, marfim, ouro, DM Serif Display, Manrope, IBM Plex Mono), mantendo a linguagem direta.
