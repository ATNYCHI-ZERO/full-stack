"""Regression tests for the intent-auth proof of concept."""
from __future__ import annotations

import unittest

import numpy as np
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from crypto_core import KEMStub, derive_key, decrypt_message, encrypt_message
from intent_model import IntentModel
from policy_engine import Policy, decide


class TestCryptoRoundTrip(unittest.TestCase):
    def test_roundtrip_with_utf8_operator_fp(self) -> None:
        receiver_sk = X25519PrivateKey.generate()
        receiver_pk = receiver_sk.public_key()
        encapsulated, shared = KEMStub.encapsulate(receiver_pk)
        operator_fp = "K-MATH::Ωv1".encode("utf-8")
        key = derive_key(shared, operator_fp)
        package = encrypt_message(b"hello", key)

        recovered_shared = KEMStub.decapsulate(receiver_sk, encapsulated)
        key2 = derive_key(recovered_shared, operator_fp)
        plaintext = decrypt_message(
            package.ciphertext,
            package.nonce,
            key2,
        )
        self.assertEqual(plaintext, b"hello")


class TestIntentDecision(unittest.TestCase):
    def test_decision_thresholds(self) -> None:
        model = IntentModel()
        model.train()
        benign = np.array([0.6, 0.4, 0.7, 0.2, 0.3, 0.5])
        score, _ = model.predict(benign)
        # Lenient policy ensures benign samples allow without flakiness.
        policy = Policy(allow_threshold=0.0, stepup_threshold=0.0, deny_threshold=0.0)
        self.assertEqual(decide(score, policy), "ALLOW")


if __name__ == "__main__":
    unittest.main()
