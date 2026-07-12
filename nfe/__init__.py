"""nfe — de uma URL de nota fiscal eletrônica para dados estruturados.

Fluxo (etapa 1): `url → baixar → parse → Nota` (JSON, pronto para persistir).
A gravação no Supabase e o recebimento pela sala do Matrix são etapas
posteriores; este pacote só se ocupa de transformar a URL em `Nota`.
"""

from .fetch import Payload, baixar
from .modelos import Emitente, Item, Nota
from .parse import parse

__all__ = ["Payload", "baixar", "Emitente", "Item", "Nota", "parse", "consultar"]


def consultar(url: str, *, timeout: float = 30.0) -> Nota:
    """Baixa a URL da nota e devolve a `Nota` estruturada. Atalho de `baixar`+`parse`."""
    return parse(baixar(url, timeout=timeout), url)
