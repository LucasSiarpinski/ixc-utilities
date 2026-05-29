"""Aplicação web — módulos de automação (lote cliente/contrato, boletos, etc.)."""

from __future__ import annotations

from flask import Flask

from blueprints.lote import bp as lote_bp
from blueprints.modulos import bp as modulos_bp

app = Flask(__name__)
app.secret_key = "dev-bulk-contratos-altere-em-producao"

app.register_blueprint(lote_bp)
app.register_blueprint(modulos_bp)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
