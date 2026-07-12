"""Parser da Consulta Pública de NFC-e da SEFAZ-SP (ConsultaQRCode.aspx).

Validado contra páginas reais de nfce.fazenda.sp.gov.br. Estrutura observada:

    <table id="tabResult">
      <tr id="Item + N">
        <td>
          <span class="txtTit">MACA GALA KG</span>
          <span class="RCod">(Código: 893 )</span>
          <span class="Rqtd"><strong>Qtde.:</strong> 0,85</span>
          <span class="RUN"><strong>UN:</strong> kg</span>
          <span class="RvlUnit"><strong>Vl. Unit.:</strong> 9,98</span>
        </td>
        <td class="txtTit noWrap">Vl. Total<span class="valor">8,48</span></td>
      </tr>
    </table>
    <span class="txtTopo">Mercado Violeta Ltda EPP</span>   (emitente)
    ...CNPJ: 04.742.665/0001-21 ... Emissão: 26/04/2026 20:58:08
    <span class="chave">3526 0404 ... 6688</span>
    linhas de total: "Valor a pagar R$: 105,56"
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from ..chave import ChaveInfo, decompor, extrair_chave
from ..erros import ParseErro
from ..fetch import Payload
from ..modelos import Emitente, Item, Nota

TZ = ZoneInfo("America/Sao_Paulo")
_CNPJ_RE = re.compile(r"CNPJ:\s*([\d./-]{14,20})")
_EMISSAO_RE = re.compile(r"Emiss[ãa]o:\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})")
_SO_DIGITOS = re.compile(r"\D+")


def _dec(texto: str | None) -> Decimal | None:
    """Converte valor pt-BR ('1.234,56' / '0,85') para Decimal. None se vazio."""
    if not texto:
        return None
    limpo = re.sub(r"[^\d,.-]", "", texto)
    if not limpo:
        return None
    limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return Decimal(limpo)
    except InvalidOperation:
        return None


def _span(tr, classe: str, rotulo: str = "") -> str | None:
    el = tr.find("span", class_=classe)
    if not el:
        return None
    return el.get_text(strip=True).replace(rotulo, "").strip()


def parse(payload: Payload, url: str, info: ChaveInfo | None) -> Nota:
    soup = BeautifulSoup(payload.texto, "html.parser")
    tabela = soup.find(id="tabResult")
    if not tabela:
        raise ParseErro("página SP sem #tabResult (nota indisponível ou layout mudou)")

    itens: list[Item] = []
    for tr in tabela.find_all("tr"):
        nome_el = tr.find("span", class_="txtTit")
        if not nome_el:
            continue
        cod = _span(tr, "RCod")
        codigo = _SO_DIGITOS.sub("", cod) or None if cod else None
        unidade = _span(tr, "RUN", "UN:")
        itens.append(
            Item(
                seq=len(itens) + 1,
                descricao=nome_el.get_text(strip=True),
                codigo=codigo,
                quantidade=_dec(_span(tr, "Rqtd", "Qtde.:")) or Decimal(1),
                unidade=unidade.lower() if unidade else None,
                valor_unitario=_dec(_span(tr, "RvlUnit", "Vl. Unit.:")),
                valor_total=_dec(tr.find(class_="valor").get_text(strip=True))
                if tr.find(class_="valor")
                else Decimal(0),
            )
        )
    if not itens:
        raise ParseErro("#tabResult sem itens legíveis")

    texto = soup.get_text(" ", strip=True)
    emitente_el = soup.find(class_="txtTopo")
    cnpj_m = _CNPJ_RE.search(texto)
    emissao_m = _EMISSAO_RE.search(texto)

    total = None
    for numb in soup.find_all(class_="totalNumb"):
        contexto = numb.find_parent(["div", "tr", "li"])
        if contexto and "Valor a pagar" in contexto.get_text(" ", strip=True):
            total = _dec(numb.get_text(strip=True))
            break
    if total is None:
        total = sum((i.valor_total for i in itens), Decimal(0))

    if info is None:
        chave = extrair_chave(url) or extrair_chave(texto)
        info = decompor(chave) if chave else None

    return Nota(
        url=url,
        formato="html",
        chave_acesso=info.chave if info else None,
        uf=info.uf if info else "SP",
        modelo=info.modelo if info else "65",
        serie=info.serie if info else None,
        numero=info.numero if info else None,
        emitente=Emitente(
            cnpj=cnpj_m.group(1) if cnpj_m else (info.cnpj_emitente if info else None),
            nome=emitente_el.get_text(strip=True) if emitente_el else None,
        ),
        emitida_em=(
            datetime.strptime(
                f"{emissao_m.group(1)} {emissao_m.group(2)}", "%d/%m/%Y %H:%M:%S"
            ).replace(tzinfo=TZ)
            if emissao_m
            else None
        ),
        total=total,
        itens=itens,
    )
