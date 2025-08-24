# 🔗 HASHIRU/SUPEREZIO - Mapeamento de Relacionamentos entre Componentes

## 🎯 Mapeamento de Dependências dos Arquivos Principais

### 📋 **main.py** (Entry Point Enterprise)
```python
# Dependências principais:
├── chainlit as cl                           # UI Framework
├── superezio_enterprise.config.settings    # Enterprise Config  
├── superezio_enterprise.logging_setup      # Structured Logging
├── superezio_enterprise.correlation        # Correlation IDs
├── superezio_enterprise.cache              # Cache System
├── superezio_enterprise.rate_limiter       # Rate Limiting
├── superezio_enterprise.circuit_breaker    # Circuit Breakers
├── superezio_enterprise.session_manager    # Session Management
├── superezio_enterprise.health_manager     # Health Monitoring
├── superezio_enterprise.hardware           # GPU Management
├── superezio_enterprise.commands           # Command System
└── superezio_enterprise.streamer           # Response Streaming

# Funcionalidades:
- 🚀 Enterprise-grade entry point
- 📊 Full observability stack
- 🔄 Async request handling
- 🛡️ Security and rate limiting
- 📈 Real-time metrics
```

### 🤖 **main_agent_superezio.py** (Core Agent)
```python
# Dependências principais:
├── chainlit as cl                    # UI Integration
├── autonomous_config                 # Modern Configuration
├── asyncio                          # Async Operations
├── logging                          # Structured Logging
├── json, re, time                   # Core utilities
└── typing                           # Type hints

# Componentes internos:
├── SuperEzioCommandRegistry         # Dynamic command loading
├── PerformanceMonitor              # Performance tracking
├── SuperEzioAgent                  # Main agent class
└── Command handlers                # Individual command processors

# Funcionalidades:
- 🎯 Dynamic command registration
- 📊 Performance monitoring
- 🔄 Async command execution
- 🧠 LLM integration
- 🛠️ Tool orchestration
```

### ⚙️ **config.py** (Basic Configuration)
```python
# Sistema de configuração básico:
├── os, pathlib                      # Path management
├── dataclasses                      # Configuration structures
├── typing                           # Type safety
└── dotenv                           # Environment variables

# Configurações exportadas:
├── ROOT, DATA_DIR, LOGS_DIR         # Directory paths
├── HOST, PORT                       # Server config
├── TIMEOUT_DEFAULT                  # Default timeouts
├── AUDIT_ENABLED                    # Audit settings
├── DELETE_MODE                      # File deletion mode
├── PY_UNSAFE_DEFAULT               # Python execution safety
└── EXEC_ALLOWLIST                  # Allowed commands

# Utilizado por:
- main_agent_superezio.py
- tools/self_commands.py
- Various utility modules
```

### 🔧 **autonomous_config.py** (Modern Configuration)
```python
# Sistema de configuração avançado:
├── os, pathlib                      # System integration
├── dataclasses, field              # Modern Python patterns
├── typing                           # Type safety
└── @dataclass decorators           # Clean configuration

# Estruturas principais:
├── OllamaConfig                     # LLM configuration
├── SecurityConfig                   # Security policies
├── EngineConfig                     # Self-modification engine
├── SystemConfig                     # System-level settings
└── Config                           # Main configuration class

# Features:
- 🎯 Type-safe configuration
- 🔒 Security policies
- 🤖 Multi-model LLM support
- 🔄 Self-modification controls
- 🌍 Environment-based config
```

---

## 🏗️ **API Layer** - Component Relationships

### 🎯 **api/orchestrator.py** (Expert Orchestration)
```python
# Core do sistema de experts:
├── importlib                        # Dynamic loading
├── os                              # File system operations
├── asyncio                         # Async operations
├── api.llm_client                  # LLM communication
├── api.experts.base                # Expert base classes
└── api.router                      # Expert routing

# Fluxo de dados:
User Query → Orchestrator → Dynamic Expert Loading → 
Expert Execution → LLM Calls → Result Aggregation → Response

# Experts gerenciados:
├── 📊 Fundamental Analyst
├── 💹 Technical Analyst  
├── 🎭 Sentiment Analyst
├── 💰 Crypto Analyst
├── 🌍 Macro Analyst
└── ⚠️ Risk Analyst
```

### 🔗 **api/llm_client.py** (LLM Interface)
```python
# Cliente principal para LLMs:
├── httpx                           # Async HTTP client
├── json                            # Data serialization
├── asyncio                         # Async operations
└── typing                          # Type safety

# Integrações:
- 🤖 Ollama API
- 🧠 Multiple LLM models
- ⚡ Async request handling
- 🔄 Error handling and retries
- 📊 Performance monitoring
```

### 🧠 **api/experts/** (AI Specialists)
```python
# Sistema de especialistas:
base.py                             # Base expert class
├── ExpertDefinition               # Expert metadata
├── BaseExpert                     # Common functionality
└── Expert interfaces              # Standardized API

# Especialistas implementados:
fundamental_analyst.py              # 📊 Financial fundamentals
technical_analyst.py                # 💹 Technical analysis
sentiment_analyst.py                # 🎭 Market sentiment
crypto_analyst.py                   # 💰 Cryptocurrency analysis
macro_analyst.py                    # 🌍 Macroeconomic analysis
risk_analyst.py                     # ⚠️ Risk assessment

# Padrão de integração:
Each Expert → LLM Model → Specialized Analysis → Structured Output
```

---

## 🏢 **Enterprise Infrastructure** - Component Map

### 🚀 **superezio_enterprise/main.py**
```python
# Entry point enterprise:
├── asyncio                         # Async runtime
├── logging                         # Structured logging
├── superezio_enterprise.*          # All enterprise modules
└── correlation                     # Request tracking

# Fluxo de inicialização:
1. Setup enterprise logging
2. Initialize hardware manager
3. Configure health checks
4. Start monitoring systems
5. Demo enterprise features
```

### 🏥 **superezio_enterprise/health_manager.py**
```python
# Health monitoring system:
├── asyncio                         # Async health checks
├── psutil                          # System monitoring
├── typing                          # Type definitions
└── dataclasses                     # Health status models

# Health checks registrados:
├── memory_usage                    # Memory monitoring
├── cache_stats                     # Cache performance
├── gpu_health                      # GPU status
└── system_status                   # Overall health

# Integração:
Health Manager ↔ All System Components → Real-time Status
```

### 🖥️ **superezio_enterprise/hardware.py**
```python
# GPU and hardware management:
├── threading                       # Background monitoring
├── dataclasses                     # GPU state models
├── typing                          # Type safety
└── Optional: pynvml                # NVIDIA monitoring

# Funcionalidades:
- 🎮 GPU discovery and monitoring
- 📊 Resource allocation tracking
- 🔄 Load balancing
- 📈 Performance metrics
- ⚡ Real-time status updates
```

### 💾 **superezio_enterprise/cache.py**
```python
# Enterprise caching system:
├── asyncio                         # Async operations
├── time                            # TTL management
├── typing                          # Type definitions
└── Optional: redis                 # Distributed cache

# Cache layers:
├── Memory Cache                    # Fast local access
├── Redis Cache                     # Distributed storage
├── TTL Management                  # Automatic expiration
└── Cache warming                   # Predictive loading
```

---

## 🛠️ **Tools Layer** - Component Architecture

### 🤖 **tools/automation_commands.py**
```python
# Main automation system:
├── tools.web                       # Web automation
├── tools.fs                        # File operations
├── tools.exec                      # Command execution
├── tools.net                       # Network operations
└── utils.audit                     # Audit trail

# Command categories:
├── 🌐 Web automation (Selenium)
├── 📁 File system operations
├── 🔧 System command execution
├── 🐍 Python code execution
├── 🌍 Network operations
└── 📊 Data analysis commands
```

### 🌐 **tools/web.py** (Web Automation)
```python
# Web automation framework:
├── selenium                        # Browser automation
├── beautifulsoup4                  # HTML parsing
├── requests                        # HTTP requests
├── chainlit                        # UI integration
└── utils.security                  # Security validation

# Capabilities:
- 🖱️ Browser control and automation
- 📸 Screenshot capture and OCR
- 🔍 Web scraping and data extraction
- 🔗 Link following and navigation
- 📱 Responsive design testing
```

### 📁 **tools/fs.py** (File System)
```python
# File system operations:
├── pathlib                         # Modern path handling
├── shutil                          # File operations
├── send2trash                      # Safe deletion
├── os                              # OS integration
└── utils.security                  # Path validation

# Operations:
- 📂 Directory management
- 📄 File operations (CRUD)
- 🗑️ Safe file deletion
- 🔍 File search and filtering
- 📊 Directory analysis
```

---

## 🔧 **Utilities Layer** - Support Systems

### 🔍 **utils/audit.py** (Audit System)
```python
# Comprehensive audit trail:
├── datetime                        # Timestamp management
├── json                            # Structured logging
├── pathlib                         # Path operations
└── typing                          # Type definitions

# Audit features:
- 📝 Action logging
- 🔍 Change tracking
- 📊 Usage analytics
- 🔒 Security monitoring
- 📈 Performance tracking
```

### 🛡️ **utils/security.py** (Security Framework)
```python
# Security utilities:
├── pathlib                         # Secure path handling
├── re                              # Pattern matching
├── typing                          # Type safety
└── config                          # Security policies

# Security features:
- 🔒 Input sanitization
- 📁 Path validation
- ✅ Permission checking
- 🛡️ Command validation
- 🔍 Threat detection
```

---

## 🧪 **Testing Infrastructure** - Quality Assurance

### 🧪 **tests/** Structure
```python
# Test organization:
test_main.py                        # Main functionality tests
test_config.py                      # Configuration tests
test_cache.py                       # Cache system tests
test_commands.py                    # Command execution tests
test_hardware.py                    # Hardware manager tests
test_session_manager.py             # Session management tests
test_rate_limiter.py                # Rate limiting tests

# Test patterns:
- 🎯 Unit tests for individual components
- 🔄 Integration tests for workflows
- 🧪 Async test support (pytest-asyncio)
- 🔍 Mock-based testing for external deps
- 📊 Performance and load testing
```

---

## 📊 **Data Flow Patterns**

### 1. **Command Execution Flow**
```
User Input → Chainlit UI → Command Registry → 
Route Detection → Tool Selection → Execution → 
Result Processing → Response Formatting → UI Update
```

### 2. **Expert Analysis Flow**
```
Analysis Request → Orchestrator → Expert Selection → 
LLM Model Selection → Parallel Analysis → 
Result Aggregation → Confidence Scoring → Final Report
```

### 3. **Enterprise Monitoring Flow**
```
System Events → Structured Logging → Correlation IDs → 
Metrics Collection → Health Checks → Alert System → 
Dashboard Updates → Administrative Actions
```

### 4. **Cache Management Flow**
```
Data Request → Cache Key Generation → Cache Lookup → 
Hit: Return Cached Data | Miss: Fetch Fresh Data → 
Update Cache with TTL → Return to Requestor
```

---

## 🔗 **Inter-Component Communication**

### **Event-Driven Patterns**
- Health status changes
- Cache invalidation events
- Command completion notifications
- GPU resource availability

### **Request-Response Patterns**
- LLM API calls
- Expert analysis requests
- File system operations
- Web automation commands

### **Pub-Sub Patterns**
- Metrics collection
- Audit trail logging
- Performance monitoring
- System status updates

---

*Mapeamento gerado em: 2025-01-24*  
*Baseado em análise estática do código HASHIRU/SUPEREZIO v6.0.0*