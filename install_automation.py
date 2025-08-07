# -*- coding: utf-8 -*-
"""
HASHIRU 6.1 - INSTALADOR DE AUTOMAÇÃO COMPLETA
Instala todas as dependências necessárias para automação completa
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(command, description):
    """Executar comando e mostrar resultado"""
    print(f"\n🔧 {description}")
    print(f"💻   Executando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅   Sucesso!")
            if result.stdout.strip():
                print(f"📋   Output: {result.stdout.strip()}")
        else:
            print(f"❌   Erro!")
            if result.stderr.strip():
                print(f"🚨   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"💥   Exceção: {str(e)}")
        return False
    
    return True

def install_python_packages():
    """Instalar pacotes Python necessários"""
    packages = [
        ("selenium", "Automação de browser web"),
        ("pyautogui", "Automação de desktop (mouse/teclado)"),
        ("duckduckgo-search", "Busca na internet"),
        ("pillow", "Processamento de imagens (para PyAutoGUI)"),
        ("opencv-python", "Visão computacional (para localizar imagens)"),
        ("webdriver-manager", "Gerenciamento automático de drivers")
    ]
    
    print("🎯  INSTALANDO PACOTES PYTHON")
    print("=" * 50)
    
    for package, description in packages:
        success = run_command(
            f"pip install {package} --upgrade",
            f"Instalando {package} - {description}"
        )
        if not success:
            print(f"⚠️   Continuando mesmo com erro em {package}...")

def install_chrome_driver():
    """Verificar se Chrome/Chromedriver está disponível"""
    print("\n🌐  VERIFICANDO CHROME/CHROMEDRIVER")
    print("=" * 50)
    
    # Verificar Chrome
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser"
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅   Chrome encontrado: {path}")
            chrome_found = True
            break
    
    if not chrome_found:
        print("❌   Chrome não encontrado!")
        print("📥   Por favor, instale o Google Chrome:")
        print("      https://www.google.com/chrome/")
        return False
    
    # Testar webdriver-manager
    try:
        print("\n🔧   Testando webdriver-manager...")
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Isso vai baixar o chromedriver automaticamente
        service = Service(ChromeDriverManager().install())
        print("✅   WebDriver Manager funcionando!")
        
        # Teste rápido do driver
        print("🧪   Testando inicialização do Chrome...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f"✅   Chrome WebDriver funcionando! (Título: {title})")
        return True
        
    except Exception as e:
        print(f"❌   Erro no WebDriver: {str(e)}")
        print("💡   Tentativa manual necessária...")
        return False

def test_pyautogui():
    """Testar PyAutoGUI"""
    print("\n🖱️   TESTANDO PYAUTOGUI")
    print("=" * 50)
    
    try:
        import pyautogui
        
        # Configurações de segurança
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Teste básico
        screen_size = pyautogui.size()
        mouse_pos = pyautogui.position()
        
        print(f"✅   PyAutoGUI funcionando!")
        print(f"📱   Tamanho da tela: {screen_size}")
        print(f"🖱️   Posição do mouse: {mouse_pos}")
        print(f"🛡️   Fail-safe ativo: {pyautogui.FAILSAFE}")
        
        return True
        
    except Exception as e:
        print(f"❌   Erro no PyAutoGUI: {str(e)}")
        return False

def test_duckduckgo():
    """Testar DuckDuckGo Search"""
    print("\n🔍  TESTANDO DUCKDUCKGO SEARCH")
    print("=" * 50)
    
    try:
        from duckduckgo_search import DDGS
        
        print("🌐   Fazendo busca de teste...")
        with DDGS() as ddgs:
            results = list(ddgs.text(keywords="python programming", region="us-en"))
            
        if results:
            print(f"✅   DuckDuckGo funcionando! ({len(results)} resultados)")
            print(f"📋   Primeiro resultado: {results[0].get('title', 'N/A')}")
            return True
        else:
            print("❌   Nenhum resultado retornado")
            return False
            
    except Exception as e:
        print(f"❌   Erro no DuckDuckGo: {str(e)}")
        return False

def create_automation_integration():
    """Criar arquivo de integração com HASHIRU"""
    integration_code = '''# -*- coding: utf-8 -*-
"""
HASHIRU 6.1 - INTEGRAÇÃO DE AUTOMAÇÃO
Adicione este código ao seu tools/__init__.py ou main_agent.py
"""

from tools.automation_master import AUTOMATION_COMMANDS

# Integrar comandos de automação ao sistema principal
def register_automation_commands():
    """Registrar todos os comandos de automação"""
    return AUTOMATION_COMMANDS

# Exemplo de uso no main_agent.py:
"""
from tools.automation_master import get_automation_master

# No seu handler de comandos, adicione:
if command.startswith("/auto_"):
    automation_master = get_automation_master()
    
    if command == "/auto_search":
        result = automation_master.search_and_analyze(args)
    elif command == "/auto_browse":
        result = automation_master.navigate_to(args)
    elif command == "/auto_research":
        result = automation_master.auto_research_and_save(args)
    # ... etc
    
    return result
"""
'''
    
    integration_file = Path("automation_integration.py")
    with open(integration_file, 'w', encoding='utf-8') as f:
        f.write(integration_code)
    
    print(f"\n📁  ARQUIVO DE INTEGRAÇÃO CRIADO")
    print("=" * 50)
    print(f"✅   Arquivo: {integration_file.absolute()}")
    print("📋   Use este código para integrar ao HASHIRU")

def show_usage_examples():
    """Mostrar exemplos de uso"""
    examples = """
📚  EXEMPLOS DE USO DO SISTEMA DE AUTOMAÇÃO
=" * 50

🔍  BUSCA E PESQUISA:
    /auto_search "machine learning Python"
    /auto_research "artificial intelligence trends" 5

🌐  AUTOMAÇÃO WEB:
    /auto_browse "https://python.org"
    /auto_click "#search-input" css
    /auto_click "//button[@type='submit']" xpath

🖱️  AUTOMAÇÃO DESKTOP:
    /auto_screenshot "minha_tela"
    /auto_type "Hello World!"
    /auto_keys "ctrl" "c"
    /auto_folder "C:\\meu_projeto_livre"

🤖  AUTOMAÇÃO COMPLETA:
    /auto_research "Python web frameworks" 3
    → Busca na internet
    → Abre 3 melhores sites
    → Analisa cada página
    → Captura screenshots
    → Salva relatório completo

📁  ARQUIVOS SALVOS EM:
    C:\\meu_projeto_livre\\
    ├── downloads/          # Downloads automáticos
    ├── screenshots/        # Capturas de tela
    ├── automation_logs/    # Logs de automação
    ├── web_captures/       # Capturas de páginas
    └── research/           # Relatórios de pesquisa

🛡️  SEGURANÇA:
    - Fail-safe do PyAutoGUI ativo (mouse nos cantos = parar)
    - Timeouts em todas as operações web
    - Backups automáticos
    - Logs detalhados de todas as ações
"""
    
    print(examples)

def main():
    """Instalação principal"""
    print("🚀  HASHIRU 6.1 - INSTALADOR DE AUTOMAÇÃO COMPLETA")
    print("=" * 60)
    print("Este script vai instalar:")
    print("  • Selenium (automação web)")
    print("  • PyAutoGUI (automação desktop)")
    print("  • DuckDuckGo Search (busca internet)")
    print("  • Dependências necessárias")
    print("=" * 60)
    
    # Verificar Python
    python_version = sys.version_info
    print(f"🐍  Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 7):
        print("❌  Python 3.7+ é necessário!")
        return
    
    # Verificar plataforma
    os_info = platform.system()
    print(f"💻  Sistema: {os_info} {platform.release()}")
    
    # 1. Instalar pacotes Python
    install_python_packages()
    
    # 2. Configurar Chrome/WebDriver
    chrome_ok = install_chrome_driver()
    
    # 3. Testar PyAutoGUI
    pyautogui_ok = test_pyautogui()
    
    # 4. Testar DuckDuckGo
    ddg_ok = test_duckduckgo()
    
    # 5. Criar integração
    create_automation_integration()
    
    # Resumo final
    print("\n🎯  RESUMO DA INSTALAÇÃO")
    print("=" * 50)
    print(f"🌐  Chrome/Selenium: {'✅ OK' if chrome_ok else '❌ ERRO'}")
    print(f"🖱️  PyAutoGUI: {'✅ OK' if pyautogui_ok else '❌ ERRO'}")
    print(f"🔍  DuckDuckGo: {'✅ OK' if ddg_ok else '❌ ERRO'}")
    
    all_ok = chrome_ok and pyautogui_ok and ddg_ok
    
    if all_ok:
        print("\n🎉  INSTALAÇÃO COMPLETA COM SUCESSO!")
        print("🚀  Sistema de automação pronto para uso!")
        show_usage_examples()
    else:
        print("\n⚠️  INSTALAÇÃO PARCIAL")
        print("Algumas funcionalidades podem não funcionar.")
        print("Verifique os erros acima e tente resolver.")
    
    print("\n📁  PRÓXIMOS PASSOS:")
    print("1. Cole o arquivo automation_master.py em tools/")
    print("2. Integre os comandos ao main_agent.py")
    print("3. Reinicie o Chainlit")
    print("4. Teste com /auto_search 'teste'")

if __name__ == "__main__":
    main()