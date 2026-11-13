# Handoff — SanitaTech

Atualizado em 13/11/2026. Este arquivo contextualiza a primeira implementação; o estado exato dos dados enviados está em `data/provenance/snapshot.json`.

## Objetivo e contexto

Projeto acadêmico de Ciência de Dados/FIAP, baseado no PDF SanitaTech_Proposta.pdf fornecido pelo usuário. Pretende investigar a associação ecológica entre saneamento e saúde em Diadema/SP, estimar custos e apoiar a priorização de obras. Produto previsto: Streamlit com mapa de risco, tipologia, ranking e simulador. Unidade pretendida: setor censitário; janela de saúde 2021–2024, centrada no Censo 2022.

O usuário autorizou construir do zero, coletar bases oficiais e enviar a primeira versão para https://github.com/joaovessa/SanitaTech. O repositório estava vazio e é público. Nenhuma implantação na nuvem foi realizada.

## O que foi implementado

- `app.py`: cinco abas — extração, território, saúde, modelo/prioridades e fontes/dicionário. Downloads podem ser iniciados pela interface; andamento e falhas são registrados localmente. Há mapa interativo dos limites dos setores e exportações municipais.
- `pipeline.py`: descoberta de arquivos nos catálogos oficiais, download com SHA-256 e recibo, leitura de CSV/GeoPackage/DBC, filtros municipais, validação de duplicidade e resumos por competência. Reutiliza downloads concluídos cujo hash confere; um download parcial é reiniciado do início.
- Censo: leitura em blocos para filtrar Diadema sem carregar todas as tabelas nacionais em memória. Trata nomes diferentes da chave do setor e UTF-8/Latin-1 conforme observado nos arquivos.
- SIH: leitura DBC via pyreaddbc/DBF, filtro `MUNIC_RES=351380`, diagnóstico principal A00–A09 e soma nominal de `VAL_TOT`. O produto grava somente resumos municipais; os arquivos individuais baixados permanecem locais.
- `scripts/prepare_handoff.py`: gera manifesto da fotografia publicável, com hashes dos recortes e recibos dos arquivos de origem. Copia o dicionário oficial para `data/reference`.
- `.streamlit/config.toml`, dependências diretas e lock do ambiente Windows/Python 3.13. As dependências científicas estão instaladas, mas os modelos ainda não estão implementados.

## Dados enviados no primeiro commit

Fotografia de 13/11/2026 às 11:40:45, horário de São Paulo (14:40:45 UTC):

| Base | Recorte disponível |
| --- | --- |
| Malha IBGE | 778 setores, GeoJSON WGS84 |
| Básico do Censo | 778 setores; população somada de 393.237 |
| Características domiciliares 1 | 771 setores |
| Características domiciliares 2 | 771 setores |
| Demografia | 771 setores |
| Dicionário oficial | XLSX da revisão disponível em 13/11/2026 |
| SIH RD-SP | 9 competências concluídas: janeiro a agosto/2021 e janeiro/2024 |

O manifesto é a referência de quais arquivos compõem esta fotografia; coleta em andamento pode produzir outros arquivos locais depois dela. Todos os recortes tabulares do Censo foram conferidos quanto a chaves duplicadas: nenhuma encontrada. Não transformar os sete setores ausentes nas tabelas temáticas em zero; investigar sua situação e reconciliar com a malha.

Piloto SIH 2024-01: 2.027 AIHs de residentes, 14 com diagnóstico principal A00–A09, R$ 5.335,77 pagos nesse grupo. Estes números não representam o período completo nem uma contagem validada de internações únicas.

Fontes oficiais:

- IBGE: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/
- DATASUS: ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/

Não foram enviados: DBCs, DBFs, CEP/idade/sexo individuais, arquivos nacionais brutos, logs de execução, credenciais ou `.venv`. Os dados públicos enviados são recortes censitários, geometria, dicionário, recibos e resumos municipais de saúde.

## Executar e continuar a coleta

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abrir http://127.0.0.1:8501. Os dados versionados permitem explorar a primeira versão sem refazer os downloads. O manifesto fornece o estado de origem mesmo sem `data/status` local.

```powershell
.\.venv\Scripts\python.exe pipeline.py censo
.\.venv\Scripts\python.exe pipeline.py sih-periodo
```

A fila SIH 2021–2024 foi iniciada na máquina local. É um processo local, não um serviço durável: pode parar quando a sessão ou máquina encerrar. Antes de iniciar outra fila na mesma pasta, conferir se a anterior ainda está em execução. Não há trava entre processos/sessões; evitar coletas simultâneas do mesmo arquivo. A fila pula competências marcadas como concluídas no estado local; em um clone novo sem esse estado poderá recalculá-las. Reiniciar a fila tenta novamente as competências com falha. Para atualizar uma fotografia, concluir/inspecionar as coletas, rodar `scripts/prepare_handoff.py`, conferir o manifesto e adicionar somente seus arquivos concluídos ao próximo commit.

## Limites metodológicos que devem guiar a continuação

1. CEP não identifica necessariamente um único setor. Ainda não existe correspondência CEP–setor validada. Não atribuir setor ao paciente com falsa precisão usando apenas centroide do CEP. Medir ambiguidades, cobertura e perdas; pode ser necessário rever a unidade de análise.
2. RD-SP cobre processamento em SP, não residentes atendidos em qualquer UF. Expandir a cobertura para outras UFs ou quantificar e declarar a perda antes das análises.
3. Competência é processamento, não admissão. AIH não é pessoa única e pode ter continuidade. Validar tipo/continuidade e regras de contagem/deduplicação antes de usar o termo “internações”. A primeira versão não deduplica entre competências.
4. Os códigos originais do Censo foram preservados; ainda falta mapear variáveis pelo dicionário e tratar supressões (`X`, outros marcadores), nulos e denominadores. Não presumir que todas as covariáveis propostas, inclusive renda, existem por setor nessa fonte.
5. DRSAI ampliado, crianças de 0–4 anos, leptospirose e sensibilidade à COVID ainda não foram implementados. A primeira extração considera A00–A09 sem restrição etária.
6. Não há taxas, suavização Bayesiana, Moran/LISA, K-Means, regressão ou estimativas de custo evitável calculadas. A aba do modelo explicita suas dependências; não apresentar resultados demonstrativos como observados.
7. Associação ecológica não comprova causalidade. Contrafactual do modelo não deve ser chamado de economia garantida. Revisar a unidade do índice proposto e possível contagem repetida da população.

## Próximos passos, em ordem

1. Concluir as 48 competências e revisar erros; reconciliar cobertura municipal com TabNet, com os mesmos critérios e datas. Conferir população com IBGE e investigar os sete setores sem tabelas temáticas.
2. Definir as regras de AIH, continuidade e datas, a classificação DRSAI e o recorte etário; implementar controles de qualidade e testes dos limites que mudam as contagens.
3. Validar dicionário do Censo, construir variáveis de saneamento, idade e densidade e verificar disponibilidade real de renda. Produzir um contrato de dados e relatório de cobertura dos joins.
4. Resolver a viabilidade do vínculo espacial de saúde. Caso inviável, documentar e revisar o desenho com o orientador antes de estimar riscos por setor.
5. Integrar comunidades, hidrografia e contexto atualizado SNIS/SINISA, preservando fonte, revisão, escala e referência temporal.
6. Implementar taxas com denominadores adequados, suavização e autocorrelação com testes/correção de múltiplas comparações. Criar tipologia K-Means com padronização e diagnóstico de estabilidade.
7. Ajustar Binomial Negativa com offset/covariáveis; verificar convergência, confundimento e resíduos espaciais. Só então definir eventual modelo espacial e contrafactual com incerteza.
8. Implementar ranking, simulador, relatório e apresentação com limitações e rastreabilidade. Confirmar as datas da FIAP com o usuário.
9. Depois de definir o uso e orçamento, preparar implantação Azure, CI e gestão de segredos. Não criar recursos pagos apenas porque a conta está autenticada.

## Acessos e operação

GitHub confirmado como `joaovessa`. Azure CLI foi trocado para a conta estudantil solicitada, com Azure for Students ativa e padrão. Não há tokens nem identificadores de assinatura neste repositório; verificar `az account show` antes de uma implantação. Não usar a conta anterior nem presumir que as credenciais estarão disponíveis em outra máquina.

Servidor local inicial: porta 8501. A abertura automática do navegador foi bloqueada pela política da ferramenta; o link é acessível manualmente. Verificações realizadas: compilação Python, healthcheck HTTP 200 e AppTest Streamlit com cinco abas sem exceções. A inspeção visual do mapa no navegador não foi verificada. Ainda não existem testes epidemiológicos nem validação do modelo.
