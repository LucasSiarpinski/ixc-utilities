# IXC Utilities

Aplicação web Flask para automação de módulos do IXCSoft — criação em lote de clientes/contratos, geração de boletos e demais utilitários.

---

## Pré-requisitos

- **Python 3.10+** instalado
- **Git** instalado
- Acesso à internet para clonar o repositório e instalar dependências

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/ronye011/ixc-utilities
cd ixc-utilities
```

### 2. Instale o suporte a ambientes virtuais (apenas na primeira vez)

> Necessário em sistemas Debian/Ubuntu onde o Python é gerenciado pelo sistema operacional.

```bash
sudo apt update && sudo apt install python3-venv python3-full -y
```

### 3. Crie o ambiente virtual

```bash
python3 -m venv .venv
```

### 4. Ative o ambiente virtual

**Linux / macOS:**
```bash
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

> Após ativar, o prompt do terminal exibirá `(.venv)` no início.

### 5. Instale as dependências

```bash
pip install -r requirements.txt
```

---

## Execução

Com o ambiente virtual ativo, rode:

```bash
python app.py
```

A aplicação estará disponível em: **http://127.0.0.1:5000**

---

## Desativar o ambiente virtual

Quando terminar de usar, desative o ambiente virtual com:

```bash
deactivate
```

---

## Próximas execuções

Nas próximas vezes que for usar a aplicação, basta ativar o ambiente virtual e rodar:

```bash
source .venv/bin/activate   # Linux/macOS
python app.py
```

---

## Estrutura do projeto

```
ixc-utilities/
├── app.py              # Ponto de entrada da aplicação Flask
├── api_client.py       # Cliente HTTP para a API do IXCSoft
├── blueprints/
│   ├── lote.py         # Rotas de criação em lote (clientes/contratos)
│   └── modulos.py      # Rotas dos demais módulos
├── templates/          # Templates HTML (Jinja2)
├── static/             # Arquivos estáticos (CSS, JS, imagens)
├── fixtures/           # Dados de exemplo / fixtures
└── requirements.txt    # Dependências Python
```

---

## Dependências

| Pacote | Versão mínima | Descrição |
|--------|--------------|-----------|
| Flask | 3.0.0 | Framework web |
| requests | 2.31.0 | Chamadas HTTP à API do IXCSoft |
| urllib3 | 2.0.0 | Gerenciamento de conexões HTTP |

---

## Solução de problemas

### `externally-managed-environment` ao rodar `pip install`

Este erro ocorre em sistemas Debian/Ubuntu modernos que protegem o Python do sistema. **Solução:** sempre utilize o ambiente virtual (passos 2–5 acima).

### Porta 5000 já em uso

Altere a porta no final do `app.py`:

```python
app.run(debug=True, host="127.0.0.1", port=5001)
```

---

## Licença

Uso interno — IXC Lucao.
