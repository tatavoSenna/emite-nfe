from __future__ import annotations

import base64
import gzip


def gzip_b64(conteudo: str | bytes) -> str:
    raw = conteudo.encode("utf-8") if isinstance(conteudo, str) else conteudo
    return base64.b64encode(gzip.compress(raw)).decode("ascii")


def gunzip_b64(payload: str) -> str:
    return gzip.decompress(base64.b64decode(payload)).decode("utf-8")
