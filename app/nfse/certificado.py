from __future__ import annotations

import ssl
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    pkcs12,
)


@dataclass(slots=True)
class CertificadoA1:
    """Certificado ICP-Brasil A1 (.pfx/.p12) para mTLS e assinatura XMLDSig."""

    private_key: object
    certificate: object
    additional_certificates: list

    @classmethod
    def from_pfx(cls, path: Path | str, password: str) -> CertificadoA1:
        data = Path(path).read_bytes()
        key, cert, extra = pkcs12.load_key_and_certificates(
            data,
            password.encode("utf-8") if password else None,
        )
        if key is None or cert is None:
            raise ValueError("O arquivo PFX não contém chave privada e certificado.")
        return cls(private_key=key, certificate=cert, additional_certificates=extra or [])

    def cnpj_do_titular(self) -> str | None:
        """Extrai CNPJ do subject do certificado, quando disponível."""
        subject = self.certificate.subject.rfc4514_string()
        # Formato comum: CN=RAZAO:11222333000181
        for part in subject.split(","):
            part = part.strip()
            if part.upper().startswith("CN="):
                cn = part[3:]
                if ":" in cn:
                    digits = "".join(ch for ch in cn.split(":")[-1] if ch.isalnum())
                    if len(digits) in (11, 14):
                        return digits
        return None

    def ssl_context(self) -> ssl.SSLContext:
        """Contexto SSL com cliente mTLS (HTTP/1.1 via httpx)."""
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.load_default_certs()

        with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as cert_file:
            cert_file.write(self.certificate.public_bytes(Encoding.PEM))
            for extra in self.additional_certificates:
                cert_file.write(extra.public_bytes(Encoding.PEM))
            cert_path = cert_file.name

        with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as key_file:
            key_file.write(
                self.private_key.private_bytes(
                    Encoding.PEM,
                    PrivateFormat.PKCS8,
                    NoEncryption(),
                )
            )
            key_path = key_file.name

        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        Path(cert_path).unlink(missing_ok=True)
        Path(key_path).unlink(missing_ok=True)
        return ctx
