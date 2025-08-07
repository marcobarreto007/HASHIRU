import psutil
from typing import Optional

def list_processes(sort_by: str = 'cpu', top_n: int = 10) -> str:
    """
    Lista os processos do sistema, ordenados por uso de CPU ou memória.
    Handler para /ps [--top N] [--sort cpu|mem].
    """
    if sort_by not in ['cpu', 'mem']:
        return "Invalid sort key. Use 'cpu' or 'mem'."

    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                # cpu_percent pode precisar de um intervalo para ser mais preciso na primeira chamada
                p.cpu_percent(interval=0.01)
                procs.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Segunda chamada para obter valores de CPU mais estáveis
        for p in procs:
            try:
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                p.info['cpu_percent'] = 0 # Zera se o processo sumiu

        sort_key = 'cpu_percent' if sort_by == 'cpu' else 'memory_percent'
        sorted_procs = sorted(procs, key=lambda p: p.info[sort_key], reverse=True)

        output = [f"Top {top_n} processes sorted by {sort_by.upper()} usage:"]
        output.append("PID    | Name                 | %CPU   | %MEM")
        output.append("------ | -------------------- | ------ | ------")

        for p in sorted_procs[:top_n]:
            name = p.info['name'] or 'N/A'
            cpu = p.info['cpu_percent']
            mem = p.info['memory_percent']
            output.append(f"{p.info['pid']:<6} | {name[:20]:<20} | {cpu:5.2f} | {mem:5.2f}")

        return "\n".join(output)

    except Exception as e:
        return f"Error listing processes: {e}"


def kill_process(pid: int) -> str:
    """
    Termina um processo pelo seu PID.
    Handler para /kill CONFIRMO <PID>.
    """
    try:
        p = psutil.Process(pid)
        p_name = p.name()
        p.terminate() # Tenta terminar graciosamente
        try:
            p.wait(timeout=3) # Espera até 3s
            return f"Process {pid} ({p_name}) terminated successfully."
        except psutil.TimeoutExpired:
            p.kill() # Força o encerramento
            return f"Process {pid} ({p_name}) did not respond, was killed."
    except psutil.NoSuchProcess:
        return f"Error: Process with PID {pid} not found."
    except psutil.AccessDenied:
        return f"Error: Access denied. Cannot terminate process {pid}."
    except Exception as e:
        return f"An unexpected error occurred: {e}"
