from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from xml.sax.saxutils import escape

from app.nfse.ambientes import Ambiente, tipo_ambiente_codigo
from app.nfse.dps_id import montar_id_dps
from app.nfse.models import EmitirNfseRequest

NS = "http://www.sped.fazenda.gov.br/nfse"
VERSAO_DPS = "1.00"
TZ_BRASILIA = timezone(timedelta(hours=-3))


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'))}"


def _el(tag: str, text: str | None = None, attrs: dict[str, str] | None = None) -> str:
    attr = "".join(f' {k}="{escape(v, {"\"": "&quot;"})}"' for k, v in (attrs or {}).items())
    if text is None:
        return f"<{tag}{attr}/>"
    return f"<{tag}{attr}>{escape(text)}</{tag}>"


def build_dps_xml(
    request: EmitirNfseRequest,
    *,
    ambiente: Ambiente,
    ver_aplic: str,
) -> tuple[str, str]:
    """Monta o XML da DPS (sem assinatura). Retorna (xml, id_dps)."""
    prestador_doc = request.prestador.cnpj or request.prestador.cpf
    if not prestador_doc:
        raise ValueError("Informe CNPJ ou CPF do prestador")

    id_dps = montar_id_dps(
        codigo_municipio=request.codigo_municipio_emissao,
        cnpj_ou_cpf=prestador_doc,
        serie=request.serie,
        numero_dps=request.numero_dps,
        tipo_inscricao="1" if request.prestador.cnpj else "2",
    )

    dh_emi = request.data_emissao or datetime.now(TZ_BRASILIA)
    if dh_emi.tzinfo is None:
        dh_emi = dh_emi.replace(tzinfo=TZ_BRASILIA)
    # Margem de relógio vs SEFIN (evita rejeição por dhEmi no futuro)
    dh_emi = dh_emi - timedelta(seconds=5)

    parts: list[str] = [
        f'<DPS xmlns="{NS}" versao="{VERSAO_DPS}">',
        f'<infDPS Id="{id_dps}">',
        _el("tpAmb", str(tipo_ambiente_codigo(ambiente))),
        _el("dhEmi", dh_emi.isoformat(timespec="seconds")),
        _el("verAplic", ver_aplic),
        _el("serie", request.serie.zfill(5)[-5:]),
        _el("nDPS", str(request.numero_dps)),
        _el("dCompet", request.competencia.isoformat()),
        _el("tpEmit", str(int(request.tipo_emitente))),
        _el("cLocEmi", request.codigo_municipio_emissao),
    ]

    # Prestador
    parts.append("<prest>")
    if request.prestador.cnpj:
        parts.append(_el("CNPJ", request.prestador.cnpj))
    else:
        parts.append(_el("CPF", request.prestador.cpf))
    if request.prestador.inscricao_municipal:
        parts.append(_el("IM", request.prestador.inscricao_municipal))
    parts.append(_el("xNome", request.prestador.razao_social[:150]))
    if request.prestador.telefone:
        parts.append(_el("fone", request.prestador.telefone))
    if request.prestador.email:
        parts.append(_el("email", request.prestador.email))
    parts.append("<regTrib>")
    parts.append(_el("opSimpNac", str(int(request.prestador.op_simp_nac))))
    if request.prestador.reg_ap_trib_sn:
        parts.append(_el("regApTribSN", request.prestador.reg_ap_trib_sn))
    parts.append(_el("regEspTrib", str(request.prestador.reg_esp_trib)))
    parts.append("</regTrib>")
    parts.append("</prest>")

    # Tomador
    parts.append("<toma>")
    if request.tomador.cnpj:
        parts.append(_el("CNPJ", request.tomador.cnpj))
    elif request.tomador.cpf:
        parts.append(_el("CPF", request.tomador.cpf))
    parts.append(_el("xNome", request.tomador.razao_social[:150]))
    if request.tomador.telefone:
        parts.append(_el("fone", request.tomador.telefone))
    if request.tomador.email:
        parts.append(_el("email", request.tomador.email))
    end = request.tomador.endereco
    parts.append("<end>")
    parts.append("<endNac>")
    parts.append(_el("cMun", end.codigo_municipio))
    parts.append(_el("CEP", end.cep))
    parts.append("</endNac>")
    parts.append(_el("xLgr", end.logradouro[:255]))
    parts.append(_el("nro", end.numero[:60]))
    if end.complemento:
        parts.append(_el("xCpl", end.complemento[:156]))
    parts.append(_el("xBairro", end.bairro[:60]))
    parts.append("</end>")
    parts.append("</toma>")

    # Serviço
    parts.append("<serv>")
    parts.append("<locPrest>")
    parts.append(_el("cLocPrestacao", request.servico.codigo_municipio_prestacao))
    parts.append("</locPrest>")
    parts.append("<cServ>")
    parts.append(_el("cTribNac", request.servico.codigo_tributacao_nacional))
    if request.servico.codigo_tributacao_municipal:
        parts.append(_el("cTribMun", request.servico.codigo_tributacao_municipal))
    parts.append(_el("xDescServ", request.servico.descricao[:2000]))
    parts.append("</cServ>")
    parts.append("</serv>")

    # Valores / tributos
    trib = request.tributacao_municipal
    parts.append("<valores>")
    parts.append("<vServPrest>")
    parts.append(_el("vServ", _money(request.valor_servico)))
    parts.append("</vServPrest>")
    parts.append("<trib>")
    parts.append("<tribMun>")
    parts.append(_el("tribISSQN", str(trib.trib_issqn)))
    parts.append(_el("tpRetISSQN", str(trib.tipo_retencao_issqn)))
    parts.append(_el("pAliq", _money(trib.aliquota)))
    parts.append("</tribMun>")
    parts.append("<totTrib>")
    parts.append(_el("indTotTrib", "0"))
    parts.append("</totTrib>")
    parts.append("</trib>")
    parts.append("</valores>")

    parts.append("</infDPS>")
    parts.append("</DPS>")

    xml = '<?xml version="1.0" encoding="UTF-8"?>' + "".join(parts)
    return xml, id_dps
