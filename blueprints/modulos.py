"""Rotas placeholder para futuras ferramentas (boletos, massa em contratos, etc.)."""

from __future__ import annotations

from flask import Blueprint, render_template

bp = Blueprint("modulos", __name__, url_prefix="/modulos")


@bp.get("/massa-contratos")
def massa_contratos():
    return render_template(
        "modulos/em_breve.html",
    )


@bp.get("/boletos")
def boletos():
    return render_template(
        "modulos/em_breve.html",
    )

@bp.get("/modelo-contrato")
def modelo_contrato():
    return render_template(
        "modulos/modelo_de_contrato/index.html"
    )

@bp.get("/processar-logs-em-massa")
def processar_logs_em_massa():
    return render_template(
        "modulos/processar_logs_em_massa/index.html",
    )

