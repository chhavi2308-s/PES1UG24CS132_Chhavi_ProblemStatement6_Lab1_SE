"""Event ticket tier processor (hardened against invalid input).

Every function validates its input and NEVER raises on bad data:
  * decode_promo_voucher / parse_attendee_badge return an "Invalid ..." message
  * calculate_seat_tier_price returns None for invalid input
"""

TIER_RATES = {
    "VIP": 150.0,
    "PREMIUM": 90.0,
    "GENERAL": 45.0,
}

MAX_ROW = 1000
MAX_AGE = 120


def _to_int(text):
    """Safely convert text to int. Returns None if it is not a valid integer."""
    try:
        return int(text.strip())
    except (ValueError, TypeError, AttributeError, OverflowError):
        return None


def decode_promo_voucher(voucher_code):
    """Decode a voucher like 'EARLY-20' -> 'Valid EARLY: 20% OFF'."""
    if not isinstance(voucher_code, str):
        return "Invalid voucher: input must be a string"

    parts = voucher_code.strip().split('-')
    if len(parts) != 2:
        return "Invalid voucher: expected format PREFIX-PERCENT"

    prefix = parts[0].strip()
    if not prefix:
        return "Invalid voucher: missing prefix"

    percentage = _to_int(parts[1])
    if percentage is None:
        return "Invalid voucher: percentage must be a whole number"
    if not 0 <= percentage <= 100:
        return "Invalid voucher: percentage must be between 0 and 100"

    return f"Valid {prefix.upper()}: {percentage}% OFF"


def calculate_seat_tier_price(tier_spec):
    """Price for a spec like 'VIP@4'. Returns a float, or None if invalid."""
    if not isinstance(tier_spec, str):
        return None

    parts = tier_spec.split('@')
    if len(parts) != 2:
        return None

    tier = parts[0].strip().upper()
    base = TIER_RATES.get(tier)
    if base is None:
        return None

    row = _to_int(parts[1])
    if row is None or not 1 <= row <= MAX_ROW:
        return None

    return base + (row * 2.0)


def parse_attendee_badge(badge_csv):
    """Parse 'Name,Age,Seat' -> 'Name [Adult/Child] - Seat X'."""
    if not isinstance(badge_csv, str):
        return "Invalid badge: input must be a string"

    tokens = badge_csv.split(',')
    if len(tokens) != 3:
        return "Invalid badge: expected format Name,Age,Seat"

    name = tokens[0].strip()
    seat = tokens[2].strip()
    if not name:
        return "Invalid badge: missing name"
    if not seat:
        return "Invalid badge: missing seat"

    age = _to_int(tokens[1])
    if age is None:
        return "Invalid badge: age must be a whole number"
    if not 0 <= age <= MAX_AGE:
        return f"Invalid badge: age must be between 0 and {MAX_AGE}"

    category = "Child" if age < 18 else "Adult"
    return f"{name} [{category}] - Seat {seat}"


def main():
    print("==== Running decode_promo_voucher ====")
    v_input = input("Enter voucher (e.g. EARLY-20): ")
    print("Voucher:", decode_promo_voucher(v_input))

    print("\n==== Running calculate_seat_tier_price ====")
    t_input = input("Enter tier spec (e.g. VIP@4): ")
    price = calculate_seat_tier_price(t_input)
    if price is None:
        print("Seat Price: Invalid tier spec (expected TIER@ROW, e.g. VIP@4)")
    else:
        print("Seat Price: $", price)

    print("\n==== Running parse_attendee_badge ====")
    b_input = input("Enter badge CSV (Name,Age,Seat): ")
    print("Badge:", parse_attendee_badge(b_input))


if __name__ == "__main__":
    main()
