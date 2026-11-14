from pathlib import Path
import json
import subprocess
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
from pipeline import ROOT, DATA, OUT, RAW, BASE, TASKS

ASSETS = ROOT / 'assets'
st.set_page_config(page_title='SanitaTech | Diadema', page_icon=str(ASSETS / 'sanitatech-mark.svg'), layout='wide')
st.logo(str(ASSETS / 'sanitatech-logo.svg'), icon_image=str(ASSETS / 'sanitatech-mark.svg'), size='large')
st.title('SanitaTech')
st.caption('Diadema · Saneamento e saúde pública · Censo 2022 / SIH-SUS 2021–2024')


def records():
    result = {}
    snapshot = DATA / 'provenance' / 'snapshot.json'
    if snapshot.exists():
        for entry in json.loads(snapshot.read_text(encoding='utf-8')).get('files', []):
            if entry.get('status'):
                row = entry['status']
                result[row['source']] = row
    for path in sorted((DATA / 'status').glob('*.json')):
        try:
            row = json.loads(path.read_text(encoding='utf-8'))
            result[row['source']] = row
        except (OSError, json.JSONDecodeError):
            pass
    return list(result.values())


def launch(task, year=None, month=None):
    key = f'sih_{year}{month:02}' if task == 'sih' else task
    processes = st.session_state.setdefault('processes', {})
    if key in processes and processes[key].poll() is None:
        st.info('Esta coleta já está em execução nesta sessão.')
        return
    (DATA / 'logs').mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(ROOT / 'pipeline.py'), task]
    if task == 'sih':
        command += ['--year', str(year), '--month', str(month)]
    with (DATA / 'logs' / f'{key}.log').open('a', encoding='utf-8') as log:
        processes[key] = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log,
                                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    st.success('Coleta iniciada. O acompanhamento é atualizado automaticamente.')


with st.sidebar:
    st.subheader('Área de estudo')
    st.write('Diadema, São Paulo')
    st.caption('IBGE 3513801 · SUS 351380')
    st.divider()
    st.write('Ambiente local')
    st.caption('Os arquivos brutos não são publicados. Não são exibidos pontos de pacientes.')
    st.link_button('Catálogo oficial do IBGE', BASE)
    st.link_button('Transferência DATASUS', 'https://datasus.saude.gov.br/transferencia-de-arquivos/')

collect, territory, health, model, sources = st.tabs([
    'Extração das bases', 'Território', 'Saúde', 'Modelo e prioridades', 'Fontes e dicionário'])

with collect:
    st.subheader('Central de extração')
    st.write('Baixe as bases oficiais e acompanhe o recorte de Diadema. Downloads concluídos são reutilizados após a conferência do hash.')
    labels = {'malha': 'Malha e atributos', 'basico': 'População e domicílios',
              'saneamento': 'Características domiciliares 2', 'domicilios1': 'Características domiciliares 1',
              'demografia': 'Idade e demografia', 'dicionario': 'Dicionário das variáveis'}
    c1, c2 = st.columns(2)
    with c1:
        selected = st.selectbox('Base do Censo 2022', list(TASKS), format_func=labels.get)
        if st.button('Extrair base do IBGE', type='primary'):
            launch(selected)
    with c2:
        year = st.selectbox('Ano da competência SIH', [2024, 2023, 2022, 2021])
        month = st.selectbox('Mês da competência', list(range(1, 13)))
        if st.button('Extrair competência SIH-SUS'):
            launch('sih', year, month)
        if st.button('Coletar período completo · 2021–2024'):
            launch('sih-periodo')
        st.caption('Arquivos RD-SP contêm AIHs processadas em SP. Residentes atendidos em outras UFs ainda não estão incluídos.')

    @st.fragment(run_every='3s')
    def progress():
        rows = records()
        done = sum(r.get('state') == 'ready' for r in rows)
        running = sum(r.get('state') in ('starting', 'downloading', 'processing') for r in rows)
        a, b, c = st.columns(3)
        a.metric('Extrações concluídas', done)
        b.metric('Em andamento', running)
        c.metric('Com falha', sum(r.get('state') == 'error' for r in rows))
        for row in rows:
            title = labels.get(row['source'], row['source'].upper())
            state = row.get('state')
            with st.expander(f'{title} · {state}', expanded=state in ('error', 'downloading')):
                if row.get('total_bytes'):
                    st.progress(min(row.get('bytes', 0) / row['total_bytes'], 1),
                                text=f"{row.get('bytes', 0) / 1024**2:.1f} / {row['total_bytes'] / 1024**2:.1f} MB")
                if row.get('error'):
                    st.error(row['error'])
                st.json(row)
        if not rows:
            st.info('Selecione uma base para iniciar a coleta.')
    progress()

with territory:
    st.subheader('Setores censitários de Diadema')
    if st.button('Atualizar território'):
        st.rerun()
    path = OUT / 'setores.geojson'
    if path.exists():
        import geopandas as gpd
        import pydeck as pdk
        geo = gpd.read_file(path)
        a, b = st.columns(2)
        a.metric('Setores no arquivo oficial', len(geo))
        b.metric('Ano de referência', '2022')
        layer = pdk.Layer('GeoJsonLayer', data=json.loads(geo.to_json()), pickable=True,
                          stroked=True, filled=True, get_fill_color=[11, 79, 92, 60],
                          get_line_color=[11, 79, 92], line_width_min_pixels=1)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(
            latitude=-23.69, longitude=-46.62, zoom=11.8),
            map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
            tooltip={'text': 'Setor: {CD_SETOR}'}))
        st.caption('Limites oficiais do Censo 2022. Este mapa ainda não representa risco sanitário.')
        coverage = []
        for name in ['basico', 'saneamento', 'domicilios1', 'demografia']:
            candidate = OUT / f'{name}.csv'
            if candidate.exists():
                table_frame = pd.read_csv(candidate, dtype=str)
                unmatched = set(geo.CD_SETOR.astype(str)) - set(table_frame.CD_SETOR)
                coverage.append({'Base': name, 'Setores com registro': len(table_frame),
                                 'Setores da malha sem registro': len(unmatched)})
        if coverage:
            st.dataframe(pd.DataFrame(coverage), hide_index=True)
            st.caption('Setores sem registro ficam ausentes. A ausência não equivale a zero e precisa ser investigada antes dos modelos.')
        st.dataframe(geo.drop(columns='geometry'), hide_index=True)
        st.download_button('Baixar malha de Diadema', path.read_bytes(), 'diadema_setores_2022.geojson', 'application/geo+json')
    else:
        st.info('A malha ficará disponível quando a extração terminar.')

with health:
    st.subheader('AIHs de residentes em Diadema · A00–A09')
    reports = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('sih_*.json'))]
    if reports:
        frame = pd.DataFrame(reports)
        st.warning('Cobertura parcial: apenas as competências abaixo, em arquivos RD-SP. AIHs são autorizações processadas; não equivalem a pessoas únicas. Valores pagos são nominais.')
        a, b = st.columns(2)
        a.metric('AIHs A00–A09 nas competências coletadas', int(frame.aih_a00_a09.sum()))
        b.metric('Valor pago nessas AIHs', f"R$ {frame.valor_pago.sum():,.2f}")
        st.plotly_chart(px.bar(frame, x='competencia', y='aih_a00_a09',
                              labels={'competencia': 'Competência coletada', 'aih_a00_a09': 'AIHs A00–A09'},
                              color_discrete_sequence=['#0B4F5C']), width='stretch')
        st.dataframe(frame, hide_index=True)
        st.download_button('Baixar resumo agregado', frame.to_csv(index=False), 'sih_diadema_competencias.csv', 'text/csv')
    else:
        st.info('Nenhuma competência de saúde processada. A coleta separa as AIHs de residentes em Diadema com diagnóstico principal A00–A09.')
    st.caption('Janela planejada: 2021–2024. DRSAI ampliado, crianças de 0–4 anos e sensibilidade à COVID serão implementados após validação do dicionário e da cobertura.')

with model:
    st.subheader('Risco, tipologia e prioridades')
    st.info('Ainda não há estimativas de risco ou custo evitável validadas. Estes resultados não podem ser usados para decidir obras nesta versão.')
    st.dataframe(pd.DataFrame([
        {'Entrega': 'Taxas por setor e suavização', 'Dependência': 'População + AIHs + correspondência CEP–setor com qualidade medida'},
        {'Entrega': 'Moran e LISA', 'Dependência': 'Taxas válidas, vizinhança, testes e correção de múltiplas comparações'},
        {'Entrega': 'Tipologia K-Means', 'Dependência': 'Dicionário e seleção das covariáveis socio-sanitárias'},
        {'Entrega': 'Regressão Binomial Negativa', 'Dependência': 'Contagens, exposição, renda, idade e diagnóstico dos resíduos'},
        {'Entrega': 'Ranking e simulador', 'Dependência': 'Modelo validado e contrafactual com incerteza quantificada'},
    ]), hide_index=True, width='stretch')
    st.write('O estudo é ecológico: associações entre setores não demonstram causalidade individual. CEPs podem abranger vários setores; o vínculo espacial precisa ser auditado.')
    st.caption('O índice da proposta será revisado quanto à unidade e à possível contagem repetida da população antes de entrar no ranking.')

with sources:
    st.subheader('Arquivos, recortes e proveniência')
    st.write('Agregados do Censo mantêm os códigos originais das variáveis. Supressões estatísticas permanecem como valores ausentes; não são convertidas em zero.')
    receipts = []
    receipt_paths = {p.name: p for p in (DATA / 'provenance').glob('*.json') if p.name != 'snapshot.json'}
    receipt_paths.update({p.name: p for p in RAW.glob('*.json')})
    for path in receipt_paths.values():
        receipts.append(dict(file=path.name.removesuffix('.json'), **json.loads(path.read_text(encoding='utf-8'))))
    if receipts:
        st.dataframe(pd.DataFrame(receipts), hide_index=True)
    table = st.selectbox('Tabela local', ['basico', 'saneamento', 'domicilios1', 'demografia'])
    path = OUT / f'{table}.csv'
    if path.exists():
        frame = pd.read_csv(path, dtype=str)
        st.write(f'{len(frame)} setores · {len(frame.columns)} variáveis')
        st.dataframe(frame, hide_index=True)
        st.download_button('Baixar recorte municipal', path.read_bytes(), path.name, 'text/csv')
    dictionaries = {p.name: p for p in (DATA / 'reference').glob('*dicionario*.xlsx')}
    dictionaries.update({p.name: p for p in RAW.glob('*dicionario*.xlsx')})
    for path in dictionaries.values():
        st.download_button('Baixar dicionário oficial', path.read_bytes(), path.name)
    st.caption('SNIS/SINISA, comunidades e hidrografia: integração pendente. A data de download não altera o ano de referência das informações.')
