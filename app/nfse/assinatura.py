from __future__ import annotations

from lxml import etree
from signxml import SignatureConstructionMethod, XMLSigner

from app.nfse.certificado import CertificadoA1

C14N = "http://www.w3.org/2001/10/xml-exc-c14n#"
RSA_SHA256 = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
SHA256 = "http://www.w3.org/2001/04/xmlenc#sha256"
DSIG_NS = "http://www.w3.org/2000/09/xmldsig#"
NFSE_NS = "http://www.sped.fazenda.gov.br/nfse"


def assinar_dps(xml_dps: str, certificado: CertificadoA1) -> str:
    """
    Assina o elemento infDPS com XMLDSig enveloped RSA-SHA256.

    A assinatura é inserida como irmão de infDPS, dentro de DPS.
    """
    root = etree.fromstring(xml_dps.encode("utf-8"))
    inf = root.find(f"{{{NFSE_NS}}}infDPS")
    if inf is None:
        raise ValueError("XML da DPS sem elemento infDPS")

    id_attr = inf.get("Id")
    if not id_attr:
        raise ValueError("infDPS sem atributo Id")

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
        reference_uri=f"#{id_attr}",
        id_attribute="Id",
    )

    signature = signed.find(f"{{{DSIG_NS}}}Signature")
    if signature is None:
        raise RuntimeError("Falha ao gerar Signature XMLDSig")

    return etree.tostring(signed, encoding="utf-8", xml_declaration=True).decode("utf-8")
