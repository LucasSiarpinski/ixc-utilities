<div align="center">

# 📄 Conversor de Contratos IXC

**Converte modelos de contrato Word (.docx) para HTML compatível com o CKEditor do IXC Provedor — com bordas corretas e sem quebramento na impressão.**

[![Netlify](https://img.shields.io/badge/Acesse%20agora-conversor--contratos--ixc.netlify.app-3B82F6?style=for-the-badge&logo=netlify&logoColor=white)](https://conversor-contratos-ixc.netlify.app)
[![Licença MIT](https://img.shields.io/badge/Licença-MIT-22c55e?style=for-the-badge)](LICENSE)
![Sem backend](https://img.shields.io/badge/Sem%20backend-100%25%20browser-f59e0b?style=for-the-badge)

</div>

---

## O problema

Provedores de internet que usam o **IXC Provedor** precisam cadastrar modelos de contrato no editor de texto do sistema. O processo manual era demorado e propenso a erros:

| Situação | Antes | Depois |
|---|---|---|
| Tempo de cadastro | 60–120 min | 2–5 min |
| Tabelas quebradas na impressão | Frequente | Eliminado |
| Palavras coladas / sem espaço | Frequente | Eliminado |
| Alinhamento perdido | Frequente | Preservado |
| Retrabalho do operador | Alto | Zero |

**Causa raiz:** ao colar conteúdo do Word diretamente no CKEditor, estilos `mso-*` incompatíveis corrompem a formatação. Além disso, o CKEditor 5 envolve tabelas com `<figure class="table">` que o TCPDF (gerador de PDF do IXC) não renderiza corretamente — exibindo o texto das células verticalmente, letra por letra.

---

## Solução

A ferramenta lê o **XML interno do arquivo `.docx`** diretamente no browser (sem backend), extrai parágrafos, tabelas e formatações, e gera o HTML no formato nativo de cada versão do CKEditor — pronto para colar no IXC.

```
Contrato .docx  →  Ferramenta  →  HTML nativo CKEditor  →  IXC Provedor
```

---

## Como usar

### Opção 1 — Online (recomendado)

Acesse diretamente no navegador, sem instalar nada:

**[conversor-contratos-ixc.netlify.app](https://conversor-contratos-ixc.netlify.app)**

### Opção 2 — Arquivo local

1. Baixe o arquivo [`conversor_ixc.html`](conversor_ixc.html)
2. Abra no Chrome ou Edge

---

## Passo a passo no IXC

1. Selecione **CKEditor 5** ou **CKEditor 4** conforme a versão do seu IXC
2. Arraste o arquivo `.docx` ou clique em **Selecionar arquivo**
3. Confira o resultado no **Preview**
4. Clique em **Copiar HTML**
5. No IXC Provedor: `Modelo de contrato` → botão `</>` (código fonte) → seleciona tudo → cola → **OK** → **Salvar**

---

## Funcionalidades

- **CKEditor 4 e 5** — alterna entre os dois formatos com um clique; reconverte o arquivo automaticamente ao trocar
- **Tabelas com bordas corretas** — formato nativo de cada editor (`border-color:#000000` no CK5, `border="1"` no CK4)
- **Células mescladas** — `colspan` e `rowspan` extraídos do XML real do Word (`w:gridSpan`)
- **Espaços preservados** — runs de texto com `xml:space="preserve"` são lidos corretamente, evitando palavras coladas
- **Alinhamento** — centralizado, direita e justificado lidos do `w:jc` e aplicados via `text-align`
- **Formatação inline** — negrito (`<strong>`), itálico (`<em>`) e sublinhado (`<u>`) preservados
- **Histórico de sessão** — últimas 10 conversões ficam salvas enquanto a aba estiver aberta
- **Funciona offline** — nenhum dado sai do navegador; processamento 100% local
- **Cópia inteligente** — detecta automaticamente HTTPS ou HTTP e usa o método de cópia compatível

---

## Segurança

> **Nenhum dado do contrato é enviado para servidores externos.**

- O arquivo `.docx` é lido e processado inteiramente no browser do usuário
- Nenhum contrato, dado de cliente ou informação pessoal é armazenado
- Ao fechar a aba, tudo é descartado da memória
- Hospedado no Netlify com HTTPS/TLS — comunicação criptografada
- Código fonte aberto e auditável neste repositório

---

## Formatos de saída

### CKEditor 5

```html
<figure class="table" style="width:100%;">
  <table class="ck-table-resized" style="border-style:solid;">
    <colgroup>
      <col style="width:50%;">
      <col style="width:50%;">
    </colgroup>
    <tbody>
      <tr>
        <td style="border-color:#000000;">Conteúdo</td>
        <td style="border-color:#000000;" colspan="2">Célula mesclada</td>
      </tr>
    </tbody>
  </table>
</figure>
```

### CKEditor 4

```html
<table border="1" cellpadding="1" cellspacing="1" style="width:100%;">
  <tbody>
    <tr>
      <td>Conteúdo</td>
      <td colspan="2">Célula mesclada</td>
    </tr>
  </tbody>
</table>
```

---

## Como funciona internamente

Um arquivo `.docx` é um ZIP contendo XMLs no formato **OOXML** (padrão Microsoft). A ferramenta usa o **JSZip** para abrir esse ZIP no browser e lê o `word/document.xml` com o **DOMParser** nativo.

```
.docx (ZIP)
└── word/
    └── document.xml  ← lido pelo DOMParser
         ├── <w:p>    → <p style="text-align:...">
         ├── <w:tbl>  → <figure class="table"> (CK5) ou <table border="1"> (CK4)
         ├── <w:tc>   → <td colspan="N">  (colspan via w:gridSpan)
         ├── <w:r>    → <strong>, <em>, <u>
         └── <w:jc>   → text-align: center | right | justify
```

Não há Mammoth, não há backend, não há build step — apenas HTML, CSS e JavaScript puro.

---

## Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| HTML + CSS | — | Interface e layout |
| JavaScript | ES2020+ | Lógica de conversão e UI |
| [JSZip](https://stuk.github.io/jszip/) | 3.10.1 | Leitura do `.docx` como ZIP no browser |
| DOMParser | Nativo | Interpretação do XML OOXML |

---

## Deploy próprio

### Netlify (recomendado)

1. Faça fork deste repositório
2. Conecte no [Netlify](https://netlify.com) → **Add new site** → **Import from Git**
3. Deixe as configurações de build em branco
4. Clique em **Deploy** — URL pública gerada automaticamente

### VM com Nginx

```bash
sudo apt install nginx
sudo cp conversor_ixc.html /var/www/html/index.html
sudo chmod 644 /var/www/html/index.html
sudo chmod 755 /var/www/html/
```

Acesse: `http://IP-DA-VM/`

### Servidor local (testes)

```bash
python3 -m http.server 8080
# Acesse: http://localhost:8080/conversor_ixc.html
```

> **Atenção:** Em HTTP puro (sem HTTPS), o botão **Copiar HTML** usa um fallback via `execCommand` que funciona normalmente. A API `navigator.clipboard` exige HTTPS ou localhost.

---

## Estrutura do repositório

```
conversor_ixc.html   # ferramenta completa — único arquivo, sem dependências locais
CLAUDE.md            # contexto técnico detalhado para o Claude AI
README.md            # este arquivo
```

---

## Limitações conhecidas

| Limitação | Situação |
|---|---|
| Imagens dentro do `.docx` | Não convertidas |
| Listas numeradas / marcadores | Convertidas como parágrafos simples |
| Tamanho e família de fonte | Não preservados |
| Arquivos `.doc` (formato legado) | Não suportados — converta para `.docx` no Word antes |

---
