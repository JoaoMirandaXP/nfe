from nfe.chave import decompor, extrair_chave

from .conftest import CHAVE_SP, URL_SP


def test_extrair_da_url():
    assert extrair_chave(URL_SP) == CHAVE_SP


def test_extrair_chave_espacada():
    # como a SEFAZ mostra na tela, em blocos de 4
    espacada = "3526 0404 7426 6500 0121 6500 7000 0512 7615 6696 6688"
    assert extrair_chave(espacada) == CHAVE_SP


def test_extrair_none():
    assert extrair_chave("sem chave aqui") is None
    assert extrair_chave(None) is None


def test_decompor_nota_real():
    info = decompor(CHAVE_SP)
    assert info.uf == "SP"
    assert info.cnpj_emitente == "04742665000121"
    assert info.modelo == "65"           # NFC-e
    assert info.serie == "7"
    assert info.numero == "51276"
    assert info.ano_mes == "2604"
    assert info.dv_ok is True            # dígito verificador da nota real confere


def test_decompor_invalida():
    import pytest

    with pytest.raises(ValueError):
        decompor("123")
