"""Rotas placeholder para futuras ferramentas (boletos, massa em contratos, etc.)."""

from __future__ import annotations

from flask import Blueprint, render_template

bp = Blueprint("modulos", __name__, url_prefix="/modulos")


@bp.get("/massa-contratos")
def massa_contratos():
    return render_template(
        "modulos/em_breve.html",
        titulo="Massa em contratos",
        descricao="Ações em lote sobre contratos já criados (alterações, segunda via, etc.).",
    )


@bp.get("/boletos")
def boletos():
    return render_template(
        "modulos/em_breve.html",
        titulo="Boletos",
        descricao="Consulta e recebimento de boletos em massa.",
    )
