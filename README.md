# nfe

De uma **URL de nota fiscal eletrônica** (o link do QR code da NFC-e) para
**JSON estruturado**, pronto para persistir.

```
url  →  baixar (html | xml)  →  parse  →  Nota  →  JSON
```

Projeto deliberadamente pequeno e desacoplado: só transforma a URL na nota.
Gravar no Supabase e receber a URL pela sala do Matrix são **etapas
seguintes** — este pacote não conhece banco nem chat.

## Uso

```bash
uv sync
uv run nfe "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=3526...|2|1|1|0A84..."
uv run nfe --bruto <url>      # imprime o html/xml cru, para inspeção
```

Como biblioteca:

```python
from nfe import consultar
nota = consultar(url)          # baixa + parseia
dados = nota.para_dict()       # dict JSON-serializável
```

## Saída

```json
{
  "chave_acesso": "35260404742665000121650070000512761566966688",
  "uf": "SP",
  "modelo": "65",
  "serie": "7",
  "numero": "51276",
  "emitente": { "cnpj": "04.742.665/0001-21", "nome": "Mercado Violeta Ltda EPP" },
  "emitida_em": "2026-04-26T20:58:08-03:00",
  "total": 105.56,
  "itens": [
    { "seq": 1, "codigo": "893", "descricao": "MACA GALA KG",
      "quantidade": 0.85, "unidade": "kg", "valor_unitario": 9.98, "valor_total": 8.48 }
  ],
  "url": "...",
  "formato": "html"
}
```

## Como parseia

- **Chave de acesso** (`chave.py`): os 44 dígitos já dão UF, CNPJ, modelo,
  série e número — e validam o dígito verificador (mod 11). É o que escolhe
  o parser e preenche o cabeçalho mesmo quando o HTML é irregular.
- **HTML por UF** (`parse/sp.py`): hoje só **SP** (`ConsultaQRCode.aspx`,
  tabela `#tabResult`). Registrar outra UF é adicionar uma função em
  `parse/__init__.py::_HTML_PARSERS`.
- **XML nacional** (`parse/xml_nfe.py`): leiaute **NFe v4.00** (pacote
  `PL_010e`), vale para qualquer UF. Usado quando a URL devolve XML.

## Testes

```bash
uv run pytest
```

Os testes usam uma nota **real** de SP (`tests/fixtures/sp_nfce.html`) e um
XML v4.00 (`tests/fixtures/nfce_v4.xml`); não tocam a rede.

## Escopo / próximas etapas

1. **(feito)** url → parse → JSON.
2. Persistência no Supabase (schema a definir).
3. Receber a URL direto da sala do Matrix.
