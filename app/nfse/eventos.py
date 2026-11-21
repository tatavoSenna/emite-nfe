from __future__ import annotations

from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

from lxml import etree
from signxml import SignatureConstructionMethod, XMLSigner

from app.nfse.assinatura import C14N, RSA_SHA256, SHA256
from app.nfse.certificado import CertificadoA1
from app.nfse.compressao import gzip_b64

NS = "http://www.sped.fazenda.gov.br/nfse"
TZ_BRASILIA = timezone(timedelta(hours=-3))


def montar_pedido_cancelamento(
    *,
    chave_acesso: str,
    cnpj_autor: str,
    motivo: str,
    codigo_motivo: int,
    certificado: CertificadoA1,
    ver_aplic: str,
    tp_amb: int,
) -> str:
    """
    Monta e assina o pedido de registro de evento de cancelamento.

    Retorna o payload já em GZip+Base64 para envio à SEFIN.
    """
    dh = datetime.now(TZ_BRASILIA).isoformat(timespec="seconds")
    id_evento = f"EVT{chave_acesso}101001"

    xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<pedRegEvento xmlns="{NS}" versao="1.00">'
        f'<infPedReg Id="{id_evento}">'
        f"<tpAmb>{int(tp_amb)}</tpAmb>"
        f"<verAplic>{escape(ver_aplic)}</verAplic>"
        f"<dhEvento>{dh}</dhEvento>"
        f"<CNPJAutor>{escape(cnpj_autor)}</CNPJAutor>"
        f"<chNFSe>{escape(chave_acesso)}</chNFSe>"
        f"<e101101>"
        f"<xDesc>Cancelamento de NFS-e</xDesc>"
        f"<cMotivo>{int(codigo_motivo)}</cMotivo>"
        f"<xMotivo>{escape(motivo)}</xMotivo>"
        f"</e101101>"
        f"</infPedReg>"
        f"</pedRegEvento>"
    )

    root = etree.fromstring(xml.encode("utf-8"))
    signer = XMLSigner(
        method=SignatureConstructionMethod.enveloped,
        signature_algorithm=RSA_SHA256,
        digest_algorithm=SHA256,
        c14n_algorithm=C14N,
    )
    signed = signer.sign(
        root,
        key=certificado.private_key,
        cert=[certificado.certificate],
        reference_uri=f"#{id_evento}",
        id_attribute="Id",
    )
    signed_xml = etree.tostring(signed, encoding="utf-8", xml_declaration=True).decode("utf-8")
    return gzip_b64(signed_xml)
