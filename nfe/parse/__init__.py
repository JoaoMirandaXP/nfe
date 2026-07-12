"""Dispatcher do parse: escolhe o parser certo para o payload.

- Payload XML → parser nacional v4.00 (qualquer UF).
- Payload HTML → parser por UF, decidida pela chave de acesso.

Adicionar uma UF nova é registrar `sigla: função` em `_HTML_PARSERS`; a
assinatura é `(payload, url, ChaveInfo|None) -> Nota`.
"""

from ..chave import decompor, extrair_chave
from ..erros import UFNaoSuportada
from ..fetch import Payload
from ..modelos import Nota
from . import sp, xml_nfe

# UF (sigla) → parser de HTML. Cresce conforme mapeamos outros portais.
_HTML_PARSERS = {
    "SP": sp.parse,
}


def parse(payload: Payload, url: str) -> Nota:
    if payload.formato == "xml":
        return xml_nfe.parse(payload, url)

    chave = extrair_chave(url) or extrair_chave(payload.texto)
    info = decompor(chave) if chave else None
    uf = info.uf if info else None

    parser = _HTML_PARSERS.get(uf)
    if parser is None:
        raise UFNaoSuportada(uf, chave)
    return parser(payload, url, info)
