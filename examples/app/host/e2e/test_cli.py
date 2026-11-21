import subprocess
import sys


def sum_of(*args: str) -> str:
    done = subprocess.run([sys.executable, "-m", "app.cli", *args], capture_output=True, text=True, check=True)
    return done.stdout.strip()


def test_user_sums_two_numbers():
    assert sum_of("2", "3") == "5"


def test_user_sums_nothing():
    assert sum_of() == "0"
