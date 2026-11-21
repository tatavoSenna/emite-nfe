from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="API NFS-e Nacional",
        description=(
            "API para emissão, consulta e cancelamento de Notas Fiscais de Serviço "
            "eletrônicas no Sistema Nacional (SEFIN Nacional / ADN)."
        ),
        version=settings.app_version,
    )
    app.include_router(router, prefix="/v1")
    return app


app = create_app()
