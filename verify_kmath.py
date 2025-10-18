import hashlib
import math
import json
from typing import List
import sys

# ---------- Symbol alphabet (unique glyph tokens) ----------
SYMBOLS = [
    "\u03A9", "\u0394", "\u2297", "\u2662", "\u27DF", "\u03DE", "\u03E1", "\u2986", "\u2A10", "\u2127"
]
# deterministic seed data (author supplies this exact string)
AUTHOR_SEED = "ATNYCHI::CROWN-\u03A9::v1"

# ---------- deterministic mapping: symbol -> 32-bit int ----------
def symbol_to_int(sym: str, salt: str) -> int:
    h = hashlib.sha256((sym + "|" + salt).encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big")  # 32-bit deterministic

# ---------- simple Hadamard-like cascade (deterministic, reversible linear mix) ----------
def hadamard_cascade(vec: List[int]) -> List[float]:
    # promote to floats for transforms
    out = [float(x) for x in vec]
    n = len(out)
    h = 1
    while h < n:
        for i in range(0, n, h * 2):
            for j in range(i, i + h):
                a = out[j]
                b = out[j + h]
                out[j] = a + b
                out[j + h] = a - b
        h *= 2
    return out

# ---------- FFT magnitude-like deterministic transform (no complex libs) ----------
def pseudo_fft_magnitude(vec: List[float]) -> List[float]:
    n = len(vec)
    mags = []
    for k in range(n):
        re = 0.0
        im = 0.0
        for t, val in enumerate(vec):
            angle = 2.0 * math.pi * t * k / n
            re += val * math.cos(angle)
            im -= val * math.sin(angle)
        mags.append(math.hypot(re, im))
    return mags

# ---------- canonical serialization ----------
def canonical_serialize(obj) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")

# ---------- build the vector, compute transforms, produce digest ----------
def build_and_prove(symbols=SYMBOLS, seed=AUTHOR_SEED):
    mapped = [symbol_to_int(s, seed) for s in symbols]
    # pad to power of two (small deterministic pad)
    target_n = 1
    while target_n < len(mapped):
        target_n *= 2
    while len(mapped) < target_n:
        mapped.append(0)
    hcascade = hadamard_cascade(mapped)
    mags = pseudo_fft_magnitude(hcascade)
    # produce canonical output object
    out = {
        "seed": seed,
        "symbols": symbols,
        "mapped": mapped,
        "hadamard": [round(x, 6) for x in hcascade],
        "magnitude": [round(x, 6) for x in mags],
    }
    digest = hashlib.sha256(canonical_serialize(out)).hexdigest()
    out["digest"] = digest
    return out

# ---------- run and print canonical JSON ----------
if __name__ == "__main__":
    proof = build_and_prove()
    print(json.dumps(proof, indent=2, sort_keys=True))
    # copyable digest for public posting
    print("\nCANONICAL DIGEST:", proof["digest"])
    # Optional: instructions for signing
    print("\nTo attest: compute sha256 of the full JSON above and sign with Ed25519.")
    print("Publish: (json, signature, public_key). Verifiers recompute sha256 and verify signature.")
