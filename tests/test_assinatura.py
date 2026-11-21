from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree
from signxml import XMLVerifier

from app.nfse.ambientes import Ambiente
from app.nfse.assinatura import assinar_dps
from app.nfse.certificado import CertificadoA1
from app.nfse.dps_builder import build_dps_xml
from app.nfse.models import (
    EmitirNfseRequest,
    Endereco,
    Prestador,
    Servico,
    Tomador,
    TributacaoMunicipal,
)


def _certificado_teste() -> CertificadoA1:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Teste"),
            x509.NameAttribute(NameOID.COMMON_NAME, "EMPRESA TESTE:11222333000181"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=30))
        .sign(key, hashes.SHA256())
    )
    return CertificadoA1(private_key=key, certificate=cert, additional_certificates=[])


def test_assinar_dps_sha256_enveloped():
    request = EmitirNfseRequest(
        serie="1",
        numero_dps=10,
        competencia=date(2026, 11, 3),
        data_emissao=datetime(2026, 11, 3, 10, 0, 0, tzinfo=timezone(timedelta(hours=-3))),
        codigo_municipio_emissao="3205200",
        prestador=Prestador(cnpj="11222333000181", razao_social="Prestador"),
        tomador=Tomador(
            cpf="52998224725",
            razao_social="Tomador",
            endereco=Endereco(
                codigo_municipio="3205200",
                cep="29010000",
                logradouro="Rua A",
                numero="1",
                bairro="Centro",
            ),
        ),
        servico=Servico(
            codigo_tributacao_nacional="010301",
            descricao="Servico de teste",
            codigo_municipio_prestacao="3205200",
        ),
        valor_servico=Decimal("100.00"),
        tributacao_municipal=TributacaoMunicipal(aliquota=Decimal("5.00")),
    )
    xml, id_dps = build_dps_xml(request, ambiente=Ambiente.PRODUCAO_RESTRITA, ver_aplic="test")
    cert = _certificado_teste()
    signed = assinar_dps(xml, cert)

    assert "Signature" in signed
    assert "rsa-sha256" in signed
    assert f'URI="#{id_dps}"' in signed

    root = etree.fromstring(signed.encode("utf-8"))
    XMLVerifier().verify(root, x509_cert=cert.certificate)
