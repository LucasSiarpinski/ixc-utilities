"""Módulo: criação em lote de clientes e contratos via webservice."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from flask import Blueprint, render_template, request, session

from api_client import extract_id, post_json

bp = Blueprint("lote", __name__)

APP_DIR = Path(__file__).resolve().parent.parent
FIXTURES = APP_DIR / "fixtures"
SESSION_LOTE_FORM = "lote_form"

# Códigos enviados em status (tabela cliente_contrato).
ALLOWED_STATUS_CONTRATO: frozenset[str] = frozenset({"A", "I", "P", "N", "S"})

# Opções para renderizar no HTML (código, descrição)
STATUS_CONTRATO_OPTIONS: tuple[tuple[str, str], ...] = (
    ("A", "Ativo"),
    ("I", "Inativo"),
    ("P", "Pré-contrato"),
    ("N", "Negativado"),
    ("S", "Suspenso"),
)

def _coerce_status_contrato(value: str | None) -> str | None:
    """Converte entrada em código permitido para o status do contrato, ou None se inválido."""
    if value is None:
        return None
    s = str(value).strip().upper()
    if s in ALLOWED_STATUS_CONTRATO:
        return s
    return None


def _resolve_status_contrato(form_value: str, template_value: str | None) -> str:
    """Valor efetivo para o JSON do contrato: só códigos A, I, P, N, S."""
    for candidate in (form_value, template_value or "", "A"):
        code = _coerce_status_contrato(candidate)
        if code:
            return code
    return "A"

# Códigos enviados em status_internet (webservice IXC).
ALLOWED_STATUS_INTERNET: frozenset[str] = frozenset({"A", "D", "CM", "CA", "CE", "FA", "AA"})

# (código, descrição) — o valor do POST e do JSON deve ser o código (ex.: AA, A).
STATUS_INTERNET_OPTIONS: tuple[tuple[str, str], ...] = (
    ("AA", "Aguardando assinatura"),
    ("A", "Ativo"),
    ("D", "Desativado"),
    ("CM", "Bloqueio manual"),
    ("CA", "Bloqueio automático"),
    ("CE", "CE (definição no sistema — confirmar na sua base)"),
    ("FA", "Financeiro em atraso"),
)

# Compatibilidade com formulário/sessão antigos que usavam texto em vez de código.
_LEGACY_STATUS_INTERNET: dict[str, str] = {
    "aguardando assinatura": "AA",
    "ativo": "A",
    "desativado": "D",
}


def _coerce_status_internet(value: str | None) -> str | None:
    """Converte entrada (código ou texto legado) em código permitido, ou None se inválido."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    key = s.upper()
    if key in ALLOWED_STATUS_INTERNET:
        return key
    legacy = _LEGACY_STATUS_INTERNET.get(s.strip().lower())
    if legacy and legacy in ALLOWED_STATUS_INTERNET:
        return legacy
    return None


def _resolve_status_internet(form_value: str, template_value: str | None) -> str:
    """Valor efetivo para o JSON do contrato: só códigos A, D, CM, CA, CE, FA, AA."""
    for candidate in (form_value, template_value or "", "AA"):
        code = _coerce_status_internet(candidate)
        if code:
            return code
    return "AA"


LOTE_FORM_DEFAULTS: dict = {
    "base_url": "",
    "username": "",
    "password": "",
    "verify_ssl": True,
    "quantidade": "3",
    "contratos_por_cliente": "1",
    "padding": "4",
    "razao_prefix": "Cliente",
    "contrato_prefix": "Plano Teste",
    "cnpj_cpf": "175.181.720-20",
    "cep": "83215-210",
    "endereco": "Rua Teste",
    "numero": "1200",
    "bairro": "Teste",
    "cidade": "1",
    "tipo_pessoa": "F",
    "contribuinte_icms": "I",
    "tipo_assinante": "1",
    "tipo_localidade": "U",
    "iss_classificacao_padrao": "00",
    "cob_envia_email": "",
    "cob_envia_sms": "",
    "c_tipo": "I",
    "id_vd_contrato": "1",
    "id_tipo_contrato": "10",
    "id_modelo": "1",
    "id_filial": "1",
    "data_contrato": "18/06/2024",
    "id_tipo_documento": "501",
    "id_carteira_cobranca": "1",
    "id_vendedor": "1",
    "cc_previsao": "M",
    "tipo_cobranca": "P",
    "renovacao_automatica": "S",
    "base_geracao_tipo_doc": "P",
    "bloqueio_automatico": "S",
    "aviso_atraso": "S",
    "endereco_padrao_cliente": "S",
    "status_internet": "AA",
    "status": "A",
}


def _load_json(name: str) -> dict:
    path = FIXTURES / name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _verify_ssl_from_form() -> bool:
    values = request.form.getlist("verify_ssl")
    if not values:
        return True
    return values[0] in ("1", "on", "true", "True", "yes", "S", "s")


def _as_int(name: str, default: int) -> int:
    try:
        return int(request.form.get(name, "").strip() or default)
    except ValueError:
        return default


def _snapshot_lote_form() -> dict:
    """Serializa o POST atual para guardar na sessão (reabrir formulário)."""
    data = {k: v for k, v in LOTE_FORM_DEFAULTS.items()}
    for key in LOTE_FORM_DEFAULTS:
        if key == "verify_ssl":
            data["verify_ssl"] = _verify_ssl_from_form()
            continue
        if key not in request.form:
            continue
        raw = request.form.get(key, "")
        if key == "password":
            data[key] = raw if isinstance(raw, str) else str(raw)
        elif isinstance(raw, str):
            data[key] = raw.strip()
        else:
            data[key] = str(raw)
    return data


def _merge_prefill() -> dict:
    saved = session.get(SESSION_LOTE_FORM)
    if not isinstance(saved, dict):
        saved = {}
    out = {**LOTE_FORM_DEFAULTS, **saved}
    if "verify_ssl" not in saved:
        out["verify_ssl"] = LOTE_FORM_DEFAULTS["verify_ssl"]
    
    raw_si = out.get("status_internet")
    coerced_si = _coerce_status_internet("" if raw_si is None else str(raw_si))
    out["status_internet"] = coerced_si or LOTE_FORM_DEFAULTS["status_internet"]
    
    raw_s = out.get("status")
    coerced_s = _coerce_status_contrato("" if raw_s is None else str(raw_s))
    out["status"] = coerced_s or LOTE_FORM_DEFAULTS["status"]
    
    return out


def _run_batch() -> list[dict]:
    base_url = (request.form.get("base_url") or "").strip()
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    verify_ssl = _verify_ssl_from_form()

    n = max(1, min(_as_int("quantidade", 1), 500))
    por_cliente = max(1, min(_as_int("contratos_por_cliente", 1), 500))
    pad = max(1, min(_as_int("padding", 4), 8))
    razao_prefix = (request.form.get("razao_prefix") or "Cliente").strip() or "Cliente"
    contrato_prefix = (request.form.get("contrato_prefix") or "Plano Teste").strip() or "Plano Teste"

    cliente_base = _load_json("cliente_template.json")
    contrato_base = _load_json("contrato_template.json")

    cliente_overrides = {
        "cnpj_cpf": (request.form.get("cnpj_cpf") or "").strip(),
        "cep": (request.form.get("cep") or "").strip(),
        "endereco": (request.form.get("endereco") or "").strip(),
        "numero": (request.form.get("numero") or "").strip(),
        "bairro": (request.form.get("bairro") or "").strip(),
        "cidade": (request.form.get("cidade") or "").strip(),
        "tipo_pessoa": (request.form.get("tipo_pessoa") or "F").strip(),
        "contribuinte_icms": (request.form.get("contribuinte_icms") or "I").strip(),
        "tipo_assinante": (request.form.get("tipo_assinante") or "1").strip(),
        "tipo_localidade": (request.form.get("tipo_localidade") or "U").strip(),
        "iss_classificacao_padrao": (request.form.get("iss_classificacao_padrao") or "00").strip(),
        "cob_envia_email": (request.form.get("cob_envia_email") or "").strip(),
        "cob_envia_sms": (request.form.get("cob_envia_sms") or "").strip(),
    }

    form_si = (request.form.get("status_internet") or "").strip()
    tpl_si = contrato_base.get("status_internet")
    status_internet = _resolve_status_internet(form_si, str(tpl_si) if tpl_si is not None else "")

    form_s = (request.form.get("status") or "").strip()
    tpl_s = contrato_base.get("status")
    status_contrato = _resolve_status_contrato(form_s, str(tpl_s) if tpl_s is not None else "")

    contrato_overrides = {
        "tipo": (request.form.get("c_tipo") or "I").strip(),
        "id_vd_contrato": (request.form.get("id_vd_contrato") or "1").strip(),
        "id_tipo_contrato": (request.form.get("id_tipo_contrato") or "10").strip(),
        "id_modelo": (request.form.get("id_modelo") or "1").strip(),
        "id_filial": (request.form.get("id_filial") or "1").strip(),
        "data": (request.form.get("data_contrato") or "").strip(),
        "id_tipo_documento": (request.form.get("id_tipo_documento") or "502").strip(),
        "id_carteira_cobranca": (request.form.get("id_carteira_cobranca") or "1").strip(),
        "id_vendedor": (request.form.get("id_vendedor") or "1").strip(),
        "cc_previsao": (request.form.get("cc_previsao") or "M").strip(),
        "tipo_cobranca": (request.form.get("tipo_cobranca") or "P").strip(),
        "renovacao_automatica": (request.form.get("renovacao_automatica") or "S").strip(),
        "base_geracao_tipo_doc": (request.form.get("base_geracao_tipo_doc") or "P").strip(),
        "bloqueio_automatico": (request.form.get("bloqueio_automatico") or "S").strip(),
        "aviso_atraso": (request.form.get("aviso_atraso") or "S").strip(),
        "endereco_padrao_cliente": (request.form.get("endereco_padrao_cliente") or "S").strip(),
        "status_internet": status_internet,
        "status": status_contrato,
        "agrupar_financeiro_contrato": (request.form.get("agrupar_financeiro_contrato") or "S").strip(),
        "contrato_suspenso": (request.form.get("contrato_suspenso") or "N").strip(),
    }

    rows: list[dict] = []

    for i in range(1, n + 1):
        suffix = str(i).zfill(pad)
        cli = copy.deepcopy(cliente_base)
        cli.update({k: v for k, v in cliente_overrides.items() if v})
        cli["razao"] = f"{razao_prefix} {suffix}"

        res_cli = post_json(
            base_url,
            "/webservice/v1/cliente",
            cli,
            username,
            password,
            verify_ssl=verify_ssl,
        )
        cid = extract_id(res_cli)
        row_base = {
            "indice": i,
            "razao": cli["razao"],
            "cliente_ok": res_cli.ok,
            "cliente_id": cid,
            "cliente_msg": res_cli.message,
            "cliente_http": res_cli.status_code,
            "contratos": [],
        }

        if not res_cli.ok or not cid:
            rows.append(row_base)
            continue

        for j in range(1, por_cliente + 1):
            ctr = copy.deepcopy(contrato_base)
            ctr.update(contrato_overrides)
            ctr["id_cliente"] = cid
            if por_cliente > 1:
                ctr["contrato"] = f"{contrato_prefix} {suffix}-{j}"
            else:
                ctr["contrato"] = f"{contrato_prefix} {suffix}"

            res_ctr = post_json(
                base_url,
                "/webservice/v1/cliente_contrato",
                ctr,
                username,
                password,
                verify_ssl=verify_ssl,
            )
            
            ctrid = extract_id(res_ctr)

            # Executa a rotina nativa de ativação do IXC caso o usuário queira o contrato Ativo
            if res_ctr.ok and ctrid and status_contrato == "A":
                try:
                    # Enviando exatamente o formato que funcionou no seu Postman!
                    resposta_bruta = post_json(
                        base_url=base_url,
                        path="/webservice/v1/cliente_contrato_ativar_cliente",
                        payload={"id_contrato": ctrid},  # <--- CHAVE EXATA DO POSTMAN
                        username=username,
                        password=password,
                        verify_ssl=verify_ssl,
                        method="POST"
                    )
                    
                    print("\n" + "="*50)
                    print(f"SUCESSO NA ATIVAÇÃO - CONTRATO ID: {ctrid}")
                    print(f"HTTP Status: {resposta_bruta.status_code}")
                    print(f"Mensagem IXC: {resposta_bruta.message}")
                    print("="*50 + "\n")

                except Exception as erro_python:
                    print(f"Aviso: Falha ao disparar gatilho de ativação para o contrato {ctrid}: {erro_python}")

            row_base["contratos"].append(
                {
                    "seq": j,
                    "ok": res_ctr.ok,
                    "id": ctrid,
                    "msg": res_ctr.message,
                    "http": res_ctr.status_code,
                }
            )
            if not res_ctr.ok:
                break

        rows.append(row_base)

    return rows


def _render_lote_index(erro: str | None = None):
    return render_template(
        "lote/index.html",
        prefill=_merge_prefill(),
        erro=erro,
        status_internet_options=STATUS_INTERNET_OPTIONS,
        status_contrato_options=STATUS_CONTRATO_OPTIONS, 
    )


@bp.get("/")
def index():
    return _render_lote_index(None)


@bp.post("/executar")
def executar():
    session[SESSION_LOTE_FORM] = _snapshot_lote_form()

    if not request.form.get("base_url", "").strip():
        return _render_lote_index("Informe a base URL (ex.: https://seudominio.com.br)."), 400
    if not request.form.get("username", "").strip():
        return _render_lote_index("Informe o usuário (Basic Auth)."), 400

    try:
        linhas = _run_batch()
    except FileNotFoundError as e:
        return _render_lote_index(f"Arquivo de template ausente: {e}"), 500
    except json.JSONDecodeError as e:
        return _render_lote_index(f"JSON inválido nos fixtures: {e}"), 500

    return render_template(
        "lote/resultado.html",
        linhas=linhas,
        base_url=request.form.get("base_url", "").strip(),
    )