@echo off
setlocal EnableDelayedExpansion

REM Navigate to script directory
cd /d "%~dp0"

echo.
echo [SUPEREZIO] Corrigindo formatacao do chainlit.toml...
echo.

REM Backup do arquivo atual
if exist chainlit.toml (
    copy chainlit.toml chainlit.toml.backup
    echo ✅ Backup criado: chainlit.toml.backup
)

REM Recreate chainlit.toml with proper formatting
(
    echo # chainlit.toml - Configuracao do Command Deck SUPEREZIO
    echo.
    echo [project]
    echo name = "SUPEREZIO | Command Deck"
    echo description = "Uma interface cognitiva desenvolvida por Marco Barreto, Gemini & ChatGPT."
    echo show_readme_as_default = true
    echo.
    echo [UI]
    echo custom_css = "public/superezio.css"
    echo.
    echo [UI.theme]
    echo background_color = "#0A192F"
    echo primary_color = "#FF6B35"
    echo text_color = "#CCD6F6"
) > chainlit.toml

echo ✅ Arquivo chainlit.toml corrigido com formatacao adequada!
echo.
echo Conteudo atual:
echo ----------------------------------------
type chainlit.toml
echo ----------------------------------------
echo.
pause