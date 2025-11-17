# ============================================================
# BUNDY_RUNTIME v1.2 — SECURE ACCESS BROKER + PIN LOGIN
# Login: chrisksys1
# PIN: 1298
# Zero-Trust, Capability-Based Access Layer
# Author: Brendon Joseph Kelly
# Hash: 3db297f42aa8ff207e7c9804b6cb1f2f
# Timestamp: 2025-11-17T04:52:00Z
# Crown Seal: Ω†BLK
# ============================================================

import hashlib
import hmac
import os
import time
import json
from typing import Dict, Any, Callable


# ------------------------------------------------------------
# AUTHENTICATION CORE — PIN CHECK
# ------------------------------------------------------------

PIN_HASH = hashlib.sha256("1298".encode()).hexdigest()

def verify_pin(pin: str) -> bool:
    """Secure constant-time PIN verification."""
    attempt = hashlib.sha256(pin.encode()).hexdigest()
    return hmac.compare_digest(attempt, PIN_HASH)


# ------------------------------------------------------------
# CRYPTO CORE
# ------------------------------------------------------------

class Keyring:
    def __init__(self, master_key: bytes):
        self.master_key = master_key

    def sign(self, message: bytes) -> str:
        return hmac.new(self.master_key, message, hashlib.sha256).hexdigest()

    def verify(self, message: bytes, signature: str) -> bool:
        return hmac.compare_digest(
            hmac.new(self.master_key, message, hashlib.sha256).hexdigest(),
            signature
        )


# ------------------------------------------------------------
# ZERO-TRUST CAPABILITY TOKEN
# ------------------------------------------------------------

class CapabilityToken:
    def __init__(self, subject: str, permissions: Dict[str, bool], keyring: Keyring):
        self.subject = subject
        self.permissions = permissions
        self.keyring = keyring

    def encode(self) -> str:
        payload = {
            "subject": self.subject,
            "permissions": self.permissions,
            "ts": time.time()
        }
        raw = json.dumps(payload).encode()
        sig = self.keyring.sign(raw)
        return json.dumps({"payload": payload, "signature": sig})

    @staticmethod
    def decode(token_str: str, keyring: Keyring) -> "CapabilityToken":
        obj = json.loads(token_str)
        raw = json.dumps(obj["payload"]).encode()
        if not keyring.verify(raw, obj["signature"]):
            raise PermissionError("Invalid token signature")
        return CapabilityToken(
            subject=obj["payload"]["subject"],
            permissions=obj["payload"]["permissions"],
            keyring=keyring
        )


# ------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------

class AccessRouter:
    def __init__(self):
        self.routes: Dict[str, Callable[[Any], Any]] = {}

    def route(self, name: str):
        def decorator(func):
            self.routes[name] = func
            return func
        return decorator

    def execute(self, token: CapabilityToken, name: str, data: Any):
        if name not in self.routes:
            raise KeyError("No such capability route")

        if not token.permissions.get(name, False):
            raise PermissionError(
                f"Subject '{token.subject}' lacks permission for '{name}'"
            )

        return self.routes[name](data)


# ------------------------------------------------------------
# BOOTSTRAP
# ------------------------------------------------------------

MASTER_KEY = os.getenv("BUNDY_MASTER_KEY", "dev-fallback-key").encode()
keyring = Keyring(MASTER_KEY)
router = AccessRouter()


# ------------------------------------------------------------
# CAPABILITY MODULES
# ------------------------------------------------------------

@router.route("read_dataset")
def read_dataset(data):
    path = data.get("path")
    with open(path, "r") as f:
        return f.read()

@router.route("submit_log")
def submit_log(data):
    msg = data.get("message")
    ts = time.time()
    return {"status": "ok", "timestamp": ts, "echo": msg}

@router.route("run_analysis")
def run_analysis(data):
    return {"result": sum(data.get("numbers", []))}


# ------------------------------------------------------------
# LOGIN + TOKEN GENERATION (CHRISKSYS1)
# ------------------------------------------------------------

def bundy_login(pin: str) -> str:
    if not verify_pin(pin):
        raise PermissionError("Incorrect PIN")

    token = CapabilityToken(
        subject="chrisksys1",
        permissions={
            "read_dataset": True,
            "submit_log": True,
            "run_analysis": True
        },
        keyring=keyring
    )
    return token.encode()


if __name__ == "__main__":
    # Example login run
    try:
        token = bundy_login("1298")
        print("Login OK — Token:")
        print(token)
    except PermissionError as e:
        print("Login failed:", str(e))
