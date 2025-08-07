"""
HASHIRU 6.1 - Apply All Fixes Script
Aplica todas as correções críticas em uma execução
"""
import sys
import json
import time
import subprocess  
from pathlib import Path


def run_cmd(cmd: str) -> tuple[bool, str]:
    """Execute command and return success, output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, f"Error: {e}"


def main():
    print("🔥 HASHIRU 6.1 - APPLYING ALL FIXES")
    print("=" * 50)
    
    fixes_applied = 0
    
    # 1. Test current syntax
    print("\n1️⃣ Testing current syntax...")
    success, output = run_cmd("python -c \"import main_agent; print('✅ Import successful')\"")
    if not success:
        print(f"⚠️  Current syntax issues detected:\n{output}")
    else:
        print("✅ Current syntax is clean")
    
    # 2. Backup current main_agent.py
    print("\n2️⃣ Creating backup...")
    main_file = Path("main_agent.py")
    if main_file.exists():
        backup_file = Path(f"main_agent_backup_{int(time.time())}.py")
        backup_file.write_text(main_file.read_text())
        print(f"💾 Backup created: {backup_file}")
        fixes_applied += 1
    
    # 3. Apply fixes to main_agent.py
    print("\n3️⃣ Applying main_agent.py fixes...")
    current_content = main_file.read_text()
    
    fixes = [
        # Fix duplicate Optional import
        ("from typing import Dict, List, Any, Optional, Optional", 
         "from typing import Dict, List, Any, Optional"),
        
        # Fix HTTP client concatenation bug
        ("self.http: Optional[httpx.AsyncClient] = httpx.AsyncClient()# Engine de auto-modificação (opcional)",
         "self.http: Optional[httpx.AsyncClient] = httpx.AsyncClient()\n        \n        # Engine de auto-modificação (opcional)"),
        
        # Fix regex pattern (raw string)
        ('pattern = re.compile(r"(?ms)^\\s*(\\\/[a-z][\\w:-]*(?:[^\\n<]*?))\\s*(?:<<<(.*?)>>>|)\\s*$")',
         'pattern = re.compile(r"(?ms)^\\s*(\\/[a-z][\\w:-]*(?:[^\\n<]*?))\\s*(?:<<<(.*?)>>>|)\\s*$")'),
    ]
    
    for old, new in fixes:
        if old in current_content:
            current_content = current_content.replace(old, new)
            print(f"  ✅ Applied fix: {old[:50]}...")
            fixes_applied += 1
    
    # Write fixed content
    main_file.write_text(current_content)
    
    # 4. Test fixed syntax
    print("\n4️⃣ Testing fixed syntax...")
    success, output = run_cmd("python -c \"import main_agent; print('✅ Fixed import successful')\"")
    if success:
        print("✅ All syntax issues resolved!")
        fixes_applied += 1
    else:
        print(f"❌ Still has issues:\n{output}")
    
    # 5. Test Chainlit startup
    print("\n5️⃣ Testing Chainlit startup (5 seconds)...")
    success, output = run_cmd("timeout 5 chainlit run main_agent.py --port 8081 --host 127.0.0.1")
    if "Your app is available" in output:
        print("✅ Chainlit starts successfully!")
        fixes_applied += 1
    else:
        print(f"⚠️  Chainlit startup issues:\n{output[:200]}...")
    
    # 6. Apply security policies if fs.py exists
    fs_file = Path("tools/fs.py")
    if fs_file.exists():
        print("\n6️⃣ Checking filesystem security...")
        content = fs_file.read_text()
        if "is_write_path_allowed" not in content:
            print("⚠️  Security policies not integrated in tools/fs.py")
            print("   → Need to integrate security policies manually")
        else:
            print("✅ Security policies already integrated")
            fixes_applied += 1
    
    # 7. Create artifacts directory
    print("\n7️⃣ Ensuring artifacts directory...")
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    print(f"✅ Artifacts directory ready: {artifacts_dir}")
    fixes_applied += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 FIXES APPLIED: {fixes_applied}")
    print("✅ Ready to test with commands:")
    print("   /self:status")
    print("   /self:analyze main_agent.py") 
    print("   /write tools/test.txt <<<Hello>>")
    print("=" * 50)
    
    return fixes_applied


if __name__ == "__main__":
    import time
    main()