"""Testes de integridade e privacidade dos dados versionados em data/processed.

Estes arquivos alimentam o painel publicado. Os testes garantem que eles
continuam restritos a Diadema, sem setores duplicados e sem nenhum campo
que identifique pacientes.
"""
import json
import re
from pathlib import Path

import pandas as pd
import pytest

PROCESSADOS = Path(__file__).resolve().parents[1] / 'data' / 'processed'
MUNICIPIO = '3513801'
TABELAS_CENSO = ['basico', 'saneamento', 'domicilios1', 'demografia']
CAMPOS_PROIBIDOS = re.compile(r'^(CEP|IDADE|NASC|DT_NASC|SEXO|NOME|N_AIH|CNS|CPF)', re.IGNORECASE)
CHAVES_SIH = {'competencia', 'aih_a00_a09', 'valor_pago', 'aih_residentes_total'}


def test_malha_tem_778_setores_unicos_de_diadema():
    malha = json.loads((PROCESSADOS / 'setores.geojson').read_text(encoding='utf-8'))
    setores = [f['properties']['CD_SETOR'] for f in malha['features']]
    assert len(setores) == 778
    assert len(set(setores)) == len(setores)
    assert all(str(s).startswith(MUNICIPIO) for s in setores)


@pytest.mark.parametrize('tabela', TABELAS_CENSO)
def test_tabelas_do_censo_sao_so_de_diadema_e_sem_duplicidade(tabela):
    frame = pd.read_csv(PROCESSADOS / f'{tabela}.csv', dtype=str)
    assert len(frame) > 0
    assert not frame.CD_SETOR.duplicated().any()
    assert frame.CD_SETOR.str.startswith(MUNICIPIO).all()


def test_resumos_do_sih_sao_agregados_e_coerentes():
    resumos = sorted(PROCESSADOS.glob('sih_*.json'))
    assert resumos, 'nenhum resumo do SIH versionado'
    for caminho in resumos:
        resumo = json.loads(caminho.read_text(encoding='utf-8'))
        assert set(resumo) == CHAVES_SIH, caminho.name
        assert re.fullmatch(r'20\d\d-(0[1-9]|1[0-2])', resumo['competencia'])
        assert 0 <= resumo['aih_a00_a09'] <= resumo['aih_residentes_total']
        assert resumo['valor_pago'] >= 0


def test_nenhum_arquivo_publicado_tem_dado_individual():
    for caminho in PROCESSADOS.glob('*.csv'):
        colunas = pd.read_csv(caminho, nrows=0).columns
        proibidas = [c for c in colunas if CAMPOS_PROIBIDOS.match(c)]
        assert not proibidas, f'{caminho.name}: {proibidas}'
