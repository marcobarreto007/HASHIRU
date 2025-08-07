@echo off
setlocal EnableDelayedExpansion

REM Navigate to script directory
cd /d "%~dp0"

echo.
echo [SUPEREZIO] Recriando arquivos em UTF-8...
echo.

REM 1) chainlit.toml
echo Criando chainlit.toml...
(
  echo # chainlit.toml - Configuracao do Command Deck SUPEREZIO
  echo [project]
  echo name = "SUPEREZIO | Command Deck"
  echo description = "Uma interface cognitiva desenvolvida por Marco Barreto, Gemini e ChatGPT."
  echo show_readme_as_default = true
  echo [UI]
  echo custom_css = "public/superezio.css"
  echo [UI.theme]
  echo background_color = "#0A192F"
  echo primary_color = "#FF6B35"
  echo text_color = "#CCD6F6"
) > chainlit.toml

REM 2) chainlit.md
echo Criando chainlit.md...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$content = @'
# 🌟 SUPEREZIO | Command Deck
*Uma interface cognitiva desenvolvida por **Marco Barreto**, **Gemini** & **ChatGPT**.*

---

### **DIAGNÓSTICO DO SISTEMA**
<div class=\"diag-container\">

| Componente          | Status                                         | Detalhes                                  |
| :--                 | :--                                            | :--                                       |
| **CORE COGNITIVO**  | <span class=\"status-online\">✅ ONLINE</span>   | Motor de raciocínio ativo                 |
| **MÓDULO AUTOMAÇÃO**| <span class=\"status-active\">🚀 ATIVO</span>   | Protocolos de web & desktop prontos       |
| **LINK NEURAL**     | <span class=\"status-stable\">🧠 ESTÁVEL</span> | Conexão com a base de conhecimento        |

</div>

---

Aguardando sua primeira diretiva.  
Digite `/help` para ver a *Knowledge Base* de comandos.
'@; [System.IO.File]::WriteAllText('chainlit.md', $content, [System.Text.Encoding]::UTF8)"

REM 3) public\superezio.css
echo Criando public\superezio.css...
if not exist public mkdir public
powershell -NoProfile -ExecutionPolicy Bypass -Command "$content = @'
/* 🎨 public/superezio.css - HUD Vitrificado v2.1 */
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');

:root {
  --bg: #0A121F;
  --glass: rgba(20, 35, 60, 0.65);
  --accent-cyan: #64FFDA;
  --primary-orange: #FF6B35;
  --text-primary: #CCD6F6;
}

html, body {
  background: var(--bg);
  color: var(--text-primary);
  font-family: 'Roboto Mono', monospace;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to   { opacity: 1; transform: translateY(0); }
}

#root .main {
  background: var(--glass) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(100,255,218,0.25);
  border-radius: 12px;
  animation: fadeIn .6s ease-out;
}

h1,h2,h3 {
  color: var(--accent-cyan) !important;
  text-shadow: 0 0 8px rgba(100,255,218,0.5);
}

.diag-container {
  background: rgba(0,0,0,0.25);
  border: 1px solid rgba(100,255,218,0.25);
  border-radius: 10px;
  padding: 1.25rem;
}

.status-online,
.status-active,
.status-stable {
  color: var(--accent-cyan);
  font-weight: bold;
  text-shadow: 0 0 8px var(--accent-cyan);
}

.message:not(.user-message) {
  border-left: 3px solid var(--accent-cyan);
  background: linear-gradient(90deg, rgba(100,255,218,0.06), transparent);
}

textarea {
  background: rgba(0,0,0,0.35) !important;
  border: 1px solid rgba(100,255,218,0.25) !important;
  caret-color: var(--primary-orange) !important;
  transition: all .2s ease-out;
}

textarea:focus {
  border-color: var(--primary-orange) !important;
  box-shadow: 0 0 12px rgba(255,107,53,0.6) !important;
}

button {
  background: var(--primary-orange) !important;
  color: #fff !important;
  font-weight: bold !important;
  transition: transform .2s ease-out !important;
}

button:hover {
  transform: translateY(-2px);
}

::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb {
  background: var(--primary-orange);
  border-radius: 6px;
  border: 2px solid var(--bg);
}
'@; [System.IO.File]::WriteAllText('public\superezio.css', $content, [System.Text.Encoding]::UTF8)"

echo.
echo ✅ Todos os arquivos foram recriados em UTF-8!
echo.
echo Proximos passos:
echo 1. Ativar venv: hashiru_6_env\Scripts\activate.bat
echo 2. Executar: python -m chainlit run main_agent.py --host 127.0.0.1 --port 8080
echo.
pause
endlocal