# Chrono Genesis Lock Execution Window

This supplement clarifies the temporal gate logic that protects SHAARK unlock sequences.

```python
import hashlib
import hmac
import time

IDENTITY = "..."
GLYPH = "..."
EMOTION = "..."
SECRET = "..."
KNIGHT_KEY = b"..."

def knights_ethical_check(identity: str, token_hex: str, beneficiary: str, deadline_unix: int) -> bool:
    msg = f"{identity}|{beneficiary}|{deadline_unix}".encode()
    expected = hmac.new(KNIGHT_KEY, msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, (token_hex or "").lower())

def chrono_genesis_lock(deadline_unix: int, delta_t_seconds: int = 0) -> bool:
    now = int(time.time())
    deadline = int(deadline_unix)
    window = max(int(delta_t_seconds or 0), 0)
    window_start = deadline - window
    return window_start <= now <= deadline

def shaark_unlock(identity, glyph, emotion, secret, delta_t_seconds, knight_token_hex, beneficiary, deadline_unix) -> bool:
    if (identity, glyph, emotion, secret) != (IDENTITY, GLYPH, EMOTION, SECRET):
        return False
    if not chrono_genesis_lock(deadline_unix):
        return False
    if not chrono_genesis_lock(deadline_unix, delta_t_seconds):
        return False
    return knights_ethical_check(identity, knight_token_hex, beneficiary, deadline_unix)

def make_knight_token(identity, beneficiary, deadline_unix) -> str:
    msg = f"{identity}|{beneficiary}|{deadline_unix}".encode()
    return hmac.new(KNIGHT_KEY, msg, hashlib.sha256).hexdigest()
```

`delta_t_seconds` expands the valid window that precedes the absolute `deadline_unix`. When the SHAARK operator supplies a
positive window, `chrono_genesis_lock` only authorizes execution if the current time falls between
`deadline_unix - delta_t_seconds` and the deadline itself. Leaving the parameter at its default `0` replicates the original
point-in-time guard. This keeps the release sequence tightly coupled to its scheduled activation while preserving the Knights'
ethical gate enforced by `knights_ethical_check`.

**Author:** Brendon Joseph Kelly
