from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.nfse.ambientes import ENDPOINTS
from app.nfse.models import (
    CancelarNfseRequest,
    CancelarNfseResponse,
    ConsultarNfseResponse,
    EmitirNfseRequest,
    EmitirNfseResponse,
)
from app.nfse.sefin_client import SefinError
from app.nfse.service import NfseService

router = APIRouter()


def get_service(settings: Settings = Depends(get_settings)) -> NfseService:
    return NfseService(settings)


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    ambiente = settings.ambiente
    try:
        from app.nfse.ambientes import resolver_ambiente

        endpoints = ENDPOINTS[resolver_ambiente(ambiente)]
        sefin = endpoints.sefin
    except ValueError:
        sefin = None
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "ambiente": ambiente,
        "sefin": sefin,
    }


@router.post("/nfse/preview-dps")
def preview_dps(
    body: EmitirNfseRequest,
    service: NfseService = Depends(get_service),
) -> dict:
    """Monta o XML da DPS sem assinar/enviar — útil para conferência."""
    return service.preview_dps(body)


@router.post("/nfse", response_model=EmitirNfseResponse)
def emitir_nfse(
    body: EmitirNfseRequest,
    service: NfseService = Depends(get_service),
) -> EmitirNfseResponse:
    """
    Emite NFS-e no Sistema Nacional.

    Fluxo: monta DPS → assina (XMLDSig SHA-256) → GZip+Base64 → POST SEFIN /nfse.
    """
    try:
        result = service.emitir(body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Falha na emissão: {exc}") from exc

    if not result.sucesso:
        raise HTTPException(status_code=422, detail=result.model_dump())
    return result


@router.get("/nfse/{chave_acesso}", response_model=ConsultarNfseResponse)
def consultar_nfse(
    chave_acesso: str,
    service: NfseService = Depends(get_service),
) -> ConsultarNfseResponse:
    try:
        return service.consultar(chave_acesso)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SefinError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail={"mensagem": str(exc), "corpo": exc.body},
        ) from exc


@router.post("/nfse/{chave_acesso}/cancelar", response_model=CancelarNfseResponse)
def cancelar_nfse(
    chave_acesso: str,
    body: CancelarNfseRequest,
    service: NfseService = Depends(get_service),
) -> CancelarNfseResponse:
    try:
        result = service.cancelar(chave_acesso, body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not result.sucesso:
        raise HTTPException(status_code=422, detail=result.model_dump())
    return result
