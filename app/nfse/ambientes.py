from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Ambiente(str, Enum):
    PRODUCAO_RESTRITA = "producao_restrita"
    PRODUCAO = "producao"


@dataclass(frozen=True, slots=True)
class Endpoints:
    sefin: str
    adn_contribuintes: str
    adn_danfse: str
    adn_parametros: str


ENDPOINTS: dict[Ambiente, Endpoints] = {
    Ambiente.PRODUCAO_RESTRITA: Endpoints(
        sefin="https://sefin.producaorestrita.nfse.gov.br/SefinNacional",
        adn_contribuintes="https://adn.producaorestrita.nfse.gov.br/contribuintes",
        adn_danfse="https://adn.producaorestrita.nfse.gov.br/danfse",
        adn_parametros="https://adn.producaorestrita.nfse.gov.br/parametrizacao",
    ),
    Ambiente.PRODUCAO: Endpoints(
        sefin="https://sefin.nfse.gov.br/SefinNacional",
        adn_contribuintes="https://adn.nfse.gov.br/contribuintes",
        adn_danfse="https://adn.nfse.gov.br/danfse",
        adn_parametros="https://adn.nfse.gov.br/parametrizacao",
    ),
}


def tipo_ambiente_codigo(ambiente: Ambiente) -> int:
    """Código tpAmb usado no XML da DPS: 1=produção, 2=homologação."""
    return 1 if ambiente is Ambiente.PRODUCAO else 2


def resolver_ambiente(valor: str) -> Ambiente:
    try:
        return Ambiente(valor)
    except ValueError as exc:
        raise ValueError(
            f"Ambiente inválido: {valor!r}. Use 'producao_restrita' ou 'producao'."
        ) from exc
