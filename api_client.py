"""Chamadas HTTP ao webservice (cliente → contrato)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests
import urllib3


@dataclass
class ApiResult:
    ok: bool
    status_code: int | None
    message: str
    raw: dict[str, Any] | str | None = None


def _truthy_id(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _pick_id_from_dict(d: dict[str, Any]) -> Any:
    for key in ("id", "id_cliente"):
        v = d.get(key)
        if _truthy_id(v):
            return v
    return None


def _first_block_with_id(data: dict[str, Any]) -> dict[str, Any] | None:
    """Procura id em listas típicas do IXC (registros, registro, etc.)."""
    for key in ("registros", "registro", "records", "result", "cliente", "dados"):
        block = data.get(key)
        if isinstance(block, list) and block and isinstance(block[0], dict):
            return block[0]
        if isinstance(block, dict):
            return block
    return None


def _is_error_payload(data: dict[str, Any]) -> bool:
    if data.get("type") == "error":
        return True
    if data.get("erro") or data.get("error"):
        return True
    return False


def _response_keys_hint(data: dict[str, Any]) -> str:
    keys = list(data.keys())[:14]
    return ", ".join(keys) if keys else "{}"


def _looks_like_html(s: str) -> bool:
    sl = s.lower()
    return "<div" in sl or "<html" in sl or "<body" in sl or (s.count("<") > 2 and s.count(">") > 2)


def _strip_html(s: str) -> str:
    plain = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", s)
    plain = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", plain)
    plain = re.sub(r"<[^>]+>", " ", plain)
    return re.sub(r"\s+", " ", plain).strip()


def _explain_known_backend_errors(text: str) -> str | None:
    """Padrões comuns quando o IXC devolve HTML ou texto em vez de JSON."""
    t = text.lower()
    if "connection refused" in t:
        return (
            "Connection refused: o servidor do IXC (ou PHP por trás do webservice) tentou conectar "
            "a outro serviço (na prática, muito comum: banco MySQL/MariaDB) e a conexão foi recusada — "
            "serviço parado, porta errada ou firewall no próprio servidor. "
            "O navegador pode receber HTTP 200 com uma página HTML de erro; isso não indica API OK."
        )
    if "could not connect" in t or "não foi possível conectar" in t:
        return (
            "Falha de conexão interna no servidor (mensagem semelhante a 'could not connect'). "
            "Verifique se o banco de dados e serviços do IXC estão no ar no host 192.168.x.x."
        )
    if "bad gateway" in t or "502" in t:
        return "Bad Gateway / 502: proxy ou PHP-FPM com problema; verifique nginx/apache e logs do IXC."
    return None


def _polish_user_message(msg: str) -> str:
    """Evita exibir HTML bruto na tabela de resultados."""
    msg = (msg or "").strip()
    if not msg:
        return "Erro sem mensagem."
    explained = _explain_known_backend_errors(msg)
    if explained and _looks_like_html(msg):
        snippet = _strip_html(msg)[:280]
        return f"{explained} Resumo: {snippet}" if snippet else explained
    if explained:
        return explained
    if _looks_like_html(msg):
        plain = _strip_html(msg)[:400]
        return f"Resposta em HTML (não é JSON de API). Trecho: {plain}" if plain else "Resposta em HTML (não é JSON de API)."
    return msg[:1200]


def _normalize_ixc_response(data: Any) -> tuple[bool, dict[str, Any] | None, str]:
    """
    Interpreta JSON do webservice IXC / v1.

    Retorna (ok, payload_normalizado, mensagem). Em sucesso, garante chave ``id``
    no dict retornado quando o ID puder ser inferido (para extract_id).
    """
    if isinstance(data, list):
        if not data:
            return False, None, "Resposta JSON: lista vazia."
        first = data[0]
        if not isinstance(first, dict):
            return False, None, "Resposta JSON: lista sem objeto."
        rid = _pick_id_from_dict(first)
        if rid is None:
            return False, first, "Resposta JSON: primeiro item sem id/id_cliente."
        merged = {**first, "id": rid}
        msg = str(first.get("message") or first.get("mensagem") or "OK")
        return True, merged, msg

    if not isinstance(data, dict):
        return False, None, "Resposta não é um objeto JSON."

    if "_text" in data:
        raw = data.get("_text") or ""
        return False, data, _polish_user_message(str(raw))

    if _is_error_payload(data):
        msg = (
            data.get("message")
            or data.get("mensagem")
            or data.get("erro")
            or data.get("error")
            or "Erro retornado pela API."
        )
        return False, data, _polish_user_message(str(msg))

    if data.get("type") == "success":
        rid = _pick_id_from_dict(data)
        if rid is None:
            inner = _first_block_with_id(data)
            if inner is not None:
                rid = _pick_id_from_dict(inner)
        if _truthy_id(rid):
            out = dict(data)
            if not _truthy_id(out.get("id")):
                out["id"] = rid
            msg = str(data.get("message") or data.get("mensagem") or "OK")
            return True, out, msg
        return False, data, _polish_user_message(
            str(data.get("message") or data.get("mensagem") or "Sucesso sem id na resposta.")
        )

    rid = _pick_id_from_dict(data)
    if rid is not None:
        out = dict(data)
        if not _truthy_id(out.get("id")):
            out["id"] = rid
        msg = str(data.get("message") or data.get("mensagem") or "OK")
        return True, out, msg

    inner = data.get("data")
    if isinstance(inner, dict):
        rid = _pick_id_from_dict(inner)
        if rid is not None:
            out = {**data, **inner}
            if not _truthy_id(out.get("id")):
                out["id"] = rid
            msg = str(data.get("message") or inner.get("message") or inner.get("mensagem") or "OK")
            return True, out, msg

    block = _first_block_with_id(data)
    if block is not None:
        rid = _pick_id_from_dict(block)
        if rid is not None:
            out = {**data, **block, "id": rid}
            msg = str(block.get("message") or block.get("mensagem") or data.get("message") or "OK")
            return True, out, msg

    hint = _response_keys_hint(data)
    msg = data.get("message") or data.get("mensagem")
    if msg:
        return False, data, _polish_user_message(f"{msg} (campos: {hint})")
    return False, data, f"Resposta inesperada — não foi encontrado id/id_cliente. Campos: {hint}"


def _normalize_base_url(base: str) -> str:
    base = (base or "").strip().rstrip("/")
    if not base:
        return ""
    if not base.startswith(("http://", "https://")):
        base = "https://" + base
    return base


def post_json(
    base_url: str,
    path: str,
    payload: dict[str, Any],
    username: str,
    password: str,
    timeout: int = 120,
    verify_ssl: bool = True,
    method: str = "POST",  # <--- NOVO PARÂMETRO COM VALOR PADRÃO
) -> ApiResult:
    base = _normalize_base_url(base_url)
    if not base:
        return ApiResult(False, None, "Base URL vazia.", None)
    url = f"{base}{path if path.startswith('/') else '/' + path}"
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        # Usa requests.request para aceitar dinamicamente POST ou PUT
        r = requests.request(
            method=method.upper(),
            url=url,
            json=payload,
            auth=(username, password),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=timeout,
            verify=verify_ssl,
        )
    except requests.RequestException as e:
        return ApiResult(False, None, str(e), None)

    try:
        data = r.json()
    except ValueError:
        data = {"_text": r.text[:2000]}

    if r.status_code >= 400:
        msg = data.get("message") if isinstance(data, dict) else r.text[:500]
        return ApiResult(False, r.status_code, msg or f"HTTP {r.status_code}", data if isinstance(data, dict) else None)

    ok, normalized, msg = _normalize_ixc_response(data)
    if ok and normalized is not None:
        return ApiResult(True, r.status_code, msg, normalized)

    if isinstance(normalized, dict):
        raw_out: dict[str, Any] | str | None = normalized
    elif isinstance(data, dict):
        raw_out = data
    elif isinstance(data, list):
        raw_out = {"_lista_resposta": data[:5]}
    else:
        raw_out = None
    return ApiResult(False, r.status_code, msg, raw_out)


def extract_id(result: ApiResult) -> str | None:
    if not result.ok or not isinstance(result.raw, dict):
        return None
    rid = result.raw.get("id")
    if rid is None:
        rid = result.raw.get("id_cliente")
    return str(rid) if _truthy_id(rid) else None
