@echo off
setlocal EnableDelayedExpansion

REM Navigate to script directory
cd /d "%~dp0"

echo.
echo [SUPEREZIO] Corrigindo encoding e formatacao do CSS...
echo.

REM Create public directory if not exists
if not exist public mkdir public

REM Backup existing CSS
if exist public\superezio.css (
    copy public\superezio.css public\superezio.css.backup
    echo ✅ Backup criado: public\superezio.css.backup
)

REM Create properly formatted CSS with correct encoding
powershell -NoProfile -ExecutionPolicy Bypass -Command "$content = @'
/* 🎨 public/superezio.css - HUD Vitrificado v2.1 */
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');

/* ========================================
   CSS VARIABLES - HUD Color Palette
======================================== */
:root {
  --bg: #0A121F;
  --glass: rgba(20, 35, 60, 0.65);
  --accent-cyan: #64FFDA;
  --primary-orange: #FF6B35;
  --text-primary: #CCD6F6;
  --text-secondary: #8892B0;
  --border-glow: rgba(100, 255, 218, 0.25);
  --shadow-orange: rgba(255, 107, 53, 0.6);
}

/* ========================================
   BASE LAYOUT & TYPOGRAPHY
======================================== */
html, body {
  background: var(--bg);
  color: var(--text-primary);
  font-family: 'Roboto Mono', monospace;
  margin: 0;
  padding: 0;
  min-height: 100vh;
}

* {
  box-sizing: border-box;
}

/* ========================================
   ANIMATIONS & TRANSITIONS
======================================== */
@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(15px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

@keyframes pulse {
  0%, 100% { 
    transform: scale(1); 
  }
  50% { 
    transform: scale(1.05); 
  }
}

@keyframes slideIn {
  from { 
    transform: translateX(-20px); 
    opacity: 0; 
  }
  to { 
    transform: translateX(0); 
    opacity: 1; 
  }
}

/* ========================================
   MAIN CONTAINER - GLASSMORPHISM
======================================== */
#root .main {
  background: var(--glass) !important;
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-glow);
  border-radius: 12px;
  animation: fadeIn 0.6s ease-out;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* ========================================
   TYPOGRAPHY - ENHANCED HEADERS
======================================== */
h1, h2, h3, h4, h5, h6 {
  color: var(--accent-cyan) !important;
  text-shadow: 0 0 8px rgba(100, 255, 218, 0.5);
  font-weight: 700;
  margin-bottom: 1rem;
  animation: slideIn 0.5s ease-out;
}

h1 {
  font-size: 2.5rem;
  background: linear-gradient(135deg, var(--accent-cyan), var(--primary-orange));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

h2 {
  font-size: 2rem;
  border-bottom: 2px solid var(--border-glow);
  padding-bottom: 0.5rem;
}

/* ========================================
   DIAGNOSTIC CONTAINER - SPECIAL STYLING
======================================== */
.diag-container {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-glow);
  border-radius: 10px;
  padding: 1.25rem;
  margin: 1rem 0;
  backdrop-filter: blur(5px);
  position: relative;
  overflow: hidden;
}

.diag-container::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, var(--accent-cyan), var(--primary-orange));
  border-radius: 12px;
  z-index: -1;
  opacity: 0.1;
}

/* ========================================
   STATUS INDICATORS
======================================== */
.status-online,
.status-active,
.status-stable {
  color: var(--accent-cyan);
  font-weight: bold;
  text-shadow: 0 0 8px var(--accent-cyan);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: rgba(100, 255, 218, 0.1);
  animation: pulse 2s infinite;
}

/* ========================================
   MESSAGE STYLING - ENHANCED
======================================== */
.message:not(.user-message) {
  border-left: 3px solid var(--accent-cyan);
  background: linear-gradient(90deg, rgba(100, 255, 218, 0.06), transparent);
  padding: 1rem;
  margin: 0.5rem 0;
  border-radius: 0 8px 8px 0;
  animation: slideIn 0.3s ease-out;
}

.user-message {
  background: linear-gradient(90deg, transparent, rgba(255, 107, 53, 0.06));
  border-right: 3px solid var(--primary-orange);
  padding: 1rem;
  margin: 0.5rem 0;
  border-radius: 8px 0 0 8px;
}

/* ========================================
   INPUT FIELDS - ENHANCED INTERACTIONS
======================================== */
textarea, input[type="text"] {
  background: rgba(0, 0, 0, 0.35) !important;
  border: 1px solid var(--border-glow) !important;
  color: var(--text-primary) !important;
  caret-color: var(--primary-orange) !important;
  transition: all 0.2s ease-out;
  border-radius: 8px !important;
  padding: 0.75rem !important;
  font-family: 'Roboto Mono', monospace !important;
}

textarea:focus, input[type="text"]:focus {
  border-color: var(--primary-orange) !important;
  box-shadow: 0 0 12px var(--shadow-orange) !important;
  outline: none !important;
  transform: scale(1.02);
}

textarea::placeholder, input::placeholder {
  color: var(--text-secondary) !important;
  opacity: 0.7;
}

/* ========================================
   BUTTONS - NEOBRUTAL DESIGN
======================================== */
button {
  background: var(--primary-orange) !important;
  color: #fff !important;
  font-weight: bold !important;
  font-family: 'Roboto Mono', monospace !important;
  border: none !important;
  border-radius: 6px !important;
  padding: 0.75rem 1.5rem !important;
  transition: all 0.2s ease-out !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer !important;
}

button:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 4px 12px var(--shadow-orange),
    0 0 0 2px rgba(255, 107, 53, 0.3);
  animation: pulse 0.3s ease-out;
}

button:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px var(--shadow-orange);
}

button:disabled {
  opacity: 0.5;
  transform: none !important;
  cursor: not-allowed !important;
}

/* ========================================
   TABLES - DATA VISUALIZATION
======================================== */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border-glow);
}

th {
  background: var(--glass);
  color: var(--accent-cyan);
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

tr:hover {
  background: rgba(100, 255, 218, 0.05);
}

/* ========================================
   CODE BLOCKS - SYNTAX HIGHLIGHTING
======================================== */
pre, code {
  font-family: 'Roboto Mono', monospace !important;
  background: rgba(0, 0, 0, 0.4) !important;
  border: 1px solid var(--border-glow);
  border-radius: 6px;
}

pre {
  padding: 1rem !important;
  overflow-x: auto;
  margin: 1rem 0;
}

code {
  padding: 0.25rem 0.5rem !important;
  font-size: 0.9em;
}

/* ========================================
   SCROLLBARS - CUSTOM STYLING
======================================== */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: var(--bg);
  border-radius: 6px;
}

::-webkit-scrollbar-thumb {
  background: var(--primary-orange);
  border-radius: 6px;
  border: 2px solid var(--bg);
  transition: background 0.2s ease-out;
}

::-webkit-scrollbar-thumb:hover {
  background: #ff8659;
}

::-webkit-scrollbar-corner {
  background: var(--bg);
}

/* ========================================
   LOADING & STATUS INDICATORS
======================================== */
.loading {
  position: relative;
}

.loading::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  margin: auto;
  border: 2px solid transparent;
  border-top: 2px solid var(--accent-cyan);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ========================================
   RESPONSIVE DESIGN
======================================== */
@media (max-width: 768px) {
  #root .main {
    margin: 0.5rem;
    border-radius: 8px;
  }
  
  h1 {
    font-size: 2rem;
  }
  
  .diag-container {
    padding: 1rem;
  }
  
  button {
    padding: 0.5rem 1rem !important;
    font-size: 0.9rem !important;
  }
}

/* ========================================
   ACCESSIBILITY IMPROVEMENTS
======================================== */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Focus indicators for keyboard navigation */
button:focus,
textarea:focus,
input:focus {
  outline: 2px solid var(--accent-cyan) !important;
  outline-offset: 2px;
}

/* ========================================
   UTILITY CLASSES
======================================== */
.text-cyan { color: var(--accent-cyan); }
.text-orange { color: var(--primary-orange); }
.bg-glass { background: var(--glass); }
.border-glow { border: 1px solid var(--border-glow); }

/* High contrast mode support */
@media (prefers-contrast: high) {
  :root {
    --bg: #000000;
    --text-primary: #ffffff;
    --accent-cyan: #00ffff;
    --primary-orange: #ff6600;
  }
}
'@; [System.IO.File]::WriteAllText('public\superezio.css', $content, [System.Text.Encoding]::UTF8)"

echo.
echo ✅ Arquivo public\superezio.css recriado com encoding UTF-8 correto!
echo.
echo Verificando tamanho do arquivo:
dir public\superezio.css
echo.
echo Primeiras linhas do arquivo:
powershell -Command "Get-Content 'public\superezio.css' -Encoding UTF8 | Select-Object -First 10"
echo.
pause