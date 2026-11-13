"""Testes de fumaça do painel Streamlit.

O AppTest executa o app.py sem abrir navegador nem servidor, do mesmo jeito
que o Streamlit faria para um usuário. Se qualquer aba levantar exceção,
o teste falha e o deploy não acontece.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'
ABAS = ['Extração das bases', 'Território', 'Saúde', 'Modelo e prioridades', 'Fontes e dicionário']


def executar():
    return AppTest.from_file(str(APP), default_timeout=120).run()


def test_app_abre_sem_excecoes():
    app = executar()
    assert not app.exception, [e.value for e in app.exception]


def test_app_tem_as_cinco_abas():
    app = executar()
    assert [aba.label for aba in app.tabs] == ABAS


def test_mapa_mostra_os_setores_de_diadema():
    app = executar()
    metricas = {m.label: m.value for m in app.metric}
    assert metricas['Setores no arquivo oficial'] == '778'
