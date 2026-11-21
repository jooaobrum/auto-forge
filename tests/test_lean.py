import subprocess
import sys

from conftest import SKILLS

LEAN = SKILLS / "agent-spec-lean"


def test_agent_spec_lean_selftest():
    done = subprocess.run([sys.executable, str(LEAN / "scripts" / "selftest.py")], capture_output=True, text=True,
                          check=False)
    assert done.returncode == 0, done.stdout[-2000:] + done.stderr[-2000:]
    for path in LEAN.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".py", ".json"):
            text = path.read_text()
            assert "skills/tlc-spec-lean" not in text and "tlc-spec-lean/" not in text, path
            assert "name: tlc-spec-lean" not in text, path
