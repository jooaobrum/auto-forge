import hashlib

from churn import tracing


def test_lock_hash(tmp_path):
    lock = tmp_path / "x.lock"
    lock.write_bytes(b"pinned")
    assert tracing.lock_hash(str(lock)) == hashlib.sha256(b"pinned").hexdigest()
