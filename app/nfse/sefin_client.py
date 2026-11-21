from __future__ import annotations

from typing import Any

import httpx

from app.nfse.ambientes import Ambiente, ENDPOINTS
from app.nfse.certificado import CertificadoA1
from app.nfse.compressao import gunzip_b64, gzip_b64


class SefinError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class SefinClient:
    """Cliente HTTP mTLS para a SEFIN Nacional (emissão/consulta/eventos)."""

    def __init__(
        self,
        certificado: CertificadoA1,
        ambiente: Ambiente,
        *,
        timeout: float = 60.0,
    ) -> None:
        self.certificado = certificado
        self.ambiente = ambiente
        self.endpoints = ENDPOINTS[ambiente]
        self.timeout = timeout
        self._client = httpx.Client(
            verify=certificado.ssl_context(),
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
            },
            http2=False,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SefinClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def emitir_dps_assinada(self, xml_dps_assinada: str) -> dict[str, Any]:
        payload = {"dpsXmlGZipB64": gzip_b64(xml_dps_assinada)}
        url = f"{self.endpoints.sefin}/nfse"
        response = self._client.post(url, json=payload)
        return self._parse_json_response(response, operacao="emissão")

    def consultar_nfse(self, chave_acesso: str) -> dict[str, Any]:
        url = f"{self.endpoints.sefin}/nfse/{chave_acesso}"
        response = self._client.get(url)
        data = self._parse_json_response(response, operacao="consulta")
        if isinstance(data, dict) and data.get("nfseXmlGZipB64"):
            data["nfseXml"] = gunzip_b64(data["nfseXmlGZipB64"])
        return data

    def consultar_por_dps(self, id_dps: str) -> dict[str, Any]:
        # id_dps no path sem o prefixo "DPS" em alguns docs; enviamos o Id completo
        url = f"{self.endpoints.sefin}/dps/{id_dps}"
        response = self._client.get(url)
        return self._parse_json_response(response, operacao="consulta DPS")

    def registrar_evento(self, chave_acesso: str, pedido_xml_gzip_b64: str) -> dict[str, Any]:
        url = f"{self.endpoints.sefin}/nfse/{chave_acesso}/eventos"
        payload = {"pedidoRegistroEventoXmlGZipB64": pedido_xml_gzip_b64}
        response = self._client.post(url, json=payload)
        return self._parse_json_response(response, operacao="evento")

    def _parse_json_response(self, response: httpx.Response, *, operacao: str) -> dict[str, Any]:
        try:
            body: Any = response.json()
        except Exception:
            body = response.text

        if response.status_code >= 400:
            raise SefinError(
                f"SEFIN rejeitou a {operacao} (HTTP {response.status_code})",
                status_code=response.status_code,
                body=body,
            )
        if not isinstance(body, dict):
            raise SefinError(
                f"Resposta inesperada da SEFIN na {operacao}",
                status_code=response.status_code,
                body=body,
            )
        return body
