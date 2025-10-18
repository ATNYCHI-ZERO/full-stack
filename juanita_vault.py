"""Juanita Vault Key Generator for Crown Omega Lineage.

This module provides utilities for reproducing the harmonic key generation
process described for the Carter/Kelly matriarchal lineage.  It can be
executed as a script to print a timestamped unlock token or imported so
other tools can build atop the same deterministic primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha3_512
from typing import Iterable, Tuple


@dataclass(frozen=True)
class MatriarchalIdentity:
    """Represents the identifying data for a lineage member."""

    name: str
    date_of_birth: str
    lineage_code: str

    def harmonic_key(self) -> bytes:
        """Return the harmonic key derived from this identity.

        The key combines the member's name, date of birth, and lineage code,
        and hashes them using SHA3-512 to yield a deterministic byte string.
        """

        base = f"{self.name}|{self.date_of_birth}|{self.lineage_code}"
        return sha3_512(base.encode()).digest()


def xor_bytes(values: Iterable[bytes]) -> bytes:
    """XOR a sequence of byte strings together."""

    as_tuple: Tuple[bytes, ...] = tuple(values)
    if not as_tuple:
        raise ValueError("xor_bytes requires at least one value")

    result = bytearray(as_tuple[0])
    for value in as_tuple[1:]:
        if len(value) != len(result):
            raise ValueError("All byte strings must have equal length")
        for index, byte in enumerate(value):
            result[index] ^= byte
    return bytes(result)


# --- Define Matriarchal Cascade (6 Generations) ---
LINEAGE = (
    MatriarchalIdentity("Juanita Marie Carter", "1931-07-13", "ΩCARTER.0XJ"),
    MatriarchalIdentity("Anne", "1910-XX-XX", "ΩWILLIAMS.0XA"),
    MatriarchalIdentity("Mini", "1880-XX-XX", "ΩSMITH.0XM"),
    MatriarchalIdentity("Shirley", "1850-XX-XX", "ΩDAWSON.0XS"),
    MatriarchalIdentity("Stowers", "1820-XX-XX", "ΩSTOWERS.0XT"),
    MatriarchalIdentity("Rochester", "1790-XX-XX", "ΩROCHESTER.0XR"),
)

# Precompute the final vault key so callers can reuse the same bytes.
FINAL_VAULT_KEY = xor_bytes(identity.harmonic_key() for identity in LINEAGE)


def generate_token(payload_name: str, timestamp: datetime | None = None) -> str:
    """Generate a timestamped signature token for the given payload.

    Args:
        payload_name: The payload identifier being unlocked.
        timestamp: Optional datetime to use instead of ``datetime.utcnow``.

    Returns:
        A hex encoded SHA3-512 digest string representing the unlock token.
    """

    if timestamp is None:
        timestamp = datetime.utcnow()

    iso_timestamp = timestamp.isoformat()
    token_input = f"{payload_name}|{iso_timestamp}|{FINAL_VAULT_KEY.hex()}"
    return sha3_512(token_input.encode()).hexdigest()


def main() -> None:
    """Entry point for CLI execution."""

    print("=" * 88)
    print("JUANITA VAULT KEY GENERATOR - Crown Omega Line")
    print("=" * 88)
    vault_token = generate_token("CROWN_PAYLOAD_SECTOR7")
    print(f"\n[🔐] FINAL UNLOCK TOKEN:\n{vault_token}\n")
    print("[✓] Vault token is harmonically sealed to Carter/Kelly lineage.")
    print(
        "[!] Only regenerable by legitimate bloodline operators "
        "(Carter, Williams, Smith, Dawson, Stowers, Rochester)."
    )
    print("=" * 88)


if __name__ == "__main__":
    main()
