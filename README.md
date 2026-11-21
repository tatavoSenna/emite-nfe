# emite-nfse

API REST para emissão de **NFS-e (Nota Fiscal de Serviço eletrônica)** no **Sistema Nacional** do governo federal (SEFIN Nacional / ADN).

> Escopo: apenas notas de **serviço**. Não emite NF-e/NFC-e de mercadorias.

## Como funciona o sistema oficial

| Item | Detalhe |
|---|---|
| Portal | [gov.br/nfse](https://www.gov.br/nfse/pt-br) |
| Emissão | API REST da **SEFIN Nacional** |
| Homologação | `https://sefin.producaorestrita.nfse.gov.br/SefinNacional` |
| Produção | `https://sefin.nfse.gov.br/SefinNacional` |
| Autenticação | **mTLS** com certificado digital **ICP-Brasil A1** (.pfx) |
| Documento enviado | **DPS** (Declaração de Prestação de Serviço) em XML assinado |
| Payload | XML → GZip → Base64 no campo `dpsXmlGZipB64` |

Documentação oficial das APIs:  
https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao

## Fluxo desta API

```
Cliente → POST /v1/nfse (JSON)
       → monta XML da DPS
       → assina XMLDSig (RSA-SHA256)
       → compacta GZip + Base64
       → POST SEFIN /nfse (mTLS)
       → retorna chave de acesso + XML da NFS-e
```

## Pré-requisitos

1. Certificado digital **A1** (.pfx) do CNPJ emitente (ou procurador)
2. Município **aderente** ao Sistema Nacional da NFS-e
3. Contribuinte habilitado no Painel do Contribuinte / Emissor Nacional
4. Python **3.11+**

## Configuração

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# edite .env com o caminho/senha do certificado
```

Variáveis principais (`.env`):

- `AMBIENTE` — `producao_restrita` (padrão) ou `producao`
- `CERTIFICADO_PFX_PATH` — caminho do `.pfx`
- `CERTIFICADO_SENHA` — senha do certificado

## Executar

```bash
uvicorn app.main:app --reload --port 8000
```

Docs interativas: http://localhost:8000/docs

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/health` | Saúde e ambiente configurado |
| `POST` | `/v1/nfse/preview-dps` | Gera XML da DPS **sem** enviar |
| `POST` | `/v1/nfse` | Emite NFS-e na SEFIN |
| `GET` | `/v1/nfse/{chave}` | Consulta NFS-e pela chave |
| `POST` | `/v1/nfse/{chave}/cancelar` | Cancela NFS-e (evento) |

### Exemplo de emissão

```bash
curl -s http://localhost:8000/v1/nfse \
  -H 'Content-Type: application/json' \
  -d '{
    "serie": "900",
    "numero_dps": 1,
    "competencia": "2026-11-21",
    "codigo_municipio_emissao": "3550308",
    "prestador": {
      "cnpj": "11222333000181",
      "inscricao_municipal": "12345",
      "razao_social": "Empresa Prestadora LTDA",
      "op_simp_nac": 3,
      "reg_ap_trib_sn": "1"
    },
    "tomador": {
      "cnpj": "99999999000191",
      "razao_social": "Cliente LTDA",
      "endereco": {
        "codigo_municipio": "3550308",
        "cep": "01310100",
        "logradouro": "Av Paulista",
        "numero": "1000",
        "bairro": "Bela Vista"
      }
    },
    "servico": {
      "codigo_tributacao_nacional": "010301",
      "descricao": "Consultoria em software",
      "codigo_municipio_prestacao": "3550308"
    },
    "valor_servico": "1500.00",
    "tributacao_municipal": {
      "trib_issqn": 1,
      "tipo_retencao_issqn": 2,
      "aliquota": "2.50"
    }
  }'
```

## Testes

```bash
pytest -q
```

Os testes cobrem geração do Id da DPS, montagem do XML, compressão e assinatura digital (com certificado autoassinado). **Não** chamam a SEFIN de verdade — para isso é necessário um `.pfx` válido e município habilitado.

## Observações importantes

- A **numeração da DPS** (`serie` + `numero_dps`) é responsabilidade do emitente; use contador atômico por CNPJ/série.
- Apps próprios devem usar série entre **1 e 49999**.
- Sempre teste em **produção restrita** antes de ir para produção.
- Cada emissão em produção gera documento fiscal com validade jurídica.
- O leiaute completo e as regras de negócio estão nos manuais/anexos do portal gov.br/nfse (incluindo IBS/CBS conforme notas técnicas vigentes).
