"""Baixar a URL da nota e dizer se voltou HTML ou XML.

Síncrono de propósito: a etapa 1 é uma chamada por nota. Quando a sala do
Matrix entrar (etapa 2), o consumidor decide se envolve isso numa thread.
"""

from dataclasses import dataclass

import httpx

from .erros import DownloadErro

# Alguns portais estaduais devolvem página vazia sem um UA de navegador.
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"


@dataclass(slots=True)
class Payload:
    texto: str
    formato: str          # 'html' | 'xml'
    content_type: str
    url_final: str        # após redirects


def _detectar_formato(content_type: str, texto: str) -> str:
    if "xml" in content_type.lower():
        return "xml"
    inicio = texto.lstrip()[:200].lower()
    if inicio.startswith("<?xml") or "<nfeproc" in inicio or "<nfe" in inicio:
        return "xml"
    return "html"


def baixar(url: str, *, timeout: float = 30.0) -> Payload:
    """GET na URL (seguindo redirects) e classifica o corpo como html/xml."""
    try:
        resp = httpx.get(
            url,
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml"},
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise DownloadErro(f"falha ao baixar {url}: {e}") from e

    content_type = resp.headers.get("content-type", "")
    return Payload(
        texto=resp.text,
        formato=_detectar_formato(content_type, resp.text),
        content_type=content_type,
        url_final=str(resp.url),
    )
