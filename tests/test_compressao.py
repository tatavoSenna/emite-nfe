from app.nfse.compressao import gunzip_b64, gzip_b64


def test_roundtrip_gzip_b64():
    original = "<DPS>conteúdo áéíóú</DPS>"
    encoded = gzip_b64(original)
    assert gunzip_b64(encoded) == original
