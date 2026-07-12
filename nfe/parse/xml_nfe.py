"""Parser do XML da NF-e/NFC-e (leiaute nacional v4.00 — pacote PL_010e).

Vale para qualquer UF: o XML é padronizado (namespace
http://www.portalfiscal.inf.br/nfe). Aceita tanto `nfeProc` (nota + protocolo)
quanto `NFe` avulsa. Buscamos por nome local da tag, ignorando o namespace.

Caminhos usados (leiauteNFe_v4.00.xsd):
  infNFe/@Id → chave · ide/{mod,serie,nNF,dhEmi} · emit/{CNPJ|CPF,xNome}
  det/prod/{cProd,xProd,uCom,qCom,vUnCom,vProd} · total/ICMSTot/vNF
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation

from ..chave import decompor, extrair_chave
from ..erros import ParseErro
from ..fetch import Payload
from ..modelos import Emitente, Item, Nota


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _busca(el, nome: str):
    """Primeiro descendente (ou o próprio) com esse nome local."""
    for c in el.iter():
        if _local(c.tag) == nome:
            return c
    return None


def _todos(el, nome: str) -> list:
    return [c for c in el.iter() if _local(c.tag) == nome]


def _txt(el, nome: str) -> str | None:
    achado = _busca(el, nome) if el is not None else None
    return achado.text.strip() if achado is not None and achado.text else None


def _dec(texto: str | None) -> Decimal | None:
    if not texto:
        return None
    try:
        return Decimal(texto.strip())
    except InvalidOperation:
        return None


def parse(payload: Payload, url: str) -> Nota:
    try:
        raiz = ET.fromstring(payload.texto)
    except ET.ParseError as e:
        raise ParseErro(f"XML inválido: {e}") from e

    inf = _busca(raiz, "infNFe")
    if inf is None:
        raise ParseErro("XML sem elemento infNFe (não é uma NF-e/NFC-e)")

    chave = (inf.get("Id") or "").removeprefix("NFe") or _txt(raiz, "chNFe")
    chave = extrair_chave(chave)
    info = decompor(chave) if chave else None

    ide = _busca(inf, "ide")
    emit = _busca(inf, "emit")

    itens: list[Item] = []
    for det in _todos(inf, "det"):
        prod = _busca(det, "prod")
        if prod is None:
            continue
        itens.append(
            Item(
                seq=int(det.get("nItem") or len(itens) + 1),
                descricao=_txt(prod, "xProd") or "",
                codigo=_txt(prod, "cProd"),
                quantidade=_dec(_txt(prod, "qCom")) or Decimal(1),
                unidade=(_txt(prod, "uCom") or "").lower() or None,
                valor_unitario=_dec(_txt(prod, "vUnCom")),
                valor_total=_dec(_txt(prod, "vProd")) or Decimal(0),
            )
        )

    total = _dec(_txt(_busca(inf, "total"), "vNF"))
    if total is None:
        total = sum((i.valor_total for i in itens), Decimal(0))

    dh = _txt(ide, "dhEmi") if ide is not None else None
    emitida_em = None
    if dh:
        try:
            emitida_em = datetime.fromisoformat(dh)
        except ValueError:
            emitida_em = None

    return Nota(
        url=url,
        formato="xml",
        chave_acesso=chave,
        uf=info.uf if info else None,
        modelo=(info.modelo if info else None) or _txt(ide, "mod"),
        serie=(info.serie if info else None) or _txt(ide, "serie"),
        numero=(info.numero if info else None) or _txt(ide, "nNF"),
        emitente=Emitente(
            cnpj=(_txt(emit, "CNPJ") or _txt(emit, "CPF")) if emit is not None else None,
            nome=_txt(emit, "xNome") if emit is not None else None,
        ),
        emitida_em=emitida_em,
        total=total,
        itens=itens,
    )
