"""O "jeito útil": a forma estruturada da nota que sai do parse.

`Decimal` internamente (dinheiro não é float); `para_dict()` serializa para
JSON com números e datas ISO — o formato que a etapa de persistência vai
receber e que o CLI imprime.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


def _num(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


@dataclass(slots=True)
class Item:
    seq: int                       # posição na nota (1-based)
    descricao: str
    quantidade: Decimal
    valor_total: Decimal
    unidade: str | None = None
    valor_unitario: Decimal | None = None
    codigo: str | None = None      # código do produto no emitente (cProd)

    def para_dict(self) -> dict:
        return {
            "seq": self.seq,
            "codigo": self.codigo,
            "descricao": self.descricao,
            "quantidade": _num(self.quantidade),
            "unidade": self.unidade,
            "valor_unitario": _num(self.valor_unitario),
            "valor_total": _num(self.valor_total),
        }


@dataclass(slots=True)
class Emitente:
    cnpj: str | None = None
    nome: str | None = None

    def para_dict(self) -> dict:
        return {"cnpj": self.cnpj, "nome": self.nome}


@dataclass(slots=True)
class Nota:
    url: str
    formato: str                   # 'html' | 'xml' — de onde veio o parse
    emitente: Emitente
    total: Decimal
    itens: list[Item] = field(default_factory=list)
    chave_acesso: str | None = None
    uf: str | None = None
    modelo: str | None = None      # '55' NF-e, '65' NFC-e
    serie: str | None = None
    numero: str | None = None
    emitida_em: datetime | None = None

    @property
    def total_itens(self) -> Decimal:
        return sum((i.valor_total for i in self.itens), Decimal(0))

    def para_dict(self) -> dict:
        return {
            "chave_acesso": self.chave_acesso,
            "uf": self.uf,
            "modelo": self.modelo,
            "serie": self.serie,
            "numero": self.numero,
            "emitente": self.emitente.para_dict(),
            "emitida_em": self.emitida_em.isoformat() if self.emitida_em else None,
            "total": _num(self.total),
            "itens": [i.para_dict() for i in self.itens],
            "url": self.url,
            "formato": self.formato,
        }
