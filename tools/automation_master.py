# -*- coding: utf-8 -*-
"""
HASHIRU 6.1 - MASTER DE AUTOMAÇÃO COMPLETA
- Selenium: Automação web (clicar, navegar, formulários)
- PyAutoGUI: Automação desktop (clicar qualquer lugar, diálogos)
- DuckDuckGo: Busca inteligente na internet
- File Navigation: Navegação automática de pastas/arquivos
"""

import time
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import pyautogui
import subprocess
import os

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# DuckDuckGo search
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class AutomationMaster:
    """Master class para todas as automações: Web + Desktop + Busca + Navegação"""
    
    def __init__(self, free_path: Path = Path(r"C:\meu_projeto_livre")):
        self.free_path = free_path
        self.driver = None
        self.setup_pyautogui()
        self.create_directories()
        
    def setup_pyautogui(self):
        """Configuração segura do PyAutoGUI"""
        pyautogui.FAILSAFE = True  # Mouse nos cantos = parar
        pyautogui.PAUSE = 0.1      # Pausa entre comandos
        
    def create_directories(self):
        """Criar estrutura de pastas para automação"""
        directories = [
            self.free_path / "downloads",
            self.free_path / "screenshots", 
            self.free_path / "automation_logs",
            self.free_path / "web_captures",
            self.free_path / "research"
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # ============================================================================
    # 1. BUSCA INTELIGENTE NA INTERNET
    # ============================================================================
    
    def search_and_analyze(self, query: str, analyze_pages: bool = True) -> Dict[str, Any]:
        """Busca na internet + análise automática das páginas"""
        if not DDGS_AVAILABLE:
            return {"error": "DuckDuckGo search não disponível"}
            
        results = {"query": query, "timestamp": datetime.now().isoformat(), "results": []}
        
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(keywords=query, region="us-en")
                
                for i, result in enumerate(search_results):
                    if i >= 5:  # Limitar a 5 resultados
                        break
                        
                    result_data = {
                        "position": i + 1,
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "domain": result.get("href", "").split("/")[2] if result.get("href") else ""
                    }
                    
                    # Se pediu análise, abrir e analisar cada página
                    if analyze_pages and self.driver:
                        page_analysis = self.analyze_webpage(result_data["url"])
                        result_data["analysis"] = page_analysis
                    
                    results["results"].append(result_data)
                    
            # Salvar resultados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.free_path / "research" / f"search_{query.replace(' ', '_')}_{timestamp}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
            return results
            
        except Exception as e:
            return {"error": f"Erro na busca: {str(e)}"}
    
    # ============================================================================
    # 2. AUTOMAÇÃO WEB (SELENIUM)
    # ============================================================================
    
    def start_browser(self, headless: bool = False) -> Dict[str, Any]:
        """Iniciar browser Chrome com Selenium"""
        if not SELENIUM_AVAILABLE:
            return {"error": "Selenium não disponível. Instale: pip install selenium"}
            
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Tentar usar chromedriver do sistema
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            
            return {"success": True, "message": "Browser iniciado com sucesso"}
            
        except Exception as e:
            return {"error": f"Erro ao iniciar browser: {str(e)}"}
    
    def navigate_to(self, url: str) -> Dict[str, Any]:
        """Navegar para URL específica"""
        if not self.driver:
            init_result = self.start_browser()
            if "error" in init_result:
                return init_result
        
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
                
            self.driver.get(url)
            
            # Aguardar carregamento
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            return {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title
            }
            
        except Exception as e:
            return {"error": f"Erro ao navegar: {str(e)}"}
    
    def click_element(self, selector: str, selector_type: str = "css") -> Dict[str, Any]:
        """Clicar em elemento da página"""
        if not self.driver:
            return {"error": "Browser não inicializado"}
            
        try:
            # Definir tipo de seletor
            by_type = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class": By.CLASS_NAME,
                "tag": By.TAG_NAME,
                "text": By.LINK_TEXT
            }.get(selector_type, By.CSS_SELECTOR)
            
            # Aguardar elemento aparecer
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by_type, selector))
            )
            
            # Rolar até o elemento
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Clicar
            element.click()
            
            return {
                "success": True,
                "message": f"Clicou em elemento: {selector}",
                "element_text": element.text[:100]
            }
            
        except Exception as e:
            return {"error": f"Erro ao clicar: {str(e)}"}
    
    def fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Preencher formulário automaticamente"""
        if not self.driver:
            return {"error": "Browser não inicializado"}
            
        results = []
        
        for field_selector, value in form_data.items():
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, field_selector))
                )
                
                element.clear()
                element.send_keys(value)
                
                results.append({
                    "field": field_selector,
                    "success": True,
                    "value_filled": value
                })
                
            except Exception as e:
                results.append({
                    "field": field_selector,
                    "success": False,
                    "error": str(e)
                })
        
        return {"form_results": results}
    
    def analyze_webpage(self, url: str) -> Dict[str, Any]:
        """Analisar estrutura da página web"""
        if not self.driver:
            nav_result = self.navigate_to(url)
            if "error" in nav_result:
                return nav_result
        else:
            self.driver.get(url)
        
        try:
            analysis = {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "meta_description": "",
                "headings": [],
                "links": [],
                "forms": [],
                "buttons": [],
                "images": []
            }
            
            # Meta description
            try:
                meta = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                analysis["meta_description"] = meta.get_attribute("content")
            except:
                pass
            
            # Headings
            for i in range(1, 7):
                headings = self.driver.find_elements(By.TAG_NAME, f"h{i}")
                for h in headings[:5]:  # Limitar a 5 por nível
                    analysis["headings"].append({
                        "level": i,
                        "text": h.text[:100]
                    })
            
            # Links importantes
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links[:10]:  # Primeiros 10 links
                href = link.get_attribute("href")
                text = link.text.strip()
                if href and text:
                    analysis["links"].append({
                        "text": text[:50],
                        "href": href
                    })
            
            # Formulários
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                inputs = form.find_elements(By.TAG_NAME, "input")
                analysis["forms"].append({
                    "action": form.get_attribute("action"),
                    "method": form.get_attribute("method"),
                    "input_count": len(inputs)
                })
            
            # Botões
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons[:5]:
                analysis["buttons"].append({
                    "text": btn.text[:30],
                    "type": btn.get_attribute("type")
                })
            
            return analysis
            
        except Exception as e:
            return {"error": f"Erro na análise: {str(e)}"}
    
    # ============================================================================
    # 3. AUTOMAÇÃO DESKTOP (PYAUTOGUI)
    # ============================================================================
    
    def take_screenshot(self, name: str = None) -> Dict[str, Any]:
        """Capturar screenshot da tela"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = name if name else f"screenshot_{timestamp}"
            filepath = self.free_path / "screenshots" / f"{filename}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            return {
                "success": True,
                "filepath": str(filepath),
                "size": screenshot.size
            }
            
        except Exception as e:
            return {"error": f"Erro ao capturar tela: {str(e)}"}
    
    def click_on_image(self, image_path: str, confidence: float = 0.8) -> Dict[str, Any]:
        """Encontrar e clicar em imagem na tela"""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center)
                
                return {
                    "success": True,
                    "position": center,
                    "message": f"Clicou em imagem: {image_path}"
                }
            else:
                return {"error": f"Imagem não encontrada: {image_path}"}
                
        except Exception as e:
            return {"error": f"Erro ao clicar em imagem: {str(e)}"}
    
    def click_at_position(self, x: int, y: int) -> Dict[str, Any]:
        """Clicar em posição específica da tela"""
        try:
            pyautogui.click(x, y)
            return {
                "success": True,
                "position": (x, y),
                "message": f"Clicou na posição ({x}, {y})"
            }
        except Exception as e:
            return {"error": f"Erro ao clicar: {str(e)}"}
    
    def type_text(self, text: str, interval: float = 0.1) -> Dict[str, Any]:
        """Digitar texto com intervalo entre teclas"""
        try:
            pyautogui.write(text, interval=interval)
            return {
                "success": True,
                "text_typed": text,
                "char_count": len(text)
            }
        except Exception as e:
            return {"error": f"Erro ao digitar: {str(e)}"}
    
    def press_key_combination(self, *keys) -> Dict[str, Any]:
        """Pressionar combinação de teclas"""
        try:
            pyautogui.hotkey(*keys)
            return {
                "success": True,
                "keys_pressed": " + ".join(keys)
            }
        except Exception as e:
            return {"error": f"Erro ao pressionar teclas: {str(e)}"}
    
    # ============================================================================
    # 4. NAVEGAÇÃO INTELIGENTE DE ARQUIVOS
    # ============================================================================
    
    def open_folder(self, folder_path: str) -> Dict[str, Any]:
        """Abrir pasta no Windows Explorer"""
        try:
            if os.path.exists(folder_path):
                subprocess.run(['explorer', folder_path], check=True)
                return {
                    "success": True,
                    "folder_opened": folder_path
                }
            else:
                return {"error": f"Pasta não encontrada: {folder_path}"}
        except Exception as e:
            return {"error": f"Erro ao abrir pasta: {str(e)}"}
    
    def search_files(self, search_path: str, pattern: str = "*") -> Dict[str, Any]:
        """Buscar arquivos em diretório"""
        try:
            search_dir = Path(search_path)
            if not search_dir.exists():
                return {"error": f"Diretório não encontrado: {search_path}"}
            
            files_found = []
            for file_path in search_dir.rglob(pattern):
                if file_path.is_file():
                    files_found.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
            
            return {
                "success": True,
                "search_path": search_path,
                "pattern": pattern,
                "files_found": len(files_found),
                "files": files_found[:50]  # Limitar a 50 resultados
            }
            
        except Exception as e:
            return {"error": f"Erro na busca: {str(e)}"}
    
    # ============================================================================
    # 5. AUTOMAÇÃO COMPLETA (COMBINA TODAS AS FUNCIONALIDADES)
    # ============================================================================
    
    def auto_research_and_save(self, topic: str, num_sites: int = 3) -> Dict[str, Any]:
        """Pesquisar tópico + abrir sites + analisar + salvar tudo"""
        try:
            # 1. Buscar na internet
            search_results = self.search_and_analyze(topic, analyze_pages=False)
            if "error" in search_results:
                return search_results
            
            # 2. Iniciar browser
            browser_result = self.start_browser()
            if "error" in browser_result:
                return browser_result
            
            # 3. Visitar e analisar cada site
            detailed_analysis = []
            
            for i, result in enumerate(search_results["results"][:num_sites]):
                site_analysis = {
                    "position": result["position"],
                    "title": result["title"],
                    "url": result["url"]
                }
                
                # Navegar para o site
                nav_result = self.navigate_to(result["url"])
                if "success" in nav_result:
                    # Capturar screenshot
                    screenshot_result = self.take_screenshot(f"{topic}_site_{i+1}")
                    site_analysis["screenshot"] = screenshot_result.get("filepath", "")
                    
                    # Analisar página
                    page_analysis = self.analyze_webpage(result["url"])
                    site_analysis["analysis"] = page_analysis
                    
                    # Aguardar um pouco
                    time.sleep(2)
                
                detailed_analysis.append(site_analysis)
            
            # 4. Salvar relatório completo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report = {
                "topic": topic,
                "timestamp": timestamp,
                "search_results": search_results,
                "detailed_analysis": detailed_analysis,
                "summary": {
                    "total_sites_analyzed": len(detailed_analysis),
                    "screenshots_taken": len([a for a in detailed_analysis if a.get("screenshot")])
                }
            }
            
            report_file = self.free_path / "research" / f"complete_research_{topic.replace(' ', '_')}_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # 5. Fechar browser
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            return {
                "success": True,
                "report_file": str(report_file),
                "sites_analyzed": len(detailed_analysis),
                "report": report
            }
            
        except Exception as e:
            if self.driver:
                self.driver.quit()
                self.driver = None
            return {"error": f"Erro na pesquisa completa: {str(e)}"}
    
    def smart_form_fill(self, url: str, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Navegar + encontrar formulário + preencher automaticamente"""
        try:
            # 1. Navegar para URL
            nav_result = self.navigate_to(url)
            if "error" in nav_result:
                return nav_result
            
            # 2. Aguardar carregamento
            time.sleep(2)
            
            # 3. Preencher formulário
            form_result = self.fill_form(form_data)
            
            # 4. Capturar screenshot do resultado
            screenshot_result = self.take_screenshot("form_filled")
            
            return {
                "success": True,
                "navigation": nav_result,
                "form_filling": form_result,
                "screenshot": screenshot_result
            }
            
        except Exception as e:
            return {"error": f"Erro no preenchimento inteligente: {str(e)}"}
    
    def cleanup(self):
        """Limpeza ao finalizar"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


# ============================================================================
# FUNÇÕES DE COMANDO PARA INTEGRAÇÃO COM CHAINLIT
# ============================================================================

# Instância global do master de automação
automation_master = None

def get_automation_master() -> AutomationMaster:
    """Obter instância global do automation master"""
    global automation_master
    if automation_master is None:
        automation_master = AutomationMaster()
    return automation_master

def handle_auto_search(query: str) -> Dict[str, Any]:
    """Comando: /auto_search <query>"""
    master = get_automation_master()
    return master.search_and_analyze(query)

def handle_auto_browse(url: str) -> Dict[str, Any]:
    """Comando: /auto_browse <url>"""
    master = get_automation_master()
    return master.navigate_to(url)

def handle_auto_click(selector: str, selector_type: str = "css") -> Dict[str, Any]:
    """Comando: /auto_click <selector> [type]"""
    master = get_automation_master()
    return master.click_element(selector, selector_type)

def handle_auto_screenshot(name: str = None) -> Dict[str, Any]:
    """Comando: /auto_screenshot [name]"""
    master = get_automation_master()
    return master.take_screenshot(name)

def handle_auto_research(topic: str, num_sites: int = 3) -> Dict[str, Any]:
    """Comando: /auto_research <topic> [num_sites]"""
    master = get_automation_master()
    return master.auto_research_and_save(topic, num_sites)

def handle_auto_type(text: str) -> Dict[str, Any]:
    """Comando: /auto_type <text>"""
    master = get_automation_master()
    return master.type_text(text)

def handle_auto_keys(*keys) -> Dict[str, Any]:
    """Comando: /auto_keys <key1> <key2> ..."""
    master = get_automation_master()
    return master.press_key_combination(*keys)

def handle_auto_folder(folder_path: str) -> Dict[str, Any]:
    """Comando: /auto_folder <path>"""
    master = get_automation_master()
    return master.open_folder(folder_path)

# Mapa de comandos para integração
AUTOMATION_COMMANDS = {
    "auto_search": handle_auto_search,
    "auto_browse": handle_auto_browse, 
    "auto_click": handle_auto_click,
    "auto_screenshot": handle_auto_screenshot,
    "auto_research": handle_auto_research,
    "auto_type": handle_auto_type,
    "auto_keys": handle_auto_keys,
    "auto_folder": handle_auto_folder
}