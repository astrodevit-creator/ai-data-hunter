from data_hunter import (
    parse_price, Record, normalize, validate, hunt,
)
import pytest


def test_parse_price_us():
    assert parse_price("$89.99") == pytest.approx(89.99)


def test_parse_price_eu_comma_decimal():
    assert parse_price("89,99") == pytest.approx(89.99)


def test_parse_price_eu_thousands():
    assert parse_price("1.234,50 €") == pytest.approx(1234.50)


def test_parse_price_mad():
    assert parse_price("250 MAD") == pytest.approx(250.0)


def test_parse_price_none():
    assert parse_price("") is None
    assert parse_price("contact us") is None


def test_normalize_dedupes():
    a = Record("s1", "Shoe", 10.0, "u1")
    b = Record("s1", "Shoe", 10.0, "u1")  # duplicate by fingerprint
    c = Record("s1", "Boot", 20.0, "u2")
    out = normalize([a, b, c])
    assert len(out) == 2


def test_validate_filters():
    recs = [
        Record("s", "A", 10.0),
        Record("s", "", 5.0),          # no name -> dropped
        Record("s", "C", 9999.0),
    ]
    out = validate(recs, require_price=True, max_price=1000.0)
    names = {r.name for r in out}
    assert names == {"A"}  # C dropped by max_price, empty name dropped


def test_hunt_end_to_end():
    def fake_fetch(url: str) -> list:
        return [
            Record("shop", "Red Shoe", 50.0, url),
            Record("shop", "Red Shoe", 50.0, url),  # dup
            Record("shop", "Blue Shoe", 70.0, url),
        ]
    out = hunt(fake_fetch, ["https://a", "https://b"])
    assert len(out) == 2  # deduped across urls too (same source+name)
    assert {r.name for r in out} == {"Red Shoe", "Blue Shoe"}
