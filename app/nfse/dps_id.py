from __future__ import annotations


def montar_id_dps(
    *,
    codigo_municipio: str,
    cnpj_ou_cpf: str,
    serie: str,
    numero_dps: int,
    tipo_inscricao: str | None = None,
) -> str:
    """
    Id da DPS: DPS + cMun(7) + tpInsc(1) + inscrição(14) + série(5) + nDPS(15).

    tpInsc: 1=CNPJ, 2=CPF. CPF é preenchido com zeros à esquerda até 14.
    """
    doc = "".join(ch for ch in cnpj_ou_cpf if ch.isalnum())
    if tipo_inscricao is None:
        tipo_inscricao = "1" if len(doc) == 14 else "2"

    if tipo_inscricao == "2":
        doc = doc.zfill(14)
    elif len(doc) != 14:
        raise ValueError("CNPJ do prestador deve ter 14 caracteres")

    cmun = "".join(ch for ch in codigo_municipio if ch.isdigit()).zfill(7)[-7:]
    serie_pad = "".join(ch for ch in serie if ch.isdigit()).zfill(5)[-5:]
    numero_pad = str(numero_dps).zfill(15)[-15:]

    return f"DPS{cmun}{tipo_inscricao}{doc}{serie_pad}{numero_pad}"
