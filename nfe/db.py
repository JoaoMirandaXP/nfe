"""Persistência da `Nota` no Postgres (Supabase), reaproveitando as tabelas
`comerciantes`/`notas`/`itens` da infraestrutura existente.

Modular de propósito: o parse (núcleo) não conhece banco; só quem chama
`salvar()`/`migrar()` puxa o `psycopg` (extra `db`). Sem a camada de produtos
canônicos/LLM do notas_fiscais — `itens.produto_id` fica nulo.

Idempotência (a nota nunca é gravada duas vezes):
- `notas.chave_acesso` é unique → `on conflict (chave_acesso) do update`;
- os itens são apagados e reinseridos na mesma transação.
"""

import json
import re
import sys
from pathlib import Path

from .config import db_url
from .erros import NFeErro
from .modelos import Nota

MIGRACOES = Path(__file__).resolve().parent.parent / "migrations"


def _conn():
    # import tardio: só quem persiste precisa do psycopg (extra `db`)
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(db_url(), row_factory=dict_row)


def _cnpj_canonico(cnpj: str | None) -> str | None:
    """Normaliza o CNPJ para a máscara NN.NNN.NNN/NNNN-NN.

    HTML de SP vem mascarado, XML vem cru — normalizando, os dois caem no
    MESMO comerciante (evita duplicar). Quem não for CNPJ de 14 dígitos passa
    intacto.
    """
    if not cnpj:
        return None
    d = re.sub(r"\D", "", cnpj)
    if len(d) != 14:
        return cnpj or None
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def _upsert_comerciante(cur, cnpj: str | None, nome: str | None) -> int | None:
    cnpj = _cnpj_canonico(cnpj)
    if cnpj:
        cur.execute(
            """insert into comerciantes (cnpj, nome) values (%s, %s)
               on conflict (cnpj) do update set nome = excluded.nome
               returning id""",
            (cnpj, nome),
        )
        return cur.fetchone()["id"]
    if not nome:
        return None
    cur.execute("select id from comerciantes where nome = %s order by id limit 1", (nome,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("insert into comerciantes (nome) values (%s) returning id", (nome,))
    return cur.fetchone()["id"]


def salvar(nota: Nota) -> dict:
    """Grava a nota e seus itens (idempotente por chave_acesso).

    Devolve {id, inserida, itens, comerciante_id}. Reprocessar a mesma nota
    atualiza a linha existente — nunca cria uma segunda.
    """
    if not nota.chave_acesso:
        raise NFeErro("nota sem chave_acesso — não dá para persistir de forma idempotente")

    dados = json.dumps(nota.para_dict(), ensure_ascii=False)
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("select id from notas where chave_acesso = %s", (nota.chave_acesso,))
            inserida = cur.fetchone() is None

            comerciante_id = _upsert_comerciante(cur, nota.emitente.cnpj, nota.emitente.nome)
            cur.execute(
                """insert into notas
                     (chave_acesso, url_sefaz, comerciante_id, emitida_em,
                      total_extraido, status, origem_extracao, dados_brutos)
                   values (%s, %s, %s, %s, %s, 'processada', 'sefaz', %s)
                   on conflict (chave_acesso) do update set
                     url_sefaz       = excluded.url_sefaz,
                     comerciante_id  = excluded.comerciante_id,
                     emitida_em      = excluded.emitida_em,
                     total_extraido  = excluded.total_extraido,
                     origem_extracao = 'sefaz',
                     -- não rebaixa uma nota já validada/divergente pela etapa 3
                     status = case when notas.status in ('validada', 'divergente')
                                   then notas.status else 'processada' end,
                     dados_brutos    = excluded.dados_brutos
                   returning id""",
                (
                    nota.chave_acesso, nota.url, comerciante_id, nota.emitida_em,
                    nota.total, dados,
                ),
            )
            nota_id = cur.fetchone()["id"]

            cur.execute("delete from itens where nota_id = %s", (nota_id,))
            for it in nota.itens:
                cur.execute(
                    """insert into itens
                         (nota_id, descricao_original, quantidade, unidade,
                          valor_unitario, valor_total)
                       values (%s, %s, %s, %s, %s, %s)""",
                    (nota_id, it.descricao, it.quantidade, it.unidade,
                     it.valor_unitario, it.valor_total),
                )
        conn.commit()

    return {
        "id": str(nota_id),
        "inserida": inserida,
        "itens": len(nota.itens),
        "comerciante_id": comerciante_id,
    }


def migrar() -> list[str]:
    """Aplica os .sql de migrations/. Devolve os nomes aplicados ([] = nada a fazer).

    Idempotente e cuidadoso com privilégios: se as tabelas já existem (caso do
    banco `financeiro`), não tenta DDL nenhum — assim o role de serviço, que só
    tem rw de dados e não CREATE no schema, roda como no-op. O DDL só dispara
    num banco novo, onde deve ser executado com um role dono/admin.
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """select to_regclass('public.comerciantes') as c,
                          to_regclass('public.notas')        as n,
                          to_regclass('public.itens')        as i"""
            )
            alvo = cur.fetchone()
            if all(alvo[k] is not None for k in ("c", "n", "i")):
                return []
            aplicadas = []
            for arquivo in sorted(MIGRACOES.glob("*.sql")):
                cur.execute(arquivo.read_text(encoding="utf-8"))
                aplicadas.append(arquivo.name)
        conn.commit()
    return aplicadas


def cli_migrar(argv: list[str] | None = None) -> int:
    """Entrypoint do console script `nfe-migrate`."""
    try:
        feitas = migrar()
    except NFeErro as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    if feitas:
        print("migrations aplicadas: " + ", ".join(feitas))
    else:
        print("schema já presente — nada a aplicar (no-op)")
    return 0
