"""Core logic for converting between Gregorian (proleptic) dates and Mayan Long Count.

GMT correlation
---------------
The most widely used correlation between the Mayan Long Count and the Julian
Day Number (JDN) system is the Goodman-Martinez-Thompson (GMT) correlation,
also called correlation 584283.  Under this correlation, Long Count
13.0.0.0.0 corresponds to JDN 584283, which is September 6, 3114 BCE in the
proleptic Gregorian calendar.

We use the *astronomical* year numbering convention: year 0 = 1 BCE,
year -1 = 2 BCE, and so on.  This avoids the AD/CE–BCE gap and makes
arithmetic straightforward.  This is the one ambiguity the brief mentions;
we state it here plainly and do not attempt to support multiple conventions.

The algorithms below (gregorian_to_jdn / jdn_to_gregorian) are the classic
Fliegel & Van Flandern formulas for the proleptic Gregorian calendar.  They
work for any integer year, including negative ones, and are fully deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

# Long Count period values (each period is 20× the previous, except the tun).
DAYS_PER_KIN = 1
DAYS_PER_WINAL = 20
DAYS_PER_TUN = 360  # 18 winal, not 20 — this is the one non-decimal step.
DAYS_PER_KATUN = 7_200  # 20 tun
DAYS_PER_BAKTUN = 144_000  # 20 katun

# Under the GMT (584283) correlation, Long Count 0.0.0.0.0 falls on JDN 584283.
GMT_CORRELATION_CONSTANT = 584_283

# Days from 13.0.0.0.0 to 0.0.0.0.0 (i.e. 13 baktun).
DAYS_13_BAKTUN = 13 * DAYS_PER_BAKTUN


def _gregorian_to_jdn(year: int, month: int, day: int) -> int:
    """Convert a proleptic Gregorian date to Julian Day Number.

    Uses the Fliegel & Van Flandern algorithm.  Works for any integer year
    (including year 0 and negative years under astronomical numbering).
    """
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _jdn_to_gregorian(jdn: int) -> tuple[int, int, int]:
    """Convert a Julian Day Number to a proleptic Gregorian date.

    Inverse of _gregorian_to_jdn.  Returns (year, month, day) with year in
    astronomical numbering (year 0 = 1 BCE).
    """
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return year, month, day


def _to_days(baktun: int, katun: int, tun: int, winal: int, kin: int) -> int:
    """Convert Long Count components to a day count from 0.0.0.0.0.

    The Long Count is purely positional: baktun.katun.tun.winal.kin, where each
    place is 20× the previous except the tun which is 18× the winal (360 days).
    Negative place values are allowed so the user can express any integer day
    offset from the epoch.
    """
    return (
        baktun * DAYS_PER_BAKTUN
        + katun * DAYS_PER_KATUN
        + tun * DAYS_PER_TUN
        + winal * DAYS_PER_WINAL
        + kin * DAYS_PER_KIN
    )


@dataclass(frozen=True)
class LongCount:
    """An immutable Mayan Long Count date.

    Fields:
        baktun, katun, tun, winal, kin: the five positional components.

    The epoch (0.0.0.0.0) corresponds, under the GMT correlation, to August 11,
    3114 BCE in the proleptic Gregorian calendar (astronomical year -3113).
    13.0.0.0.0 corresponds to December 21, 2012.

    Construction does NOT normalize components; LongCount(0, 0, 0, 0, 25) is a
    distinct object from LongCount(0, 0, 0, 1, 5).  This lets callers represent
    non-canonical or extended forms exactly as given.
    """

    baktun: int
    katun: int
    tun: int
    winal: int
    kin: int

    @classmethod
    def from_days(cls, days: int) -> "LongCount":
        """Construct a canonical LongCount from a day offset from 0.0.0.0.0.

        Day 0 is 0.0.0.0.0.  Positive days count forward, negative days count
        backward.  The result is always canonical: kin ∈ [0, 19], winal ∈ [0, 17],
        tun ∈ [0, 19], katun ∈ [0, 19].  Baktun may be any integer (positive or
        negative), which is the standard way the Long Count extends beyond a
        single 13-baktun cycle.
        """
        if not isinstance(days, int):
            raise TypeError(f"days must be int, got {type(days).__name__}")
        baktun, rem = divmod(days, DAYS_PER_BAKTUN)
        katun, rem = divmod(rem, DAYS_PER_KATUN)
        tun, rem = divmod(rem, DAYS_PER_TUN)
        winal, kin = divmod(rem, DAYS_PER_WINAL)
        return cls(baktun, katun, tun, winal, kin)

    def to_days(self) -> int:
        """Return the day offset of this LongCount from 0.0.0.0.0."""
        return _to_days(
            self.baktun, self.katun, self.tun, self.winal, self.kin
        )

    def __str__(self) -> str:
        return f"{self.baktun}.{self.katun}.{self.tun}.{self.winal}.{self.kin}"

    def __repr__(self) -> str:
        return (
            f"LongCount(baktun={self.baktun!r}, katun={self.katun!r}, "
            f"tun={self.tun!r}, winal={self.winal!r}, kin={self.kin!r})"
        )


def to_gregorian(lc: LongCount) -> tuple[int, int, int]:
    """Convert a LongCount to a proleptic Gregorian (year, month, day) triple.

    Year uses astronomical numbering: year 0 = 1 BCE, year -1 = 2 BCE, etc.
    """
    if not isinstance(lc, LongCount):
        raise TypeError(f"lc must be LongCount, got {type(lc).__name__}")
    jdn = lc.to_days() + GMT_CORRELATION_CONSTANT
    return _jdn_to_gregorian(jdn)


def from_gregorian(year: int, month: int, day: int) -> LongCount:
    """Convert a proleptic Gregorian date to a canonical LongCount.

    Year uses astronomical numbering: year 0 = 1 BCE, year -1 = 2 BCE, etc.
    Month is 1–12 and day is 1–31.  No range validation is performed on month/day
    beyond what the JDN algorithm inherently requires; the JDN formula produces
    well-defined results for any integers but nonsense for out-of-range values,
    so callers should pass valid calendar dates.
    """
    if not isinstance(year, int) or not isinstance(month, int) or not isinstance(day, int):
        raise TypeError("year, month, day must all be int")
    jdn = _gregorian_to_jdn(year, month, day)
    days = jdn - GMT_CORRELATION_CONSTANT
    return LongCount.from_days(days)
