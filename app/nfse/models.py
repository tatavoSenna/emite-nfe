from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class OpSimpNac(IntEnum):
    NAO_OPTANTE = 1
    MEI = 2
    ME_EPP = 3


class TipoEmitente(IntEnum):
    PRESTADOR = 1
    TOMADOR = 2
    INTERMEDIARIO = 3


class Endereco(BaseModel):
    codigo_municipio: str = Field(..., min_length=7, max_length=7, description="Código IBGE")
    cep: str = Field(..., min_length=8, max_length=8)
    logradouro: str
    numero: str
    bairro: str
    complemento: str | None = None
    uf: str | None = Field(default=None, min_length=2, max_length=2)

    @field_validator("cep", "codigo_municipio")
    @classmethod
    def so_digitos(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        return digits


class Prestador(BaseModel):
    cnpj: str | None = None
    cpf: str | None = None
    inscricao_municipal: str | None = None
    razao_social: str
    telefone: str | None = None
    email: str | None = None
    op_simp_nac: OpSimpNac = OpSimpNac.NAO_OPTANTE
    reg_ap_trib_sn: str | None = Field(default=None, description="Obrigatório se optante do SN")
    reg_esp_trib: int = 0

    @field_validator("cnpj", "cpf")
    @classmethod
    def limpar_documento(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return "".join(ch for ch in value if ch.isdigit())


class Tomador(BaseModel):
    cnpj: str | None = None
    cpf: str | None = None
    razao_social: str
    email: str | None = None
    telefone: str | None = None
    endereco: Endereco

    @field_validator("cnpj", "cpf")
    @classmethod
    def limpar_documento(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return "".join(ch for ch in value if ch.isdigit())


class Servico(BaseModel):
    codigo_tributacao_nacional: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="cTribNac (6 dígitos, lista nacional)",
    )
    codigo_tributacao_municipal: str | None = None
    descricao: str = Field(..., min_length=1, max_length=2000)
    codigo_municipio_prestacao: str = Field(..., min_length=7, max_length=7)


class TributacaoMunicipal(BaseModel):
    trib_issqn: Literal[1, 2, 3, 4] = Field(
        1,
        description="1=Operação tributável, 2=Imunidade, 3=Exportação, 4=Não incidência",
    )
    tipo_retencao_issqn: Literal[1, 2, 3] = Field(
        2,
        description="1=Retido pelo tomador, 2=Não retido, 3=Retido pelo intermediário",
    )
    aliquota: Decimal = Field(..., ge=0, le=100)


class EmitirNfseRequest(BaseModel):
    serie: str = Field(..., description="Série da DPS (1 a 5 dígitos; apps próprios usam 1-49999)")
    numero_dps: int = Field(..., gt=0, description="Número sequencial da DPS")
    competencia: date
    data_emissao: datetime | None = None
    codigo_municipio_emissao: str = Field(..., min_length=7, max_length=7)
    tipo_emitente: TipoEmitente = TipoEmitente.PRESTADOR
    prestador: Prestador
    tomador: Tomador
    servico: Servico
    valor_servico: Decimal = Field(..., gt=0)
    tributacao_municipal: TributacaoMunicipal

    @field_validator("serie")
    @classmethod
    def serie_numerica(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if not digits:
            raise ValueError("série deve ser numérica")
        return digits


class EmitirNfseResponse(BaseModel):
    sucesso: bool
    chave_acesso: str | None = None
    id_dps: str | None = None
    codigo_status: int | None = None
    motivo_status: str | None = None
    data_hora_processamento: str | None = None
    xml_nfse: str | None = None
    xml_dps: str | None = None
    detalhe_erro: dict | list | str | None = None


class ConsultarNfseResponse(BaseModel):
    chave_acesso: str
    xml_nfse: str | None = None
    bruto: dict | list | str | None = None


class CancelarNfseRequest(BaseModel):
    motivo: str = Field(..., min_length=15, max_length=255)
    codigo_motivo: Literal[1, 2, 9] = Field(
        1,
        description="1=Erro na emissão, 2=Serviço não prestado, 9=Outros",
    )


class CancelarNfseResponse(BaseModel):
    sucesso: bool
    chave_acesso: str
    bruto: dict | list | str | None = None
    detalhe_erro: dict | list | str | None = None
