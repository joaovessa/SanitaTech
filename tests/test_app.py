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


def test_modo_nuvem_desliga_a_coleta(monkeypatch):
    monkeypatch.delenv('WEBSITE_SITE_NAME', raising=False)
    monkeypatch.setenv('SANITATECH_MODO', 'nuvem')
    app = executar()
    assert not app.exception
    rotulos = [b.label for b in app.button]
    assert 'Extrair base do IBGE' not in rotulos
    assert any('coleta fica desativada' in i.value for i in app.info)


def test_modo_local_mantem_a_coleta(monkeypatch):
    monkeypatch.delenv('SANITATECH_MODO', raising=False)
    monkeypatch.delenv('WEBSITE_SITE_NAME', raising=False)
    app = executar()
    assert 'Extrair base do IBGE' in [b.label for b in app.button]


def test_app_service_liga_o_modo_nuvem_sozinho(monkeypatch):
    monkeypatch.delenv('SANITATECH_MODO', raising=False)
    monkeypatch.setenv('WEBSITE_SITE_NAME', 'sanitatech-diadema')
    app = executar()
    assert 'Extrair base do IBGE' not in [b.label for b in app.button]
