# PAXG × ouro: desvio, custos e rotação (2020–2026)

Pesquisa da equipe BitFlow (Gabriel Navarro, Lorenzo Cavalcante e Rodrigo Menin) para o 7º Datathon de Moedas Digitais da FGV EESP. Mede quanto o PAXG se afasta do ouro, por que o desvio persiste, quem consegue capturá-lo e o que isso muda para quem escolhe entre o token e os ETFs GLD/GLDM.

## Entrega (v5)

| Arquivo | Conteúdo |
| --- | --- |
| [slides/entrega.pdf](slides/entrega.pdf) | Apresentação final, 10 slides: capa e 9 slides de conteúdo (o material de abertura de 2026 pede até 10) |
| [slides/entrega_suplementar.pdf](slides/entrega_suplementar.pdf) | Material suplementar, 5 páginas: grades, tabelas completas, fontes e referências |
| [entrega/preco_da_promessa.zip](entrega/preco_da_promessa.zip) | Código, scripts em TXT, parâmetros, tabelas agregadas e testes |

**Tese.** O PAXG acompanha o ouro dia a dia (segue 94,6% do retorno diário e corrige 15% do desvio por dia), mas o desvio tem dois ritmos: um ruído que some em cerca de 4 pregões e um nível que dura meses (de −79 a +94 bps no período). A arbitragem de horas, com venda a descoberto, não paga (−22,0 bps por operação no cenário intermediário; 0 de 1.458 combinações positivas). Um investidor que já quer ouro captura o desvio trocando GLDM por PAXG no desconto e voltando no prêmio: +130 bps por ano contra o GLDM (IC 90% de 52 a 212; 0 de 1.000 placebos chegaram lá). Para quem só carrega, a variação do desvio em 12 meses (DP de 81 bps) supera a economia de taxa.

**Ordem das análises.** O núcleo (fidelidade, convergência, custos contra ETFs) usa parâmetros congelados antes dos resultados. A decomposição em dois componentes, a correção de erro, o fim de semana, o risco de base, a rotação e o cenário de custos intermediário (taxa do token 5 bps, spread 2 bps; escolhido na grade original a pedido da equipe) vieram depois e estão rotulados assim no relatório. O cenário original (−40,0 bps; 9,3 e 37,2 meses) continua citado.

**Código da v5.** [src/regime.py](src/regime.py) (regime e checagens na Kraken), [src/rotation.py](src/rotation.py) (rotação, placebo, fim de semana, risco de base, componentes e correção de erro), [src/report_v5.py](src/report_v5.py), [src/report_v5_pages.py](src/report_v5_pages.py) e [src/report_v5_build.py](src/report_v5_build.py) (relatório). Testes da rotação sem dado futuro em [tests/test_rotation.py](tests/test_rotation.py). Plano e validação em [PLANO_V5.md](PLANO_V5.md). Versões anteriores dos slides em [historico/](historico/).

```powershell
python run_all.py --v5          # só a extensão v5 e o relatório (usa os painéis locais)
python -m src.regime --kraken   # repete as checagens na Kraken (rede)
python run_all.py --package     # testes, integridade e pacote
```

## Revisão v3: tese e modelagem


A tese final distingue **ajuste de preço, previsibilidade e captura econômica**. O desvio observado cai após a reabertura, mas não desaparece imediatamente; modelos lineares não demonstraram ganho sobre persistência e os custos modelados superaram o bruto nas condições testadas.

| Extensão | Resultado desta execução |
| --- | --- |
| Contraste nos mesmos 301 fins de semana | Mudança média de −11,0 bps após 1h, IC exploratório [−15,2; −7,2]; −15,3 após 7h, IC [−20,2; −10,7]. |
| Previsão temporal, 204 casos | MAE 16,46 bps na persistência; 17,72 no ajuste linear; 18,21 no linear com contexto. Os modelos não demonstraram melhora. |
| Cobertura cambial, 6h | Janelas de busca de 1 e 5 minutos: 44 e 66 operações avaliadas; saldos de −40,01 e −39,76 bps, antes de financiamento desconhecido. |
| Ausências | Os 16 sinais originais não avaliados precisariam de +110,03 bps médios para zerar os 60 sinais observados elegíveis. Não é imputação. |
| Grade econômica original | 0 médias positivas em 1.458 combinações; melhor média de −2,88 bps, escolhida retrospectivamente. |

Os contrastes são médias de mudanças dentro de cada semana, não diferenças entre medianas. A modelagem usa treino expansivo com 104 semanas iniciais, somente alvos já concluídos e cinco referências/modelos avaliados na mesma amostra. O contexto inclui salto do ouro e volatilidade anterior, sem busca de hiperparâmetros. Os intervalos usam blocos de semanas do calendário.

**A extensão é retrospectiva, posterior aos resultados originais.** A separação temporal impede o uso do alvo futuro no ajuste de cada previsão, mas não constitui holdout prospectivo inédito. A janela cambial de cinco minutos permite carregar apenas FX já concluído por até quatro minutos; token e ouro permanecem no minuto exato e ativo. Ela não substitui o primário nem desbloqueia a simulação anual.

O desenho completo e as fontes primárias pesquisadas estão em [MODELAGEM_REVISAO.md](auditoria/MODELAGEM_REVISAO.md). Veja [REFINAMENTO.md](results/REFINAMENTO.md), [QA_refinement.json](results/QA_refinement.json) e [QA_presentation.json](results/QA_presentation.json). A configuração da extensão está em [config/refinement.json](config/refinement.json), com [snapshot próprio](results/refinement_config_frozen.json). O núcleo original e seus parâmetros continuam preservados; a execução anterior foi copiada para [historico/execucao_v2/](historico/execucao_v2/).

A comparação de custos com ETFs continua condicional. Com armazenamento hipotético do token de 10 bps/ano, desaparece o cruzamento favorável contra GLDM. A tendência em 24 trimestres continua inconclusiva; o ramo anual principal mantém a regra estrita, com 55 trajetórias para um mínimo de 78 e sensibilidade determinística.

## Núcleo e resultados preservados

- [Apresentação final, 10 slides + 4 anexos em PDF](slides/entrega.pdf).
- [Pacote para entrega e reprodução](entrega/preco_da_promessa.zip), com código, scripts TXT, parâmetros, testes, tabelas agregadas e figuras.
- [Interpretação dos resultados](results/INTERPRETACAO.md) e [registro numérico rastreável](results/RESULTS.md).
- [Tabelas e figuras](results/); [claims.csv](results/claims.csv) liga cada headline à sua origem.
- [Integridade do pipeline](results/QA_integrity.json), [testes executados](results/pytest.xml) e [manifesto de figuras](results/figure_manifest.json).

As análises foram executadas com dados reais na janela semiaberta **28/08/2020 12:00 UTC a 08/11/2026 00:00 UTC**. O primário tem **36.572 horas e 301 fins de semana válidos**, após exclusões explícitas dos 323 candidatos. Esses números são desta execução, rastreáveis nos resultados.

A mediana absoluta foi aproximadamente **36,4 bps log em horários comuns** e **48,4 bps log na reabertura**. A simulação principal avaliou **44 operações** e encontrou saldo médio de aproximadamente **−40,0 bps após os custos modelados, antes de custos financeiros desconhecidos**. Outros sinais sem preço completo continuam identificados no ledger; não foram declarados oportunidades inexistentes.

O equilíbrio de custo-base é **9,3 meses contra GLD e 37,2 contra GLDM**, condicionado a custos do token supostos, taxas/spread corrente dos ETFs, contas já em USD e comparação antes de impostos. Não é recomendação de investimento nem resultado universal entre produtos.

O critério de 78 trajetórias conjuntas para cenários anuais não foi atingido: houve 55. A saída aplicada é a sensibilidade determinística prevista no plano. O ramo de reamostragem conjunta está implementado e testado, mas não foi apresentado como resultado de mercado com amostra insuficiente. Não houve identificação causal de competição ou infraestrutura, e o intervalo da tendência inclui zero.

## Reproduzir

Requisitos: Python 3.11, Node >=20 e Chrome/Chromium para o PDF. O pipeline usa Chrome/Edge padrão no Windows, CHROME_PATH ou Chromium do Playwright. Se faltar navegador, execute `python -m playwright install chromium`. No Windows, a coleta usa `npx.cmd`; não exige alterar a política de execução do PowerShell. As fontes principais não exigem chave paga. Manter acesso de rede e espaço para os caches.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_all.py --all
```

Com as dependências já instaladas, `python run_all.py --all` executa coleta, construção dos painéis, minutos, análises originais, extensão v3, gráficos, HTML/PDF, testes e empacotamento. Na primeira coleta, `npx` obtém a versão fixada do downloader. Fontes podem impor limites, falhar ou revisar dados; os brutos locais e hashes permitem preservar a execução.

Depois da primeira execução completa, a repetição abaixo usa somente os caches locais e falha se um arquivo necessário estiver ausente ou tiver hash alterado:

```powershell
python run_all.py --all --offline
```

Etapas individuais:

```powershell
python run_all.py --fetch --build
python run_all.py --minutes
python run_all.py --analyze --figures
python run_all.py --refine
python run_all.py --package
python -m pytest -q
```

`--package` também executa os testes e a validação de integridade. O pacote público não contém os brutos: extraí-lo em outra máquina exige uma primeira coleta online. O relatório de downloads com URLs, datas e hashes é [download_manifest.jsonl](results/download_manifest.jsonl).

## Premissas e identificação da equipe

[config/params.json](config/params.json) contém as escolhas analíticas. O instante e o hash do congelamento estão em [config_frozen.json](results/config_frozen.json); alterações posteriores de premissas são recusadas pelo runner. Para outra rodada, preserve esta execução e versione uma cópia separada, em vez de sobrescrever silenciosamente seus resultados.

Nome da equipe e integrantes podem ser informados em [config/presentation.json](config/presentation.json), sem alterar os parâmetros da análise. Depois, execute `python run_all.py --figures --package`. Não foram inventados nomes ou vínculos para a capa.

## Organização

```text
run_all.py               orquestração das etapas
src/common.py            configuração, hashes e unidades
src/fetch.py             aquisições e cache
src/panel.py             calendário e painéis sem preenchimento indevido
src/trades.py            sinais, preços de minuto e trajetórias
src/statistics.py        P&L, cruzamentos e bootstrap semanal
src/analysis.py          núcleo original: tabelas, cenários, claims
src/refinement.py        pares, previsão temporal, cobertura e custos
src/presentation.py      apresentação científica HTML/PDF Áureo v2
src/quality.py           referência independente e integridade
src/report.py            figuras, PDF e pacote
tests/                   testes sem rede, com casos sintéticos declarados
config/                  premissas, fontes e apresentação
data/raw/                brutos locais, não distribuídos
data/interim/, panel/    dados processados locais, não distribuídos
results/                 saídas, logs, auditorias e figuras
slides/entrega.pdf       apresentação
scripts_txt/             cópias dos scripts no formato solicitado
entrega/                 ZIP e manifesto de arquivos
```

## Ajustes necessários incorporados

1. Ouro sempre com volume/atividade preservados; barras sintéticas não identificam horário negociável. Bid/ask são unidos por timestamp.
2. Bitfinex USDT/USD fornece a referência monetária primária desde 2020; a sobreposição sistemática com Coinbase é publicada como robustez. Não se supõe USDC=USD.
3. Sinal de convergência usa closes de minuto concluídos; entrada só no minuto seguinte. Trajetória horária é comparada na mesma amostra nos três instantes.
4. Perdas, preços faltantes e custos desconhecidos permanecem explícitos; a amostra insuficiente aciona a redução prevista, sem baixar limiares depois dos resultados.

## Limites e dados

Preços OHLC não garantem execução simultânea, liquidez ou acesso a short. Spread do token, taxas e slippage são cenários. Custos de empréstimo e financiamento não observados não viram zero. A inferência é exploratória; blocos semanais não resolvem dados ausentes ou custos omitidos. As conclusões não representam todo ouro tokenizado ou o custo final de um investidor brasileiro.

O ZIP exclui dados brutos, painéis de preço e ledgers detalhados com cotações de provedores, incluindo o ledger da sensibilidade cambial. Há instruções de aquisição e estatísticas próprias. Leia os termos de cada fonte antes de redistribuir dados. A validação de ouro contra GLD é um diagnóstico de compatibilidade de referência, não uma prova de equivalência de instrumentos.

## Documentação

- [Plano da equipe](<projeto_humanos (1).md>) e [especificação técnica](<projeto_agentes (1).md>).
- [Auditoria crítica](AUDITORIA.md), [fontes verificadas](auditoria/fontes_verificadas.md) e [viabilidade dos dados](auditoria/VIABILIDADE_DADOS.md).
- [Versões originais recebidas](historico/) e [regulamento consultado](auditoria/fontes/regulamento_fgv_2026.pdf).

A entrega foi preparada localmente. Nenhuma operação financeira, comunicação com a organização ou submissão externa foi feita automaticamente.
