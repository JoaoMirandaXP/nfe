"""A chave de acesso (44 dígitos) já carrega metade da nota.

Antes mesmo de baixar a página dá para saber UF, CNPJ do emitente, modelo
(55 = NF-e, 65 = NFC-e), série e número. Usamos isso para escolher o parser
e para preencher campos que o HTML às vezes não mostra de forma limpa.

Layout da chave (NT 2014/002, usado no leiaute NFe v4.00):
  cUF(2) AAMM(4) CNPJ(14) mod(2) serie(3) nNF(9) tpEmis(1) cNF(8) cDV(1)
"""

import re
from dataclasses import dataclass

# Código IBGE da UF (2 primeiros dígitos da chave) → sigla.
UF_POR_CODIGO = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

_44_DIGITOS = re.compile(r"\d{44}")
_SO_DIGITOS = re.compile(r"\D+")


@dataclass(slots=True)
class ChaveInfo:
    """Campos decodificados da chave de acesso da NFe/NFC-e."""

    chave: str
    uf: str | None
    ano_mes: str           # AAMM da emissão
    cnpj_emitente: str      # 14 dígitos
    modelo: str             # '55' NF-e, '65' NFC-e
    serie: str              # sem zeros à esquerda
    numero: str             # sem zeros à esquerda
    dv_ok: bool             # dígito verificador confere (mod 11)


def extrair_chave(texto: str | None) -> str | None:
    """Primeira sequência de 44 dígitos no texto (URL ou HTML), ou None.

    Tolera a chave "espaçada" que a SEFAZ mostra na tela (blocos de 4):
    junta os dígitos e tenta de novo.
    """
    if not texto:
        return None
    m = _44_DIGITOS.search(texto)
    if m:
        return m.group(0)
    m = _44_DIGITOS.search(_SO_DIGITOS.sub("", texto))
    return m.group(0) if m else None


def _dv_valido(chave: str) -> bool:
    """Confere o dígito verificador (mod 11) dos 44 dígitos."""
    corpo, dv = chave[:43], chave[43]
    soma, peso = 0, 2
    for d in reversed(corpo):
        soma += int(d) * peso
        peso = 2 if peso == 9 else peso + 1
    resto = soma % 11
    esperado = 0 if resto in (0, 1) else 11 - resto
    return esperado == int(dv)


def decompor(chave: str) -> ChaveInfo:
    """Quebra a chave nos seus campos. Assume 44 dígitos (use `extrair_chave` antes)."""
    if len(chave) != 44 or not chave.isdigit():
        raise ValueError(f"chave de acesso inválida: {chave!r}")
    return ChaveInfo(
        chave=chave,
        uf=UF_POR_CODIGO.get(chave[0:2]),
        ano_mes=chave[2:6],
        cnpj_emitente=chave[6:20],
        modelo=chave[20:22],
        serie=chave[22:25].lstrip("0") or "0",
        numero=chave[25:34].lstrip("0") or "0",
        dv_ok=_dv_valido(chave),
    )
