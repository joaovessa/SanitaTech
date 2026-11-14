<p align="center"><img src="assets/sanitatech-logo.svg" alt="SanitaTech" height="56"></p>

# SanitaTech — Onde o esgoto custa saúde

Painel de dados que cruza saneamento e saúde pública em Diadema/SP para apoiar a priorização de obras de esgoto. Global Solution 02/2026 · Cloud Solutions & Scalable Infrastructure · tema CitizenTech.

**Aplicação publicada:** https://sanitatech-diadema-fwa8a2c7e6bzhgev.brazilsouth-01.azurewebsites.net

## Problema e proposta

Esgoto a céu aberto ou sem tratamento gera internações por doenças de veiculação hídrica, mas esse custo fica diluído no orçamento do SUS e não entra na decisão de onde investir. Diadema concentra 109 favelas e comunidades urbanas (22,3% da população, Censo 2022) e está recebendo obras de universalização do saneamento até 2029.

O SanitaTech reúne, por setor censitário, as condições de saneamento do Censo 2022 e as internações do SIH-SUS por diarreias e gastroenterites infecciosas (CID A00–A09). O painel publicado mostra o território, a série de internações e o custo pago pelo SUS, e prepara a base para o modelo espacial que vai apontar quais setores devem receber obras primeiro.

## Integrantes

| Nome | RM | Turma |
| --- | --- | --- |
| João Silva de Araújo | 561420 | 2TSC |
| Esther Macedo | 566197 | 2TSC |
| Pedro Enrique Kaune Nascimento | _(a preencher)_ | 2TSC |

## Origem do projeto

Projeto criado pela equipe. A ideia nasceu no trabalho final de Ciência de Dados (análise espacial de esgoto e saúde em Diadema) e foi adaptada para esta Global Solution: ganhou testes automatizados, modo de execução em nuvem, identidade visual própria e um pipeline de CI/CD no GitHub Actions com deploy no Azure.

## Tecnologias

- Python 3.13, Streamlit, pandas, GeoPandas, Plotly e pydeck
- pytest e `streamlit.testing` (AppTest) para os testes
- GitHub Projects, Issues, branches e Pull Requests para planejar e versionar
- GitHub Actions para CI/CD
- Azure App Service (Linux, Python 3.13) para hospedar o painel

## Como executar localmente

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
.\.venv\Scripts\python.exe -m pytest
```

Abra http://localhost:8501. Para simular a versão publicada, defina `SANITATECH_MODO=nuvem` antes de iniciar o Streamlit: os botões de coleta somem e o painel usa só os dados versionados. No Azure isso acontece sozinho.

## Como usamos o GitHub

- **Project e Issues:** o quadro [SanitaTech — Entregas](https://github.com/users/PedroKaune/projects/1) acompanha uma história de usuário (#1) e quatro tarefas (#2 a #5), cada uma com responsável e status Todo → In Progress → Done.
- **Branches:** cada tarefa foi feita numa branch própria a partir da `main`: `ci/testes-e-workflow`, `feature/deploy-azure`, `feature/identidade-visual`, `feature/ajuste-demo` e `docs/readme-entrega`.
- **Commits:** mensagens no padrão `tipo: descrição` (`test`, `ci`, `feat`, `docs`), cada uma citando a issue com `Refs #N`.
- **Pull Requests:** toda alteração entrou na `main` por PR, com `Closes #N` ligando a issue e o check **Build e testes** aprovado antes do merge.

## Workflow de CI/CD

Arquivo: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)

| Gatilho | O que roda |
| --- | --- |
| Pull request para a `main` | job **Build e testes** |
| Push na `main` (merge de PR) | **Build e testes** e, se passar, **Deploy no Azure App Service** |
| Manual (`workflow_dispatch`) | os mesmos jobs, conforme a branch escolhida |

**Build e testes** (`ubuntu-latest`, Python 3.13): instala `requirements.txt` e `requirements-dev.txt`, compila os módulos com `compileall` e roda o pytest. Os testes abrem o painel com AppTest e conferem as cinco abas e os 778 setores, validam que os dados publicados são só de Diadema e sem duplicidade, e garantem que nenhum arquivo versionado tem CEP, idade, sexo ou outro dado individual de paciente.

**Deploy no Azure App Service** (só depois dos testes, só na `main`):

1. instala as dependências do `requirements.txt` na pasta `__oryx_packages__`, que o App Service coloca no `PYTHONPATH` ao iniciar;
2. grava o commit, o número do run e o horário em `static/version.json`;
3. empacota a aplicação em `app.zip`, sem testes, workflows e dados brutos, e publica com `azure/webapps-deploy@v3`;
4. valida o app no ar: espera o healthcheck `/_stcore/health` responder e confere que `/app/static/version.json` traz o mesmo commit que acabou de passar no CI. Se não bater, o workflow falha.

O mesmo `version.json` aparece no rodapé da barra lateral do painel, o que mostra a qualquer pessoa qual commit está no ar.

**Segredos:** o publish profile do App Service fica no secret `AZURE_WEBAPP_PUBLISH_PROFILE` e o nome do app na variável `AZURE_WEBAPP_NAME`, ambos em *Settings → Secrets and variables → Actions*. Nenhuma credencial está no código.

## Nuvem

- **Provedor:** Microsoft Azure (assinatura Azure for Students)
- **Serviço:** Azure App Service, Linux, plano B1, runtime Python 3.13, região Brazil South
- **Inicialização:** `python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true`
- **Dependências:** chegam prontas no pacote, instaladas pelo workflow; o servidor não compila nada. O modo nuvem liga sozinho porque o App Service define `WEBSITE_SITE_NAME`.
- **URL:** https://sanitatech-diadema-fwa8a2c7e6bzhgev.brazilsouth-01.azurewebsites.net

O app começou no plano gratuito F1, mas a instalação das dependências (GeoPandas) estourou a cota diária de CPU no primeiro deploy e o Azure suspendeu o app. Por isso o plano foi elevado para B1, que custa cerca de US$ 0,02 por hora do crédito de estudante.

## Evidências

| Requisito | Onde ver | Captura |
| --- | --- | --- |
| Project e Issues | [Project](https://github.com/users/PedroKaune/projects/1) · [Issues](https://github.com/joaovessa/SanitaTech/issues?q=is%3Aissue) | [01-project.png](docs/evidencias/01-project.png) · [02-issues.png](docs/evidencias/02-issues.png) |
| Repositório e `main` | [código](https://github.com/joaovessa/SanitaTech) | — |
| Branches e commits | [branches](https://github.com/joaovessa/SanitaTech/branches/all) · [commits](https://github.com/joaovessa/SanitaTech/commits/main) | [03-branches-commits.png](docs/evidencias/03-branches-commits.png) |
| Pull Requests e merge | [PRs](https://github.com/joaovessa/SanitaTech/pulls?q=is%3Apr) | [04-pull-request.png](docs/evidencias/04-pull-request.png) |
| Workflow configurado e executado | [ci-cd.yml](.github/workflows/ci-cd.yml) · [execuções](https://github.com/joaovessa/SanitaTech/actions) | [05-actions-ci.png](docs/evidencias/05-actions-ci.png) · [06-actions-deploy.png](docs/evidencias/06-actions-deploy.png) |
| App publicado no Azure | https://sanitatech-diadema-fwa8a2c7e6bzhgev.brazilsouth-01.azurewebsites.net | [07-app-publicado.png](docs/evidencias/07-app-publicado.png) |
| Alteração atualizada pelo workflow | PR `feature/ajuste-demo` e o run de deploy correspondente | [08-app-antes.png](docs/evidencias/08-app-antes.png) · [09-app-depois.png](docs/evidencias/09-app-depois.png) |

A alteração de demonstração troca o subtítulo do painel para "Onde o esgoto custa saúde". Nas capturas 08 e 09, o rodapé da barra lateral mostra o commit publicado antes e depois, e esse commit é o mesmo do run de deploy na captura 06.

## Detalhes técnicos da coleta de dados

### Disponível

- Download retomável por arquivo com recibo, URL e SHA-256; falhas ficam visíveis.
- Recorte de tabelas oficiais pelo prefixo 3513801 e validação de duplicidade.
- Malha oficial de setores filtrada para Diadema e mapa interativo.
- Leitura de RD-SP em DBC, filtro MUNIC_RES=351380 e diagnóstico principal A00–A09.
- Resumos por competência: número de AIHs e soma nominal de VAL_TOT.
- Fila sequencial 2021–2024 que pula competências concluídas; reinicie o comando para repetir falhas.
- Exportação apenas de resumos de saúde; nenhum ponto de paciente no dashboard.

### Limites desta primeira implementação

RD-SP não cobre residentes atendidos em outras UFs. Competência não é data de admissão. AIH não é pessoa única; revisar tipo/continuidade antes de contabilizar internações. Não chamar cobertura parcial de série completa. A extração não deduplica AIHs entre competências. Cobertura nacional e regra de continuidade precisam anteceder taxas e modelos.

O join CEP–setor depende de fonte e validação; não inferir setor com falsa precisão a partir do centroide de um CEP. Covariáveis mantêm os códigos do IBGE até validar o dicionário. Sem esse vínculo e sem validação, não há taxas, LISA, regressão, ranking ou custo evitável. A tipologia, modelo espacial, DRSAI ampliado, renda, hidrografia, comunidades e SINISA ainda precisam ser integrados.

`data/raw` pode conter dados individuais públicos de saúde: uso local, não versionar nem publicar. `.gitignore` exclui arquivos brutos, estado de execução, ambiente e segredos; permite recortes censitários, resumos municipais de saúde, referências e proveniência. Nenhuma credencial é armazenada pelo projeto.

Consulte [HANDOFF.md](HANDOFF.md) para o contexto, limites, estado da coleta e próximos passos. Os recortes já coletados estão em `data/processed`, o dicionário em `data/reference` e o manifesto com hashes em `data/provenance/snapshot.json`.

### Verificação inicial (13/11/2026)

As seis extrações do Censo concluíram: malha e básico com 778 setores; domicílios 1, domicílios 2 e demografia com 771 registros cada; dicionário oficial salvo. Não há chaves duplicadas nos quatro recortes tabulares. O total de população do básico é 393.237. A diferença de sete setores entre malha e tabelas temáticas precisa de investigação; não preencher com zero.

Competência piloto RD-SP 2024-01: 2.027 AIHs de residentes, sendo 14 A00–A09 e R$ 5.335,77 de VAL_TOT. Estes números validam apenas essa extração, não a cobertura do período ou a contagem de internações únicas. O AppTest do Streamlit abriu as cinco abas sem exceções e o healthcheck HTTP retornou 200. Inspeção visual no navegador não foi possível por bloqueio da abertura automática. A fila das outras competências foi iniciada em segundo plano.

### Fontes

- IBGE: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/
- DATASUS: ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/
- Proposta fornecida: SanitaTech_Proposta.pdf.
