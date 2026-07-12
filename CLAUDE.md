# nfe

Leia o README.md. Projeto uv **independente**, publicado em
`JoaoMirandaXP/nfe` (remote SSH `github-jmxp`). Vive em `worktree/nfe/` dentro
do repo notas-fiscais (irmão de `notas_fiscais/` e `analise/`). Faz: url de
NFC-e/NF-e → `Nota` estruturada (JSON) → opcionalmente grava no Supabase.
Receber a URL pela sala do Matrix é etapa posterior.

- Python com `uv` (`uv sync`, `uv run pytest`, `uv run nfe <url>`).
- **Repo PÚBLICO**: nenhum segredo aqui. Credenciais ficam em `control/nfe.env`
  (fora do repo), lidas via `NFE_DB_URL`/`NFE_ENV` — ver [[nfe-repo-identidade]].
- Persistência = extra `db` (psycopg): `nfe/db.py` (`salvar`, `migrar`) +
  `migrations/0001_notas.sql` (idempotente, no-op no banco `financeiro`).
  Reusa `comerciantes`/`notas`/`itens`; sem produtos/LLM. Idempotência por
  `notas.chave_acesso` (upsert). O núcleo do parser NÃO importa `db`/psycopg.
- Parse ancorado em **dado real**, não em fixture inventada: HTML de SP em
  `tests/fixtures/sp_nfce.html`, XSD do leiaute NFe v4.00 em
  `../../control/assets/PL_010e_v1.02/`. Ao mexer no parser, valide contra
  esses (ou baixe uma nota nova) — ver [[nfe-parse-com-schema-real]].
- Camadas: `fetch` (baixa + detecta html/xml) · `chave` (decodifica os 44
  dígitos) · `parse/` (dispatcher → `sp` HTML | `xml_nfe`) · `modelos` (`Nota`).
- Nova UF de HTML = registrar em `parse/__init__.py::_HTML_PARSERS`.
- Dinheiro é `Decimal` internamente; `para_dict()` serializa para JSON.
