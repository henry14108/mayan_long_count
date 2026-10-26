# mayan_long_count

Converts between Gregorian dates and Mayan Long Count calendar dates using the GMT (584283) correlation.  Standard library only, no dependencies.

```python
from mayan_long_count import LongCount, from_gregorian, to_gregorian

# Gregorian -> Long Count
lc = from_gregorian(2012, 12, 21)
assert str(lc) == "13.0.0.0.0"

# Long Count -> Gregorian (astronomical year numbering: year 0 = 1 BCE)
year, month, day = to_gregorian(LongCount(0, 0, 0, 0, 0))
assert (year, month, day) == (-3113, 8, 11)

# Build a Long Count directly and convert
lc2 = LongCount(9, 9, 9, 9, 9)
year, month, day = to_gregorian(lc2)
```

## Why this exists

The Mayan Long Count is a positional day-count with one awkward feature: the third place (the tun) is 360 days, not 400.  Every other place is 20× the previous one.  Getting that step right is the entire substance of the arithmetic; everything else is division and modulus.

This library exists to do that one job with no dependencies and no ambiguity.  It uses the GMT correlation (584283), which is the most widely cited of the proposed correlations.  If you need a different correlation, this is not the library for it.

## The edge you will hit

Years use **astronomical numbering**: year 0 = 1 BCE, year -1 = 2 BCE, and so on.  There is no year 0 in the BCE/CE convention.  This library does not try to support both conventions; it uses astronomical numbering throughout because it makes the arithmetic well-defined for all integer years.  If you pass a date like `(0, 1, 1)`, you get the first day of 1 BCE, not an error.

Construction of `LongCount` does **not** normalize components.  `LongCount(0, 0, 0, 0, 25)` is a distinct object from `LongCount(0, 0, 0, 1, 5)` — the first has kin=25, the second has kin=5 and winal=1.  Use `LongCount.from_days(n)` if you want a canonical form from a raw day count.

## Exports

- `LongCount(baktun, katun, tun, winal, kin)` — immutable dataclass.  Fields are not normalized on construction.
- `LongCount.from_days(days: int) -> LongCount` — canonical construction from a day offset (0 = 0.0.0.0.0).  Handles negative days by letting baktun go negative.
- `LongCount.to_days() -> int` — inverse of `from_days` for the positional value.
- `to_gregorian(lc: LongCount) -> tuple[int, int, int]` — returns `(year, month, day)` in proleptic Gregorian with astronomical year numbering.
- `from_gregorian(year: int, month: int, day: int) -> LongCount` — inverse of `to_gregorian`.
- `DAYS_PER_BAKTUN`, `DAYS_PER_KATUN`, `DAYS_PER_TUN`, `DAYS_PER_WINAL` — period constants (144000, 7200, 360, 20).

## Running tests

```
PYTHONPATH=src python -m unittest discover -s tests
```

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

