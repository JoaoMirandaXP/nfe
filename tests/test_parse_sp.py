"""Parse da nota SP real (fixtures/sp_nfce.html — Mercado Violeta, 11 itens)."""

from decimal import Decimal

from nfe.fetch import Payload
from nfe.parse import parse

from .conftest import CHAVE_SP, URL_SP


def _payload(html: str) -> Payload:
    return Payload(texto=html, formato="html", content_type="text/html", url_final=URL_SP)


def test_cabecalho(html_sp):
    nota = parse(_payload(html_sp), URL_SP)
    assert nota.formato == "html"
    assert nota.uf == "SP"
    assert nota.modelo == "65"
    assert nota.serie == "7"
    assert nota.numero == "51276"
    assert nota.chave_acesso == CHAVE_SP
    assert nota.emitente.nome == "Mercado Violeta Ltda EPP"
    assert nota.emitente.cnpj == "04.742.665/0001-21"
    assert nota.emitida_em is not None
    assert nota.emitida_em.strftime("%Y-%m-%d %H:%M:%S") == "2026-04-26 20:58:08"


def test_itens(html_sp):
    nota = parse(_payload(html_sp), URL_SP)
    assert len(nota.itens) == 11

    primeiro = nota.itens[0]
    assert primeiro.seq == 1
    assert primeiro.descricao == "MACA GALA KG"
    assert primeiro.codigo == "893"
    assert primeiro.quantidade == Decimal("0.85")
    assert primeiro.unidade == "kg"
    assert primeiro.valor_unitario == Decimal("9.98")
    assert primeiro.valor_total == Decimal("8.48")


def test_total_bate_com_soma(html_sp):
    nota = parse(_payload(html_sp), URL_SP)
    assert nota.total == Decimal("105.56")            # "Valor a pagar R$"
    assert nota.total_itens == Decimal("105.56")      # soma dos 11 itens confere


def test_json_serializavel(html_sp):
    import json

    d = parse(_payload(html_sp), URL_SP).para_dict()
    json.dumps(d)  # não pode levantar
    assert d["total"] == 105.56
    assert d["emitente"]["nome"] == "Mercado Violeta Ltda EPP"
    assert d["itens"][0]["descricao"] == "MACA GALA KG"
