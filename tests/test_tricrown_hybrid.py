from tricrown_hybrid import (
    ctx_init,
    client_hello,
    server_hello,
    client_finish,
    server_finish,
    seal,
    open_,
    rekey,
    _HAS_OQS,
)


def test_handshake_and_records():
    client = ctx_init("client", enable_pq=True)
    server = ctx_init("server", enable_pq=True)

    m1 = client_hello(client)
    m2 = server_hello(server, m1)
    m3 = client_finish(client, m2)
    server_finish(server, m3)

    assert client.chains is not None
    assert server.chains is not None
    assert client.chains.rk == server.chains.rk

    aad = b"test|aad"
    record1 = seal(client, aad, b"alpha")
    record2 = seal(client, aad, b"beta")

    assert open_(server, record1) == b"alpha"
    assert open_(server, record2) == b"beta"
    assert record1["nonce"] != record2["nonce"]

    tampered = dict(record1)
    tampered["ct"] = bytes([record1["ct"][0] ^ 1]) + record1["ct"][1:]

    try:
        open_(server, tampered)
        assert False, "tampering undetected"
    except Exception:
        pass

    rekey(client)
    rekey(server)
    record3 = seal(client, aad, b"gamma")
    assert open_(server, record3) == b"gamma"


def test_ctx_init_role_validation():
    try:
        ctx_init("bad-role")
        assert False, "invalid role accepted"
    except ValueError:
        pass


def test_pq_flag_matches_environment():
    ctx = ctx_init("client", enable_pq=True)
    assert ctx.enable_pq is _HAS_OQS
