@echo off
echo =========================================
echo  Iniciando Servidor Ezio Finance API
echo =========================================

REM Verifica se o ambiente virtual existe
IF NOT EXIST .venv (
    echo ---
    echo -- ATENCAO: Ambiente virtual .venv nao encontrado.
    echo --          Certifique-se de cria-lo com: python -m venv .venv
    echo ---
    pause
    exit /b 1
)

echo.
echo --- Ativando ambiente virtual ---
call .venv\Scripts\activate

echo.
echo --- Iniciando servidor FastAPI com Uvicorn ---
echo --- Host: 127.0.0.1, Porta: 5000
echo --- Pressione CTRL+C para parar o servidor.
echo.

uvicorn api.server:app --host 127.0.0.1 --port 5000 --reload

echo.
echo --- Desativando ambiente virtual ---
deactivate

echo.
echo Servidor finalizado.
pause
