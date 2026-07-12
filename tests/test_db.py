"""Testes da camada de persistência que não precisam de banco.

O caminho que toca o Postgres (salvar/migrar) é verificado à mão contra o
Supabase; aqui garantimos a normalização de CNPJ (que evita comerciante
duplicado) e o erro de config claro quando falta NFE_DB_URL.
"""

import pytest

from nfe.db import _cnpj_canonico


def test_cnpj_mascara_html_e_xml_convergem():
    # HTML de SP vem mascarado; XML vem cru — ambos → mesma forma canônica
    assert _cnpj_canonico("04.742.665/0001-21") == "04.742.665/0001-21"
    assert _cnpj_canonico("04742665000121") == "04.742.665/0001-21"
    assert _cnpj_canonico(" 04742665000121 ") == "04.742.665/0001-21"


def test_cnpj_none_ou_nao_padrao():
    assert _cnpj_canonico(None) is None
    assert _cnpj_canonico("") is None
    assert _cnpj_canonico("123") == "123"  # não é CNPJ de 14 dígitos → intacto


def test_config_sem_url(monkeypatch):
    from nfe import config
    from nfe.erros import ConfigErro

    monkeypatch.delenv("NFE_DB_URL", raising=False)
    with pytest.raises(ConfigErro):
        config.db_url()
