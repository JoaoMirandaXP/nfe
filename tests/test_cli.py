"""CLI sem rede: injeta o payload via monkeypatch em `baixar`."""

import json

from nfe import cli
from nfe.fetch import Payload

from .conftest import URL_SP


def _fake_baixar(html):
    def _b(url, *, timeout=30.0):
        return Payload(texto=html, formato="html", content_type="text/html", url_final=url)

    return _b


def test_cli_imprime_json(html_sp, monkeypatch, capsys):
    monkeypatch.setattr(cli, "baixar", _fake_baixar(html_sp))
    rc = cli.main([URL_SP])
    assert rc == 0
    saida = json.loads(capsys.readouterr().out)
    assert saida["chave_acesso"].endswith("6688")
    assert len(saida["itens"]) == 11


def test_cli_bruto(html_sp, monkeypatch, capsys):
    monkeypatch.setattr(cli, "baixar", _fake_baixar(html_sp))
    rc = cli.main(["--bruto", URL_SP])
    assert rc == 0
    assert "tabResult" in capsys.readouterr().out


def test_cli_erro_download(monkeypatch, capsys):
    from nfe.erros import DownloadErro

    def _boom(url, *, timeout=30.0):
        raise DownloadErro("sem rede")

    monkeypatch.setattr(cli, "baixar", _boom)
    rc = cli.main(["http://x"])
    assert rc == 1
    assert "erro:" in capsys.readouterr().err
