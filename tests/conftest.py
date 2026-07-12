from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# URL real correspondente à fixture sp_nfce.html (nota da SEFAZ-SP).
URL_SP = (
    "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/"
    "ConsultaQRCode.aspx?p=35260404742665000121650070000512761566966688|2|1|1|"
    "0A8416C7CAA8E6FBFB365368B1EB93845FBC543C"
)
CHAVE_SP = "35260404742665000121650070000512761566966688"


@pytest.fixture
def html_sp() -> str:
    return (FIXTURES / "sp_nfce.html").read_text(encoding="utf-8")


@pytest.fixture
def xml_nfce() -> str:
    return (FIXTURES / "nfce_v4.xml").read_text(encoding="utf-8")
