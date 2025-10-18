"""Run a miniature TRI-CROWN handshake using the reference helpers."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tricrown.session import TriCrownParty, perform_handshake


def main() -> None:
    client = TriCrownParty(role="client")
    server = TriCrownParty(role="server")
    client_result, server_result = perform_handshake(client, server, aead="AES-256-GCM-SIV")

    session_client = client_result.session
    session_server = server_result.session

    record = session_client.seal(b"hello quantum world", aad=b"demo")
    plaintext = session_server.open(record)
    print("server decrypted:", plaintext)


if __name__ == "__main__":
    main()
