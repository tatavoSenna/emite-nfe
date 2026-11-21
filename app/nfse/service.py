from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import Settings
from app.nfse.ambientes import resolver_ambiente, tipo_ambiente_codigo
from app.nfse.assinatura import assinar_dps
from app.nfse.certificado import CertificadoA1
from app.nfse.compressao import gunzip_b64
from app.nfse.dps_builder import build_dps_xml
from app.nfse.eventos import montar_pedido_cancelamento
from app.nfse.models import (
    CancelarNfseRequest,
    CancelarNfseResponse,
    ConsultarNfseResponse,
    EmitirNfseRequest,
    EmitirNfseResponse,
)
from app.nfse.sefin_client import SefinClient, SefinError


class NfseService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.ambiente = resolver_ambiente(settings.ambiente)

    def _carregar_certificado(self) -> CertificadoA1:
        if not self.settings.certificado_pfx_path:
            raise FileNotFoundError(
                "Configure CERTIFICADO_PFX_PATH com o caminho do certificado A1 (.pfx)."
            )
        path = Path(self.settings.certificado_pfx_path)
        if not path.exists():
            raise FileNotFoundError(f"Certificado não encontrado: {path}")
        return CertificadoA1.from_pfx(path, self.settings.certificado_senha)

    def emitir(self, request: EmitirNfseRequest) -> EmitirNfseResponse:
        certificado = self._carregar_certificado()
        xml_dps, id_dps = build_dps_xml(
            request,
            ambiente=self.ambiente,
            ver_aplic=self.settings.ver_aplic,
        )
        xml_assinado = assinar_dps(xml_dps, certificado)

        try:
            with SefinClient(
                certificado,
                self.ambiente,
                timeout=self.settings.http_timeout_seconds,
            ) as client:
                data = client.emitir_dps_assinada(xml_assinado)
        except SefinError as exc:
            return EmitirNfseResponse(
                sucesso=False,
                id_dps=id_dps,
                xml_dps=xml_assinado,
                detalhe_erro={"status_http": exc.status_code, "corpo": exc.body},
            )

        xml_nfse = None
        if data.get("nfseXmlGZipB64"):
            xml_nfse = gunzip_b64(data["nfseXmlGZipB64"])

        return EmitirNfseResponse(
            sucesso=True,
            chave_acesso=data.get("chaveAcesso"),
            id_dps=id_dps,
            codigo_status=data.get("codigoStatus"),
            motivo_status=data.get("motivoStatus"),
            data_hora_processamento=data.get("dataHoraProcessamento"),
            xml_nfse=xml_nfse,
            xml_dps=xml_assinado,
        )

    def consultar(self, chave_acesso: str) -> ConsultarNfseResponse:
        certificado = self._carregar_certificado()
        with SefinClient(
            certificado,
            self.ambiente,
            timeout=self.settings.http_timeout_seconds,
        ) as client:
            data = client.consultar_nfse(chave_acesso)

        return ConsultarNfseResponse(
            chave_acesso=chave_acesso,
            xml_nfse=data.get("nfseXml"),
            bruto=data,
        )

    def cancelar(self, chave_acesso: str, request: CancelarNfseRequest) -> CancelarNfseResponse:
        certificado = self._carregar_certificado()
        cnpj = certificado.cnpj_do_titular()
        if not cnpj:
            raise ValueError("Não foi possível obter o CNPJ do certificado para o evento.")

        pedido_b64 = montar_pedido_cancelamento(
            chave_acesso=chave_acesso,
            cnpj_autor=cnpj,
            motivo=request.motivo,
            codigo_motivo=request.codigo_motivo,
            certificado=certificado,
            ver_aplic=self.settings.ver_aplic,
            tp_amb=tipo_ambiente_codigo(self.ambiente),
        )

        try:
            with SefinClient(
                certificado,
                self.ambiente,
                timeout=self.settings.http_timeout_seconds,
            ) as client:
                data = client.registrar_evento(chave_acesso, pedido_b64)
        except SefinError as exc:
            return CancelarNfseResponse(
                sucesso=False,
                chave_acesso=chave_acesso,
                detalhe_erro={"status_http": exc.status_code, "corpo": exc.body},
            )

        return CancelarNfseResponse(sucesso=True, chave_acesso=chave_acesso, bruto=data)

    def preview_dps(self, request: EmitirNfseRequest) -> dict[str, Any]:
        """Gera XML da DPS sem enviar (útil para validar payload)."""
        xml_dps, id_dps = build_dps_xml(
            request,
            ambiente=self.ambiente,
            ver_aplic=self.settings.ver_aplic,
        )
        return {"id_dps": id_dps, "xml_dps": xml_dps, "ambiente": self.ambiente.value}
