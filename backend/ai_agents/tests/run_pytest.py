"""
运行pytest测试套件
"""
import sys
import subprocess
from pathlib import Path

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

print("=" * 80)
print("运行AIAgent图功能pytest测试套件")
print("=" * 80)

result = subprocess.run(
    [sys.executable, "-m", "pytest", "ai_agents/tests/test_graph_comprehensive.py", "-v", "--tb=short"],
    cwd=str(backend_dir),
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print("=" * 80)
if result.returncode == 0:
    print("✅ 所有pytest测试通过")
else:
    print(f"❌ 测试失败，退出码: {result.returncode}")
print("=" * 80)

sys.exit(result.returncode)