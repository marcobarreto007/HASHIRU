# Superezio Enterprise - Arquitetura de Monitoramento de GPU

Este documento detalha a arquitetura do sistema de gerenciamento e monitoramento de hardware, focado em GPUs NVIDIA, implementado no projeto `superezio_enterprise`.

## 1. Visão Geral

O objetivo deste sistema é mover de uma simulação para um gerenciamento de hardware real e em tempo real. O `HardwareManager` agora interage diretamente com os drivers da NVIDIA para descobrir, monitorar e alocar recursos de GPU de forma inteligente. Isso é essencial para aplicações de IA e Machine Learning que dependem de uso eficiente de VRAM e poder computacional.

## 2. Dependência Principal

- **Biblioteca**: `nvidia-ml-py`
- **Descrição**: Este pacote fornece os bindings Python para a **NVIDIA Management Library (NVML)**, que é uma API C para monitorar e gerenciar GPUs NVIDIA. É a mesma biblioteca que alimenta a ferramenta `nvidia-smi`.
- **Instalação**: A dependência foi adicionada ao `requirements.txt`.

## 3. Arquitetura do `HardwareManager`

O `HardwareManager` foi completamente redesenhado e opera como um singleton thread-safe com os seguintes componentes:

### 3.1. Inicialização e Descoberta Automática

- Na inicialização, o `HardwareManager` chama `nvmlInit()`.
- Ele detecta automaticamente o número de GPUs NVIDIA disponíveis no sistema (`nvmlDeviceGetCount()`).
- Se nenhuma GPU for encontrada, ele emite um aviso e opera em um modo degradado onde nenhuma alocação pode ser feita.
- Para cada GPU descoberta, ele obtém e armazena um *handle*, que é um ponteiro para a GPU usado em todas as operações subsequentes.

### 3.2. Monitoramento em Background

- Para evitar que chamadas de monitoramento bloqueiem o loop de eventos principal da aplicação, o `HardwareManager` inicia uma **thread de monitoramento dedicada** (`_monitor_loop`).
- Esta thread executa um loop contínuo que, a cada `gpu_monitoring_interval_seconds` (configurável em `config.py`), chama a função `update_all_gpu_states()`.
- A função `update_all_gpu_states()` coleta as seguintes métricas para cada GPU:
  - **Uso de Memória (VRAM)**: Total, livre e usada (em MB).
  - **Utilização do Núcleo da GPU**: Em porcentagem (%).
  - **Temperatura**: Em graus Celsius (°C).
  - **Consumo de Energia**: Em Watts (W).
- Os dados coletados são armazenados em um dicionário de `GpuState` (um dataclass), que fornece um snapshot consistente e thread-safe do estado das GPUs.

### 3.3. Lógica de Alocação Inteligente

A função `assign_model_to_gpu` foi aprimorada para tomar decisões baseadas em dados reais:

- **Input**: Recebe o nome de um modelo e, crucialmente, a **VRAM estimada que ele requer** (`required_vram_mb`).
- **Processo de Decisão**:
  1. Verifica se o modelo já está alocado.
  2. Itera sobre os estados mais recentes de todas as GPUs (obtidos pela thread de monitoramento).
  3. Filtra as GPUs que possuem **VRAM livre suficiente** para atender à requisição.
  4. Dentre as candidatas, seleciona aquela com a **menor utilização de núcleo (%)** como critério de desempate.
  5. Se nenhuma GPU puder atender à requisição, a alocação falha e um erro é logado.
- **Output**: Retorna o ID da GPU alocada ou `None` em caso de falha.

### 3.4. Liberação e Desligamento

- A função `release_model` remove um modelo das alocações, permitindo que outros modelos usem os recursos.
- A função `shutdown` é crucial: ela para a thread de monitoramento e chama `nvmlShutdown()` para liberar todos os recursos da NVML de forma limpa.

## 4. Integração com Outros Módulos

- **HealthManager**: Um novo health check (`gpu_status`) foi adicionado. Ele verifica se as GPUs estão acessíveis e se suas temperaturas estão dentro de limites seguros (atualmente < 90°C), marcando o sistema como `UNHEALTHY` em caso de superaquecimento.
- **main.py**: O fluxo de demonstração foi atualizado para refletir o novo sistema. Ele tenta alocar modelos com diferentes requisitos de VRAM e imprime um relatório ao vivo do estado das GPUs no console, mostrando a eficácia do monitoramento.

## 5. Como Usar

1.  **Instale as dependências**: `pip install -r requirements.txt`.
2.  **Execute a aplicação**: `python -m superezio_enterprise.main`.
3.  **Observe o Console**: O log mostrará a descoberta das GPUs, o processo de alocação de modelos e um relatório de status ao vivo impresso a cada 5 segundos durante a demonstração.
