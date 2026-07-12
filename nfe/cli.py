"""CLI da etapa 1: `nfe <url>` → JSON estruturado no stdout.

    nfe "https://www.nfce.fazenda.sp.gov.br/...ConsultaQRCode.aspx?p=..."
    nfe --bruto <url>     # imprime o html/xml cru baixado (para inspeção)

Sai com código 0 em sucesso, 1 em erro previsível (rede/parse), 2 em uso errado.
A gravação no Supabase é etapa posterior — aqui só imprimimos.
"""

import argparse
import json
import sys

from .erros import NFeErro
from .fetch import baixar
from .parse import parse


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="nfe",
        description="Baixa uma URL de NFC-e/NF-e e imprime a nota como JSON estruturado.",
    )
    ap.add_argument("url", help="URL de consulta da nota (QR code da NFC-e)")
    ap.add_argument("--bruto", action="store_true", help="imprime o html/xml cru, sem parsear")
    ap.add_argument("--timeout", type=float, default=30.0, help="timeout do download em segundos")
    ap.add_argument("--indent", type=int, default=2, help="indentação do JSON (0 = uma linha)")
    args = ap.parse_args(argv)

    try:
        payload = baixar(args.url, timeout=args.timeout)
        if args.bruto:
            sys.stdout.write(payload.texto)
            return 0
        nota = parse(payload, args.url)
    except NFeErro as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1

    print(json.dumps(nota.para_dict(), ensure_ascii=False, indent=args.indent or None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
