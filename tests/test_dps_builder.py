from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.nfse.ambientes import Ambiente
from app.nfse.dps_builder import build_dps_xml
from app.nfse.models import (
    EmitirNfseRequest,
    Endereco,
    Prestador,
    Servico,
    Tomador,
    TributacaoMunicipal,
)


def _request() -> EmitirNfseRequest:
    return EmitirNfseRequest(
        serie="900",
        numero_dps=1,
        competencia=date(2026, 11, 3),
        data_emissao=datetime(2026, 11, 3, 12, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
        codigo_municipio_emissao="3550308",
        prestador=Prestador(
            cnpj="11222333000181",
            inscricao_municipal="12345",
            razao_social="Empresa Prestadora LTDA",
            op_simp_nac=3,
            reg_ap_trib_sn="1",
        ),
        tomador=Tomador(
            cnpj="99999999000191",
            razao_social="Tomador Teste LTDA",
            endereco=Endereco(
                codigo_municipio="3550308",
                cep="01310100",
                logradouro="Av Paulista",
                numero="1000",
                bairro="Bela Vista",
            ),
        ),
        servico=Servico(
            codigo_tributacao_nacional="010301",
            descricao="Consultoria em desenvolvimento de software",
            codigo_municipio_prestacao="3550308",
        ),
        valor_servico=Decimal("1500.00"),
        tributacao_municipal=TributacaoMunicipal(aliquota=Decimal("2.50")),
    )


def test_build_dps_contem_id_e_ordem_basica():
    xml, id_dps = build_dps_xml(
        _request(),
        ambiente=Ambiente.PRODUCAO_RESTRITA,
        ver_aplic="test_0.1.0",
    )
    assert id_dps.startswith("DPS3550308")
    assert f'Id="{id_dps}"' in xml
    assert 'xmlns="http://www.sped.fazenda.gov.br/nfse"' in xml
    assert "<tpAmb>2</tpAmb>" in xml
    assert "<CNPJ>11222333000181</CNPJ>" in xml
    assert "<vServ>1500.00</vServ>" in xml
    assert xml.index("<prest>") < xml.index("<toma>") < xml.index("<serv>") < xml.index("<valores>")
