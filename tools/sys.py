import platform
import psutil
import socket
import os
from utils.format import fmt_bytes

def get_system_info() -> str:
    """
    Coleta e formata informações detalhadas do sistema, hardware e usuário.
    Handler para o comando /sysinfo.
    """
    try:
        # --- Basic System Info ---
        uname = platform.uname()
        info = ["System Info"]
        info.append(f"  - OS Platform: {uname.system} {uname.release} (Version: {uname.version})")
        info.append(f"  - Architecture: {uname.machine} ({platform.architecture()[0]})")
        info.append(f"  - Processor: {uname.processor}")
        info.append(f"  - Hostname: {socket.gethostname()}")
        try:
            user = os.getlogin()
            info.append(f"  - Running as User: {user}")
        except OSError:
            info.append("  - Running as User: Not available")

        # --- CPU Info ---
        info.append(f"\nCPU Info")
        cpu_freq = psutil.cpu_freq()
        info.append(f"  - Physical Cores: {psutil.cpu_count(logical=False)}")
        info.append(f"  - Logical Cores: {psutil.cpu_count(logical=True)}")
        if cpu_freq:
            info.append(f"  - Max Frequency: {cpu_freq.max:.2f} Mhz")
            info.append(f"  - Current Frequency: {cpu_freq.current:.2f} Mhz")
        info.append(f"  - Total CPU Usage: {psutil.cpu_percent(interval=1)}%")

        # --- Memory Info ---
        mem = psutil.virtual_memory()
        info.append(f"\nMemory (RAM)")
        info.append(f"  - Total: {fmt_bytes(mem.total)}")
        info.append(f"  - Available: {fmt_bytes(mem.available)}")
        info.append(f"  - Used: {fmt_bytes(mem.used)} ({mem.percent}%)")

        # --- Disk Info ---
        info.append(f"\nDisk Partitions")
        partitions = psutil.disk_partitions()
        for p in partitions:
            try:
                usage = psutil.disk_usage(p.mountpoint)
                info.append(f"  - Device: {p.device} ({p.fstype}) at {p.mountpoint}")
                info.append(f"    - Size: {fmt_bytes(usage.total)}")
                info.append(f"    - Used: {fmt_bytes(usage.used)} ({usage.percent}%)")
                info.append(f"    - Free: {fmt_bytes(usage.free)}")
            except (FileNotFoundError, PermissionError) as e:
                info.append(f"  - Could not inspect {p.mountpoint}: {e}")
        
        return "\n".join(info)

    except Exception as e:
        return f"Error collecting system info: {e}"

# Exemplo de como registrar (a lógica real está no __init__.py do tools)
# from tools.registry import register
# register("/sysinfo", get_system_info)
