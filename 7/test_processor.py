from hypothesis import given, strategies as st
from processor import decode_promo_voucher, calculate_seat_tier_price, parse_attendee_badge


# ---------- Required fuzz tests: functions must never crash ----------

@given(st.text() | st.none())
def test_decode_promo_voucher_no_crash(s):
    try:
        decode_promo_voucher(s)
    except Exception as e:
        assert False, f"decode_promo_voucher crashed with: {e!r}"


@given(st.text() | st.none())
def test_calculate_seat_tier_price_safe(s):
    try:
        calculate_seat_tier_price(s)
    except Exception as e:
        assert False, f"calculate_seat_tier_price crashed with: {e!r}"


@given(st.text() | st.none())
def test_parse_attendee_badge_safe(s):
    try:
        parse_attendee_badge(s)
    except Exception as e:
        assert False, f"parse_attendee_badge crashed with: {e!r}"


# ---------- Extra fuzzing: non-string inputs and valid-input properties ----------

@given(st.one_of(st.integers(), st.floats(), st.booleans(), st.lists(st.integers()), st.none()))
def test_non_string_inputs_do_not_crash(x):
    assert isinstance(decode_promo_voucher(x), str)
    assert calculate_seat_tier_price(x) is None
    assert isinstance(parse_attendee_badge(x), str)


@given(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1), st.integers(0, 100))
def test_valid_voucher_decodes(prefix, pct):
    assert decode_promo_voucher(f"{prefix}-{pct}") == f"Valid {prefix}: {pct}% OFF"


@given(st.text().filter(lambda t: t.strip() != "" and "-" not in t), st.integers().filter(lambda n: n < 0 or n > 100))
def test_out_of_range_voucher_rejected(prefix, pct):
    # a negative sign adds an extra '-', so it must be rejected too
    assert decode_promo_voucher(f"{prefix}-{pct}").startswith("Invalid")


@given(st.sampled_from(["VIP", "PREMIUM", "GENERAL"]), st.integers(1, 1000))
def test_valid_price_is_correct(tier, row):
    base = {"VIP": 150.0, "PREMIUM": 90.0, "GENERAL": 45.0}[tier]
    assert calculate_seat_tier_price(f"{tier}@{row}") == base + row * 2.0


@given(st.sampled_from(["VIP", "PREMIUM", "GENERAL"]), st.integers().filter(lambda n: n < 1 or n > 1000))
def test_invalid_row_returns_none(tier, row):
    assert calculate_seat_tier_price(f"{tier}@{row}") is None


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1), st.integers(0, 120),
       st.text(alphabet="ABCDEFGHIJ0123456789", min_size=1))
def test_valid_badge(name, age, seat):
    out = parse_attendee_badge(f"{name},{age},{seat}")
    assert out == f"{name} [{'Child' if age < 18 else 'Adult'}] - Seat {seat}"


@given(st.text(), st.integers().filter(lambda n: n < 0 or n > 120), st.text())
def test_invalid_age_badge_rejected(name, age, seat):
    out = parse_attendee_badge(f"{name.replace(',', '')},{age},{seat.replace(',', '')}")
    assert out.startswith("Invalid")
