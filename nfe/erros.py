"""Exceções do pacote — uma hierarquia rasa para o CLI diferenciar mensagens."""


class NFeErro(Exception):
    """Base de todos os erros previsíveis do fluxo."""


class DownloadErro(NFeErro):
    """Falha ao baixar a página da nota (rede, timeout, status HTTP)."""


class ParseErro(NFeErro):
    """A página foi baixada mas não deu para extrair os dados da nota."""


class UFNaoSuportada(ParseErro):
    """Não há parser de HTML para a UF da nota (só temos SP por enquanto).

    O parser de XML (nfeProc) é genérico e cobre qualquer UF — quando a URL
    devolve XML esse erro não acontece.
    """

    def __init__(self, uf: str | None, chave: str | None = None):
        self.uf = uf
        self.chave = chave
        alvo = uf or "desconhecida"
        super().__init__(
            f"UF {alvo} ainda não suportada no parse de HTML "
            f"(chave={chave or '?'}). Suportadas: SP (HTML) e qualquer UF via XML."
        )
