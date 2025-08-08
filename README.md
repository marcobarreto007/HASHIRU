
# 🌟 Superezio Enterprise Edition v6.0.0

**Superezio** é um Sistema Cognitivo de Automação Multi-Modal de nível empresarial, projetado para alta performance, resiliência e observabilidade. Construído com uma arquitetura assíncrona e otimizado para hardware com múltiplas GPUs, o Superezio atua como um assistente de IA autônomo capaz de executar tarefas complexas, analisar dados e gerenciar a si mesmo de forma inteligente.

Este projeto é o resultado de 7 meses de desenvolvimento, focado em trazer práticas de engenharia de software de nível de produção para o mundo dos agentes de IA.

---

## 💎 Características Principais (Enterprise Grade)

O Superezio foi construído sobre uma fundação de princípios de software robustos:

- **Arquitetura Async-First:** Totalmente assíncrono para máxima performance e concorrência.
- **Otimização Multi-GPU:** Gerenciamento e balanceamento de carga de modelos de IA em múltiplas GPUs.
- **Observabilidade Completa:**
  - **Logging Estruturado:** Logs em formato JSON com IDs de correlação para rastreamento distribuído.
  - **Health Checks:** Endpoints para monitorar a "saúde" do sistema em tempo real.
  - **Métricas:** Coleta de métricas de performance por sessão.
- **Resiliência e Estabilidade:**
  - **Circuit Breakers:** Proteção contra falhas em serviços externos, evitando o colapso do sistema.
  - **Rate Limiting:** Controle de uso para prevenir sobrecarga e abuso.
- **Performance Otimizada:**
  - **Cache Inteligente:** Sistema de cache com TTL (Time-To-Live) e gerenciamento de memória para respostas rápidas.
  - **Streaming de Respostas:** A interface de usuário recebe respostas em tempo real, melhorando a experiência.
- **Segurança:** Sanitização de inputs para prevenir ataques de injeção.
- **Gerenciamento de Sessão:** Persistência de estado e contexto durante a sessão do usuário.

---

## 🛠️ Tech Stack

- **Core Framework:** Python 3.12+
- **Interface de Usuário:** Chainlit
- **Modelos de IA:** Arquitetura para múltiplos modelos (ex: Llama 3.1, Qwen 2.5, DeepSeek Coder) gerenciados via Ollama ou similar.
- **Bibliotecas Principais:** `asyncio`, `logging`, `fastapi` (indiretamente via Chainlit).

---

## 🚀 Instalação e Execução

Siga os passos abaixo para configurar e executar o Superezio em seu ambiente local.

### 1. Pré-requisitos

- Python 3.12 ou superior
- Git
- (Opcional, mas recomendado) Um ou mais GPUs NVIDIA com CUDA instalado.

### 2. Clone o Repositório

```bash
git clone https://github.com/marcobarreto007/HASHIRU.git
cd HASHIRU
```

### 3. Crie e Ative um Ambiente Virtual

# Para Windows
python -m venv venv
.\venv\Scripts\activate

# Para macOS/Linux
source venv/bin/activate
```

### 4. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 5. Execute o Superezio

O sistema é iniciado através do Chainlit. O comando `-w` (watch) reinicia o servidor automaticamente quando você faz alterações no código.

```bash
chainlit run main.py -w
```

Após a execução, você pode acessar a interface do Superezio no seu navegador, geralmente em `http://localhost:8000`.

---

## 🤖 Comandos Disponíveis

O Superezio pode ser controlado tanto por linguagem natural quanto por comandos específicos para maior precisão.

### Automação Inteligente
- `/auto_status` - Exibe um status completo do sistema, hardware e modelos de IA.
- `/auto_health` - Executa um diagnóstico de saúde em todos os componentes internos.
- `/auto_research <tópico>` - Inicia uma pesquisa aprofundada e multi-fonte sobre um tópico.
- `/auto_search <termo>` - Realiza uma busca avançada na web.
- `/auto_screenshot` - Captura a tela e realiza uma análise OCR do conteúdo.

### Análise e Geração
- `/analyze <dados>` - Realiza uma análise avançada sobre os dados fornecidos.
- `/plan <objetivo>` - Cria um plano estratégico detalhado para um objetivo.
- `/code <especificação>` - Gera código otimizado a partir de uma especificação.
- `/debug <problema>` - Analisa um problema e propõe soluções.

### Sistema e Métricas
- `/config` - Exibe as configurações enterprise atuais.
- `/metrics` - Mostra as métricas de performance da sessão atual.
- `/session` - Apresenta todas as informações da sessão do usuário.
- `/help` - Lista todos os comandos disponíveis.

---

## ✍️ Autor

Desenvolvido com dedicação por **Marco Barreto**.
