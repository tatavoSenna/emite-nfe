from app.nfse.dps_id import montar_id_dps


def test_id_dps_cnpj_padding():
    id_dps = montar_id_dps(
        codigo_municipio="3550308",
        cnpj_ou_cpf="11222333000181",
        serie="900",
        numero_dps=1,
    )
    assert id_dps.startswith("DPS")
    assert len(id_dps) == 45  # DPS + 42 dígitos
    assert id_dps == "DPS355030811122233300018100900000000000000001"


def test_id_dps_cpf_zfill():
    id_dps = montar_id_dps(
        codigo_municipio="3205200",
        cnpj_ou_cpf="52998224725",
        serie="1",
        numero_dps=42,
        tipo_inscricao="2",
    )
    assert id_dps[10] == "2"  # tpInsc
    assert "00052998224725" in id_dps
