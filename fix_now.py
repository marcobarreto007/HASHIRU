"""
HASHIRU 6.1 - Simple Fix Script
Corrige problemas criticos sem caracteres especiais
"""
import time
from pathlib import Path


def main():
    print("HASHIRU 6.1 - Simple Fixes")
    print("=" * 30)
    
    main_file = Path("main_agent.py")
    if not main_file.exists():
        print("ERROR: main_agent.py not found!")
        return
    
    try:
        # Read with UTF-8
        print("Reading main_agent.py...")
        content = main_file.read_text(encoding='utf-8')
        original_content = content
        fixes = 0
        
        # Fix 1: Duplicate Optional
        if "Optional, Optional" in content:
            content = content.replace(
                "from typing import Dict, List, Any, Optional, Optional",
                "from typing import Dict, List, Any, Optional"
            )
            print("  Fixed: Duplicate Optional import")
            fixes += 1
        
        # Fix 2: HTTP client bug
        if "httpx.AsyncClient()# Engine" in content:
            content = content.replace(
                "httpx.AsyncClient()# Engine de auto-modificação (opcional)",
                "httpx.AsyncClient()\n        \n        # Engine de auto-modificacao"
            )
            print("  Fixed: HTTP client concatenation")
            fixes += 1
        
        # Fix 3: Replace emojis that cause encoding issues
        emoji_replacements = [
            ("🔧", "[FIX]"),
            ("✅", "[OK]"),
            ("⚠️", "[WARN]"),
            ("🚨", "[ERROR]"),
            ("🎯", "[TARGET]"),
            ("🔥", "[HOT]"),
            ("⚡", "[FAST]"),
            ("💥", "[CRASH]"),
            ("🤖", "[BOT]"),
            ("▶️", "->"),
        ]
        
        for emoji, replacement in emoji_replacements:
            if emoji in content:
                content = content.replace(emoji, replacement)
                fixes += 1
        
        if fixes > 0:
            print("  Replaced emojis with ASCII")
        
        # Save if changes made
        if fixes > 0:
            # Backup
            backup_file = Path(f"main_agent_backup_{int(time.time())}.py")
            backup_file.write_text(original_content, encoding='utf-8')
            print(f"  Backup: {backup_file}")
            
            # Save fixed
            main_file.write_text(content, encoding='utf-8')
            print(f"  Applied {fixes} fixes")
        else:
            print("  No fixes needed")
        
        # Test import
        print("Testing import...")
        import subprocess
        result = subprocess.run([
            "python", "-c", "import main_agent; print('SUCCESS')"
        ], capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0 and "SUCCESS" in result.stdout:
            print("  Import test: PASSED")
            print("\nStatus: READY!")
            print("Run: chainlit run main_agent.py --port 8080")
        else:
            print(f"  Import test: FAILED")
            print(f"  Error: {result.stderr}")
        
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()