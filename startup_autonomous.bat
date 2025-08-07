@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ================================================
REM HASHIRU 6.1 - STARTUP AUTÔNOMO SEM RESTRIÇÕES
REM Sistema de inicialização completa para agente autônomo
REM ================================================

REM --- Console em UTF-8 para acentuação e emojis ---
chcp 65001 >nul
title HASHIRU 6.1 - Inicializando Sistema Autônomo
color 0A

echo.
echo ========================================
echo 🚀 HASHIRU 6.1 - AGENTE AUTÔNOMO
echo ========================================
echo.

REM Verificar se estamos no diretório correto
if not exist "main_agent.py" (
    echo ❌ ERRO: main_agent.py não encontrado!
    echo Execute este script no diretório do projeto HASHIRU_6_1
    pause
    exit /b 1
)
echo ✅ Diretório do projeto verificado
echo.

REM Ativar ambiente virtual se existir
if exist "hashiru_6_env\Scripts\activate.bat" (
    echo 🔧 Ativando ambiente virtual...
    call "hashiru_6_env\Scripts\activate.bat"
    if errorlevel 1 (
        echo ⚠️  Nao foi possivel ativar o ambiente virtual. Continuando com Python global...
    ) else (
        echo ✅ Ambiente virtual ativo
    )
) else (
    echo ⚠️  Ambiente virtual nao encontrado - usando Python global
)
echo.

REM Forçar Python a operar em UTF-8
set PYTHONUTF8=1

REM Verificar Python
echo 🐍 Verificando Python...
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python nao encontrado no PATH!
    echo Instale o Python 3.8+ e tente novamente.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version') do set PYVER=%%v
echo ✅ Python %%PYVER%% encontrado
echo.

REM Garantir pip utilizavel
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: pip nao encontrado!
    echo Reinstale o Python habilitando "Add pip" ou rode: python -m ensurepip
    pause
    exit /b 1
)

REM Verificar Ollama CLI
echo 🧠 Verificando Ollama (CLI)...
where ollama >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Ollama nao encontrado no PATH!
    echo Instale o Ollama e tente novamente.
    pause
    exit /b 1
)
for /f "usebackq tokens=1,2 delims= " %%a in (`ollama --version 2^>^&1`) do (
    set OLV=%%a %%b
    goto :ollama_ok
)
:ollama_ok
echo ✅ Ollama: !OLV!
echo.

REM Verificar se o Ollama esta rodando (porta 11434)
echo 🔍 Verificando se Ollama esta ativo...
set OLLAMA_HOST=localhost:11434
set OLLAMA_BASE_URL=http://localhost:11434

REM Tentar conectar com retries
where curl >nul 2>&1
if errorlevel 1 (
    echo ⚠️  curl nao encontrado. Usando PowerShell para testes HTTP.
    set USE_PWSH=1
) else (
    set USE_PWSH=0
)

REM Se nao houver nada na porta, tentar subir
netstat -an | findstr ":11434" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo 🚀 Iniciando Ollama em segundo plano...
    start "" ollama serve
    echo ⏳ Aguardando Ollama inicializar...
) else (
    echo ✅ Ollama ja esta rodando
)

REM Espera ativa ate 12 tentativas (~12s com curl -s; com PowerShell, pequeno atraso)
set /a __tries=0
:wait_ollama
set /a __tries+=1
if "!USE_PWSH!"=="1" (
    powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing %OLLAMA_BASE_URL%/api/tags -TimeoutSec 2) | Out-Null; exit 0 } catch { exit 1 }"
) else (
    curl -s %OLLAMA_BASE_URL%/api/tags >nul 2>&1
)
if errorlevel 1 (
    if !__tries! GEQ 12 (
        echo ❌ ERRO: Ollama nao respondeu apos aguardar.
        echo Verifique o servico do Ollama e tente novamente.
        pause
        exit /b 1
    )
    REM pequeno atraso entre tentativas
    >nul ping 127.0.0.1 -n 2
    goto :wait_ollama
)
echo ✅ Ollama respondendo
echo.

REM Verificar modelos Ollama (opcional)
echo 🤖 Modelos de IA disponiveis no Ollama:
ollama list
echo.

REM Instalar dependencias
echo 📦 Verificando dependencias Python...
if exist "requirements.txt" (
    echo 🔧 Instalando a partir de requirements.txt ...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ⚠️  Erro ao instalar requirements. Continuando com pacotes minimos...
    )
) else (
    echo ⚠️  requirements.txt nao encontrado. Instalando pacotes essenciais...
)

REM Pacotes essenciais (reinstala se faltar)
python -m pip show httpx >nul 2>&1 || python -m pip install httpx
python -m pip show chainlit >nul 2>&1 || python -m pip install chainlit
echo ✅ Dependencias checadas
echo.

REM Criar diretórios necessários
echo 📁 Criando estrutura de diretorios...
if not exist "utils" mkdir "utils"
if not exist "artifacts" mkdir "artifacts"
if not exist "backups" mkdir "backups"
if not exist "tools" mkdir "tools"
if not exist "logs" mkdir "logs"
echo ✅ Diretorios ok

REM Garantir __init__.py em tools
if not exist "tools\__init__.py" (
    echo from __future__ import annotations>"tools\__init__.py"
    echo # HASHIRU tools package>>"tools\__init__.py"
    echo ✅ Criado tools\__init__.py
) else (
    echo ✅ tools\__init__.py OK
)
echo.

REM Limpar cache Python superficial
echo 🧹 Limpando __pycache__ (nivel 1)...
for /d %%d in (*) do (
    if exist "%%d\__pycache__" (
        rmdir /s /q "%%d\__pycache__" 2>nul
    )
)
if exist "__pycache__" rmdir /s /q "__pycache__" 2>nul
echo ✅ Cache limpo
echo.

REM Verificar arquivos essenciais
echo 🔍 Verificando arquivos do sistema...
if not exist "main_agent.py" (
    echo ❌ main_agent.py nao encontrado!
    pause
    exit /b 1
) else (
    echo ✅ main_agent.py OK
)

if not exist "utils\self_modification_engine.py" (
    echo ⚠️  utils\self_modification_engine.py nao encontrado - auto-melhoria limitada
) else (
    echo ✅ self_modification_engine.py OK
)

if not exist "config.py" (
    echo ⚠️  config.py nao encontrado - usando configuracoes padrao
) else (
    echo ✅ config.py OK
)
echo.

REM Verificar modelos essenciais (dica para o usuario)
echo 🎯 Verificando modelos essenciais no Ollama...
ollama list | findstr /i "llama3.1:8b" >nul
if errorlevel 1 (
    echo ⚠️  Modelo "llama3.1:8b" nao encontrado. Sugestao:
    echo     ollama pull llama3.1:8b
) else (
    echo ✅ llama3.1:8b disponivel
)

ollama list | findstr /i "deepseek-coder:6.7b" >nul
if errorlevel 1 (
    echo ⚠️  Modelo "deepseek-coder:6.7b" nao encontrado. Sugestao:
    echo     ollama pull deepseek-coder:6.7b
) else (
    echo ✅ deepseek-coder:6.7b disponivel
)

ollama list | findstr /i "deepseek-r1:8b" >nul
if errorlevel 1 (
    echo ⚠️  Modelo "deepseek-r1:8b" nao encontrado. Sugestao:
    echo     ollama pull deepseek-r1:8b
) else (
    echo ✅ deepseek-r1:8b disponivel
)
echo.

REM Configurar variaveis de ambiente para esta sessao
echo ⚙️  Configurando ambiente...
set CHAINLIT_AUTH_SECRET=hashiru-autonomous-secret
set CHAINLIT_PORT=8080
set OLLAMA_HOST=localhost:11434
echo ✅ Variaveis configuradas
echo.

REM Verificar Chainlit CLI
where chainlit >nul 2>&1
if errorlevel 1 (
    echo ⛓️  Instalando Chainlit CLI...
    python -m pip install chainlit
    where chainlit >nul 2>&1
    if errorlevel 1 (
        echo ❌ ERRO: Chainlit nao esta disponivel apos instalacao.
        pause
        exit /b 1
    )
)
for /f "usebackq tokens=1,2 delims= " %%a in (`chainlit --version 2^>^&1`) do (
    set CLV=%%a %%b
    goto :chainlit_ok
)
:chainlit_ok
echo ✅ Chainlit: !CLV!
echo.

REM Banner de inicialização
echo ================================================
echo 🔥 SISTEMA HASHIRU 6.1 AUTÔNOMO PRONTO!
echo ================================================
echo.
echo 🧠 IAs Disponiveis:
echo    - Llama3.1 8B (conversacao)
echo    - DeepSeek-Coder 6.7B (codigo)
echo    - DeepSeek-R1 8B (raciocinio)
echo    - Outros modelos conforme disponivel
echo.
echo ⚡ Capacidades Ativas:
echo    - Modificacao de codigo SEM restricoes
echo    - Execucao automatica de comandos
echo    - Auto-melhoria continua
echo    - Pesquisa e analise independente
echo    - Controle total do sistema
echo.
echo 🎯 Sistema configurado para MAXIMA AUTONOMIA
echo ================================================
echo.

REM Aguardar confirmacao do usuario
echo Pressione qualquer tecla para iniciar o Chainlit...
pause >nul

REM Iniciar Chainlit
echo.
echo 🚀 Iniciando Chainlit na porta 8080...
echo - Acesse: http://localhost:8080
echo - Sistema 100%% autonomo ativo
echo - Todas as restricoes removidas (conforme seu setup)
echo - Execute comandos livremente
echo.
echo Para parar: Ctrl+C
echo.

REM Execucao principal (mantem o processo em primeiro plano)
chainlit run "main_agent.py" --port 8080 --host 127.0.0.1
set __rc=%ERRORLEVEL%

REM Se chegou aqui, o Chainlit foi fechado
echo.
echo ================================================
echo 🛑 HASHIRU 6.1 FINALIZADO (erro %%__rc%%)
echo ================================================
echo.
echo Sistema autonomo foi encerrado.
echo Logs de auditoria (se habilitados) em utils\audit.py
echo Artifacts em .\artifacts
echo Backups em .\backups
echo.
pause
endlocal
exit /b %__rc%
