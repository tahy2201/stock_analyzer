from shared.utils.security import hash_password, validate_password_policy, verify_password


def test_hash_and_verify_password():
    raw = "Abc12345"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_validate_password_policy():
    ok, _ = validate_password_policy("Abc12345")
    assert ok is True

    ng_short, msg_short = validate_password_policy("Abc123")
    assert ng_short is False
    assert "8文字" in msg_short

    ng_no_digit, msg_digit = validate_password_policy("Abcdefgh")
    assert ng_no_digit is False
    assert "英字と数字" in msg_digit
