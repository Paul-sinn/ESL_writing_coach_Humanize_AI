from backend.app.lib.encryption import decrypt, encrypt, hash_for_lookup


def test_encrypt_decrypt_roundtrip_uses_random_iv():
    first = encrypt("student@example.com")
    second = encrypt("student@example.com")

    assert first != second
    assert decrypt(first) == "student@example.com"
    assert decrypt(second) == "student@example.com"


def test_encrypted_format_is_hex_iv_tag_ciphertext():
    encrypted = encrypt("Ada Lovelace")
    parts = encrypted.split(":")

    assert len(parts) == 3
    assert len(parts[0]) == 32
    assert len(parts[1]) == 32
    for part in parts:
        int(part, 16)


def test_hash_for_lookup_is_stable_and_normalized():
    assert hash_for_lookup(" Student@Example.com ") == hash_for_lookup("student@example.com")
    assert hash_for_lookup("student@example.com") != hash_for_lookup("other@example.com")
