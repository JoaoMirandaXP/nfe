"""Configuração da persistência — tudo por variável de ambiente.

Este repositório é **público**: nenhuma credencial mora aqui. A URL do banco
vem de `NFE_DB_URL`. Para não deixá-la solta no shell, aponte `NFE_ENV` para
um arquivo de ambiente guardado FORA do repo (ex.: `control/nfe.env`); ele é
carregado se o `python-dotenv` estiver instalado (extra `db`).

    NFE_ENV=/caminho/para/control/nfe.env  uv run nfe --salvar <url>
"""

import os

from .erros import ConfigErro


def _carregar_env() -> None:
    caminho = os.environ.get("NFE_ENV")
    if not caminho:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:  # sem o extra 'db'; as vars já podem estar exportadas
        return
    load_dotenv(caminho)


_carregar_env()


def db_url() -> str:
    url = os.environ.get("NFE_DB_URL")
    if not url:
        raise ConfigErro(
            "NFE_DB_URL não definida. Guarde as credenciais FORA deste repo público "
            "(ex.: control/nfe.env) e rode com NFE_ENV apontando para ele, "
            "ou exporte NFE_DB_URL no ambiente."
        )
    return url
