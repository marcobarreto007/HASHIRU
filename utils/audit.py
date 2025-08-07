import os
import json
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'audit_log.jsonl')

def audit_event(event_type: str, details: dict):
    """
    Registra um evento de auditoria em um arquivo de log JSONL.

    Args:
        event_type (str): O tipo de evento (ex: 'tool_used', 'error').
        details (dict): Um dicionário com os detalhes do evento.
    """
    try:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details
        }
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except Exception as e:
        # Em caso de falha no log, imprime o erro para o console
        # para não interromper a execução principal.
        print(f"ERRO DE AUDITORIA: {e}")
