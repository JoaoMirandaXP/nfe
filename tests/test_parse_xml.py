"""Parse do XML NFe v4.00 (fixtures/nfce_v4.xml)."""

from decimal import Decimal

from nfe.fetch import Payload
from nfe.parse import parse

from .conftest import CHAVE_SP


def _payload(xml: str) -> Payload:
    return Payload(texto=xml, formato="xml", content_type="application/xml", url_final="x")


def test_cabecalho(xml_nfce):
    nota = parse(_payload(xml_nfce), "arquivo.xml")
    assert nota.formato == "xml"
    assert nota.chave_acesso == CHAVE_SP
    assert nota.uf == "SP"
    assert nota.modelo == "65"
    assert nota.serie == "7"
    assert nota.numero == "51276"
    assert nota.emitente.cnpj == "04742665000121"
    assert nota.emitente.nome == "Mercado Violeta Ltda EPP"
    assert nota.emitida_em.strftime("%Y-%m-%d %H:%M:%S") == "2026-04-26 20:58:08"


def test_itens_e_total(xml_nfce):
    nota = parse(_payload(xml_nfce), "arquivo.xml")
    assert len(nota.itens) == 2
    assert nota.itens[0].descricao == "MACA GALA KG"
    assert nota.itens[0].codigo == "893"
    assert nota.itens[0].quantidade == Decimal("0.8500")
    assert nota.itens[0].valor_total == Decimal("8.48")
    assert nota.itens[1].descricao == "ARROZ TIPO 1 5KG"
    assert nota.total == Decimal("38.38")
