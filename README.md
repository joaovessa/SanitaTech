# SanitaTech

Implementação inicial da proposta de saneamento e saúde em Diadema. Python 3.13, Streamlit e extração de fontes oficiais. Nenhum resultado epidemiológico é simulado.

## Executar no Windows

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra http://localhost:8501. Na central de extração, escolha uma base. Também é possível executar:

```powershell
.\.venv\Scripts\python.exe pipeline.py censo
.\.venv\Scripts\python.exe pipeline.py sih --year 2024 --month 1
.\.venv\Scripts\python.exe pipeline.py sih-periodo
```

## Disponível

- Download retomável por arquivo com recibo, URL e SHA-256; falhas ficam visíveis.
- Recorte de tabelas oficiais pelo prefixo 3513801 e validação de duplicidade.
- Malha oficial de setores filtrada para Diadema e mapa interativo.
- Leitura de RD-SP em DBC, filtro MUNIC_RES=351380 e diagnóstico principal A00–A09.
- Resumos por competência: número de AIHs e soma nominal de VAL_TOT.
- Fila sequencial 2021–2024 que pula competências concluídas; reinicie o comando para repetir falhas.
- Exportação apenas de resumos de saúde; nenhum ponto de paciente no dashboard.

## Limites desta primeira implementação

RD-SP não cobre residentes atendidos em outras UFs. Competência não é data de admissão. AIH não é pessoa única; revisar tipo/continuidade antes de contabilizar internações. Não chamar cobertura parcial de série completa. A extração não deduplica AIHs entre competências. Cobertura nacional e regra de continuidade precisam anteceder taxas e modelos.

O join CEP–setor depende de fonte e validação; não inferir setor com falsa precisão a partir do centroide de um CEP. Covariáveis mantêm os códigos do IBGE até validar o dicionário. Sem esse vínculo e sem validação, não há taxas, LISA, regressão, ranking ou custo evitável. A tipologia, modelo espacial, DRSAI ampliado, renda, hidrografia, comunidades e SINISA ainda precisam ser integrados.

`data/raw` pode conter dados individuais públicos de saúde: uso local, não versionar nem publicar. `.gitignore` exclui arquivos brutos, estado de execução, ambiente e segredos; permite recortes censitários, resumos municipais de saúde, referências e proveniência. Nenhuma credencial é armazenada pelo projeto. Nenhum recurso Azure foi criado nesta etapa.

Consulte [HANDOFF.md](HANDOFF.md) para o contexto, limites, estado da coleta e próximos passos. Os recortes já coletados estão em `data/processed`, o dicionário em `data/reference` e o manifesto com hashes em `data/provenance/snapshot.json`.

## Verificação inicial (13/11/2026)

As seis extrações do Censo concluíram: malha e básico com 778 setores; domicílios 1, domicílios 2 e demografia com 771 registros cada; dicionário oficial salvo. Não há chaves duplicadas nos quatro recortes tabulares. O total de população do básico é 393.237. A diferença de sete setores entre malha e tabelas temáticas precisa de investigação; não preencher com zero.

Competência piloto RD-SP 2024-01: 2.027 AIHs de residentes, sendo 14 A00–A09 e R$ 5.335,77 de VAL_TOT. Estes números validam apenas essa extração, não a cobertura do período ou a contagem de internações únicas. O AppTest do Streamlit abriu as cinco abas sem exceções e o healthcheck HTTP retornou 200. Inspeção visual no navegador não foi possível por bloqueio da abertura automática. A fila das outras competências foi iniciada em segundo plano.

## Fontes

- IBGE: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/
- DATASUS: ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/
- Proposta fornecida: SanitaTech_Proposta.pdf.
