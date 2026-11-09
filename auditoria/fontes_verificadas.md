# Fontes e verificações da revisão

Data de referência: 08/11/2026. As respostas de endpoints e as amostras abaixo são verificações pontuais; não comprovam cobertura histórica integral. Os conteúdos de páginas podem mudar depois desta consulta.

## Regulamento

- [Página oficial do evento](https://eesp.fgv.br/evento/7o-desafio-de-dados-datathon-de-moedas-digitais-da-fgv-eesp).
- [Regulamento oficial](https://eesp.fgv.br/sites/default/files/uploads/regulamento-do-desafio-de-dados-de-moedas-digitais-fgv-2026_0.pdf), baixado e lido com `pdftotext` nesta revisão. [Cópia local](fontes/regulamento_fgv_2026.pdf).
- SHA-256 da cópia: `446b97ccbd1a9634d8882d81fa5bb827377547b11e76bc927e436b4bc1161218`.
- Confirmados: entrega em 08/11/2026 às 23h59; PDF; scripts em TXT se houver; fontes externas citadas; avaliação de qualidade, relevância e criatividade; anexos permitidos. O horário de Brasília consta da página do evento.
- O PDF lido não fixa 10 slides, 5 minutos de defesa ou uso obrigatório de machine learning. Também não contém disposição específica sobre IA. Material complementar enviado às equipes pode trazer instruções adicionais; não foi disponibilizado nesta pasta.

## Paxos

- [Overview vigente do PAXG](https://support.paxos.com/articles/5590384005-pax-gold-paxg-overview): armazenamento sem taxa atualmente; criação isenta até 01/01/2027; resgate marginal por atividade líquida em 30 dias, em faixas de 0,125%, 0,25%, 0,35% e 0,5%; conversão em ouro alocado/não alocado com taxa de 5 bps. São condições vigentes, não uma tabela histórica para 2020–2026.
- O antigo endereço `https://support.paxos.com/articles/2899561282-PAX-Gold-Fees` retornou 404 nesta revisão. Uma versão anterior mencionava 30/09/2026 como término da isenção; a página consolidada mais recente estende a data. Não usar a versão antiga para afirmar que a criação atualmente é tarifada.
- [Termos do PAXG](https://www.paxos.com/terms-and-conditions/pax-gold-terms-conditions): unidade física, elegibilidade de clientes, formação de cotações, riscos e condições de resgate. Não confundir a plataforma de emissão/resgate com negociação secundária 24/7.
- [Expansão para Solana](https://www.paxos.com/blog/bringing-paxg-to-solana), datada de 25/06/2026. A mudança exige cuidado ao reconciliar oferta entre redes; não basta somar fluxos de pontes.

## Binance

- [Documentação do arquivo público](https://github.com/binance/binance-public-data): arquivos diários/mensais, esquema dos candles e timestamps de spot em microssegundos a partir de 01/01/2025.
- [Listagem S3 de PAXGUSDT horário](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/PAXGUSDT/1h/): HTTP 200; arquivo inicial disponível de agosto de 2020.
- [ZIP inicial efetivamente aberto em memória](https://data.binance.vision/data/spot/monthly/klines/PAXGUSDT/1h/PAXGUSDT-1h-2020-08.zip): primeira linha com `open_time=1598616000000`, equivalente a **28/08/2020 12:00 UTC**. Isso valida o início deste arquivo, sem garantir ausência de buracos no restante da série.
- [Anúncio oficial do perpétuo TradFi](https://www.binance.com/en-NG/support/announcement/detail/ecf7318c0d434c339e80878588e700d0): XAUUSDT disponibilizado em 05/01/2026. O evento será apenas contexto na entrega principal.
- As taxas de 2, 5 e 10 bps usadas no plano são perfis hipotéticos por execução. Não representam acesso institucional comprovado ou tabela histórica reconstruída.

## Coinbase

- [Documentação de candles](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles): limite de 300 pontos por requisição e possíveis intervalos sem observações.
- `GET https://api.exchange.coinbase.com/products/PAXG-USD`: HTTP 200, `status=online`.
- `GET https://api.exchange.coinbase.com/products/USDT-USD`: HTTP 200, `status=online`.
- Candles horários para **28/08/2020 a 29/08/2020**: ambos os pares responderam HTTP 200 com lista vazia.
- Candles horários de PAXG-USD para **01/11/2026 a 02/11/2026**: HTTP 200 com 25 linhas. Uma observação de borda ilustra a necessidade de filtrar localmente para a janela semiaberta `[start,end)`.
- Consequência: descobrir a cobertura efetiva de cada par; não assumir que a listagem atual fornece seis anos de histórico. Não foi identificada nesta auditoria a primeira data exata de cada série Coinbase.
- `1/USDCUSDT` mede o valor de USDT em USDC. Só é USD sob a hipótese adicional de USDC=USD; esse substituto não entra no painel primário nem serve para isolar risco de USDT.

## Dukascopy

- [Código e instruções do downloader](https://github.com/Leo4815162342/dukascopy-node). `package.json` consultado: versão 1.51.1 e Node >=20.
- Ambiente testado: Python 3.11.9, Node v24.14.0. O PowerShell recusou `npx.ps1`; `npx.cmd` funcionou sem alterar a política de execução.
- A CLI `npx.cmd --yes dukascopy-node@1.51.1 --help` foi executada e confirmou `-t h1`, `-p bid|ask`, `-dir`, `--waf-mode` e opções de navegador.
- Baixadas separadamente as amostras **XAUUSD h1 bid e ask de 30/10/2026 a 03/11/2026**, com `--waf-mode off --no-waf-token-cache`, sem precisar instalar navegador. Cada lado trouxe 69 linhas, timestamps e OHLC. A validação conferiu alinhamento, timestamps crescentes e ask >= bid em open/close. O período efetivamente retornado foi de 30/10/2026 00:00 UTC a 02/11/2026 23:00 UTC.
- As amostras de mercado ficaram em diretório temporário, fora do repositório. O teste não substitui a validação integral da janela de seis anos ou o teste dos minutos necessários à simulação.
- Esta é uma referência de um provedor/broker. Sua cotação não é um preço físico universal nem prova de acesso de toda a equipe à execução nesses preços.
- Licença MIT do software não determina licença dos dados. Preservar os termos do provedor; não publicar os arquivos brutos como parte do projeto.

## ETFs

- [GLD, página do emissor](https://www.spdrgoldshares.com/usa/gld/): taxa anual de 0,40%.
- [GLDM, página do emissor](https://www.ssga.com/us/en/individual/etfs/spdr-gold-minishares-gldm): taxa anual de 0,10%.
- Endpoint de arquivo histórico encontrado no HTML e testado: `https://api.spdrgoldshares.com/api/v1/historical-archive?product=gld&exchange=NYSE&lang=en`. Respondeu HTTP 200 com XLSX de 543.372 bytes. A planilha integral não foi analisada nesta revisão.
- Não usar `gldususd` de um broker como se fosse o livro oficial de GLD. Para custo de negociação do ETF, obter cotação de bolsa ou usar uma grade de spreads explicitamente suposta.
- A comparação GLD/GLDM é de custo de carregamento atual. Prêmio de cota contra NAV exige referências e horários compatíveis e ficou fora do núcleo.

## Literatura e originalidade

- Cong, Mayer e Rabetti, [Tokenizing Real-World Assets, Wharton, maio de 2026](https://wifpr.wharton.upenn.edu/wp-content/uploads/2026/05/WIFPR-Tokenizing-Real-World-Assets-Cong-Mayer-and-Rabetti.pdf). O apêndice A.2 já discute alinhamento, liquidez e descoberta de preço no ouro tokenizado. É suficiente para rejeitar a alegação de que o tema nunca foi estudado.
- Também foram localizados registros de [Tracking Accuracy and Portfolio Performance](https://www.mdpi.com/2674-1032/5/1/19), [Stale by design](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7174537) e [Which cost binds?](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7446704). Os textos integrais desses três itens não foram acessados com sucesso nesta revisão; sua qualidade e seus resultados não foram adotados como evidência empírica do projeto.
- A contribuição proposta passa a ser aplicação reproduzível, sincronização, análise de custos e matriz de decisão. Não se promete ineditismo acadêmico.

## CME

- [Aviso Globex de 13/07/2026](https://www.cmegroup.com/notices/electronic-trading/2026/07/20260713.html) e [anúncio de 11/06/2026](https://www.cmegroup.com/media-room/press-releases/2026/6/11/cme_group_to_expand247tradingforwticrudeoilandgold.html): início da negociação de fim de semana do 1OZ em 24/07/2026, com períodos de manutenção.
- Consequência: a partir de 2026, não afirmar que o PAXG é o único preço disponível de ouro no fim de semana. A reabertura estudada é a da referência XAUUSD, e não a de todo o mercado global de ouro.
