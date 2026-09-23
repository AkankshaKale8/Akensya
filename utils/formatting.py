
def money(value):
    if abs(value) >= 1_000_000:
        return f"₹{value/1_000_000:.1f}M"
    if abs(value) >= 100_000:
        return f"₹{value/100_000:.1f}L"
    return f"₹{value:,.0f}"
