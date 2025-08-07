<#  setup_superezio.ps1
    Gera chainlit.md e public\superezio.css em UTF-8               #>

$root = "C:\Users\marco\agente_gemini\HASHIRU_6_1"
Set-Location $root

if (-not (Test-Path "$root\public")) {
    New-Item -ItemType Directory -Path "$root\public" | Out-Null
}

# --------- chainlit.md ---------
$md = @'
# SUPEREZIO | Command Deck
*Uma interface cognitiva desenvolvida por **Marco Barreto**, **Gemini** & **ChatGPT**.*

---

### **DIAGNÓSTICO DO SISTEMA**
<div class="diag-container">

| Componente          | Status                                         | Detalhes                                  |
| :--                 | :--                                            | :--                                       |
| **CORE COGNITIVO**  | <span class="status-online">✅ ONLINE</span>   | Motor de raciocínio ativo                 |
| **MÓDULO AUTOMAÇÃO**| <span class="status-active">🚀 ATIVO</span>    | Protocolos de web & desktop prontos       |
| **LINK NEURAL**     | <span class="status-stable">🧠 ESTÁVEL</span>  | Conexão com a base de conhecimento        |

</div>

---

Aguardando sua primeira diretiva.  
Digite `/help` para ver a *Knowledge Base* de comandos.
'@

$md | Set-Content -Encoding UTF8 "$root\chainlit.md"

# --------- public/superezio.css (crie ou sobrescreva) ---------
$css = @'
/* public/superezio.css – HUD Vitrificado v2.1 */
@import url("https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap");

:root{
  --bg:#0A121F;
  --glass:rgba(20,35,60,.65);
  --accent-cyan:#64FFDA;
  --primary-orange:#FF6B35;
  --text-primary:#CCD6F6;
}

/* …restante igual ao v2.1… */
'@

$css | Set-Content -Encoding UTF8 "$root\public\superezio.css"

Write-Host "`n✅ Arquivos gravados em UTF-8 com sucesso!"
