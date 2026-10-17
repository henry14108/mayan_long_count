"""Tests for mayan_long_count.core.

All tests are deterministic and use fixed historical dates.  The reference
dates come from the GMT (584283) correlation, which is the single most widely
used Mayan-to-Gregorian correlation.
"""

import math
import unittest

from mayan_long_count.core import (
    DAYS_PER_BAKTUN,
    DAYS_PER_KATUN,
    DAYS_PER_TUN,
    DAYS_PER_WINAL,
    LongCount,
    from_gregorian,
    to_gregorian,
)


class TestLongCountFromDays(unittest.TestCase):
    def test_epoch_is_zero(self):
        lc = LongCount.from_days(0)
        self.assertEqual((lc.baktun, lc.katun, lc.tun, lc.winal, lc.kin), (0, 0, 0, 0, 0))

    def test_one_kin(self):
        lc = LongCount.from_days(1)
        self.assertEqual((lc.baktun, lc.katun, lc.tun, lc.winal, lc.kin), (0, 0, 0, 0, 1))

    def test_kin_rolls_into_winal_at_20(self):
        # 20 kin = 1 winal; the Long Count does NOT use a 20-kin tun.
        lc = LongCount.from_days(20)
        self.assertEqual((lc.baktun, lc.katun, lc.tun, lc.winal, lc.kin), (0, 0, 0, 1, 0))

    def test_winal_rolls_into_tun_at_18(self):
        # 18 winal = 1 tun (360 days).  This is the one non-decimal step.
        lc = LongCount.from_days(360)
        self.assertEqual((lc.baktun, lc.katun, lc.tun, lc.winal, lc.kin), (0, 0, 1, 0, 0))

    def test_baktun_boundary(self):
        lc = LongCount.from_days(DAYS_PER_BAKTUN)
        self.assertEqual((lc.baktun, lc.katun, lc.tun, lc.winal, lc.kin), (1, 0, 0, 0, 0))

    def test_negative_days_go_backward(self):
        # One day before 0.0.0.0.0 should be -1 baktun, 19 katun, 19 tun, 17 winal, 19 kin.
        # This is how the Long Count extends backward: baktun goes negative.
        lc = LongCount.from_days(-1)
        self.assertEqual((lc.baktun, lc.katun, lc.tun, lc.winal, lc.kin), (-1, 19, 19, 17, 19))

    def test_negative_one_baktun(self):
        lc = LongCount.from_days(-DAYS_PER_BAKTUN)
        self.assertEqual((lc.baktun, lc.katun, lc.tun, lc.winal, lc.kin), (-1, 0, 0, 0, 0))

    def test_rejects_non_int(self):
        with self.assertRaises(TypeError):
            LongCount.from_days(1.5)  # type: ignore[arg-type]


class TestLongCountToDays(unittest.TestCase):
    def test_roundtrip_positive(self):
        original = LongCount(7, 14, 3, 12, 9)
        self.assertEqual(LongCount.from_days(original.to_days()), original)

    def test_roundtrip_with_negative_baktun(self):
        original = LongCount(-3, 5, 10, 2, 7)
        self.assertEqual(LongCount.from_days(original.to_days()), original)

    def test_non_canonical_not_normalized(self):
        # to_days just computes the positional value; it does NOT normalize.
        non_canonical = LongCount(0, 0, 0, 0, 25)
        self.assertEqual(non_canonical.to_days(), 25)
        self.assertEqual(LongCount.from_days(25), LongCount(0, 0, 0, 1, 5))
        self.assertNotEqual(non_canonical, LongCount(0, 0, 0, 1, 5))


class TestGregorianRoundtrip(unittest.TestCase):
    def test_dec_21_2012(self):
        # The famous 13.0.0.0.0 date.
        lc = from_gregorian(2012, 12, 21)
        self.assertEqual(str(lc), "13.0.0.0.0")
        self.assertEqual(to_gregorian(lc), (2012, 12, 21))

    def test_aug_11_3114_bce(self):
        # The epoch 0.0.0.0.0 under the GMT correlation.
        lc = from_gregorian(-3113, 8, 11)
        self.assertEqual(str(lc), "0.0.0.0.0")
        self.assertEqual(to_gregorian(lc), (-3113, 8, 11))

    def test_sep_6_3114_bce(self):
        # September 6, 3114 BCE is 26 days after the GMT epoch (August 11).
        # That is 1 winal + 6 kin = 0.0.0.1.6 under the GMT correlation.
        lc = from_gregorian(-3113, 9, 6)
        self.assertEqual(str(lc), "0.0.0.1.6")
        self.assertEqual(to_gregorian(lc), (-3113, 9, 6))

    def test_arbitrary_modern_date(self):
        y, m, d = 1969, 7, 20
        lc = from_gregorian(y, m, d)
        self.assertEqual(to_gregorian(lc), (y, m, d))

    def test_jan_1_year_1(self):
        # The first day of year 1 in astronomical numbering (1 CE).
        lc = from_gregorian(1, 1, 1)
        self.assertEqual(to_gregorian(lc), (1, 1, 1))

    def test_roundtrip_many_dates(self):
        # Deterministic pseudo-random sampling using a fixed seed-equivalent.
        # We avoid randomness entirely and just walk a fixed set of dates.
        test_dates = [
            (1, 3, 15),
            (100, 7, 4),
            (500, 12, 31),
            (1000, 1, 1),
            (1500, 6, 15),
            (2000, 2, 29),  # leap day in Gregorian
            (2020, 11, 17),
            (-1, 12, 31),   # 2 BCE
            (-44, 3, 15),   # 45 BCE (year 0 exists in astronomical numbering)
            (0, 1, 1),      # Year 0 = 1 BCE.  This must round-trip correctly.
        ]
        for y, m, d in test_dates:
            with self.subTest(date=(y, m, d)):
                lc = from_gregorian(y, m, d)
                self.assertEqual(to_gregorian(lc), (y, m, d))

    def test_year_zero_is_valid(self):
        # In astronomical numbering, year 0 = 1 BCE.  The Fliegel & Van Flandern
        # formula handles this correctly.
        lc = from_gregorian(0, 2, 29)
        self.assertEqual(to_gregorian(lc), (0, 2, 29))

    def test_rejects_non_int_inputs(self):
        with self.assertRaises(TypeError):
            from_gregorian(2012.0, 12, 21)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            from_gregorian(2012, 12.0, 21)  # type: ignore[arg-type]

    def test_to_gregorian_rejects_non_longcount(self):
        with self.assertRaises(TypeError):
            to_gregorian("13.0.0.0.0")  # type: ignore[arg-type]


class TestStrAndRepr(unittest.TestCase):
    def test_str(self):
        lc = LongCount(13, 0, 0, 0, 0)
        self.assertEqual(str(lc), "13.0.0.0.0")

    def test_repr(self):
        lc = LongCount(1, 2, 3, 4, 5)
        r = repr(lc)
        self.assertIn("LongCount(", r)
        self.assertIn("baktun=1", r)
        self.assertIn("kin=5", r)

    def test_equality_and_hash(self):
        a = LongCount(1, 2, 3, 4, 5)
        b = LongCount(1, 2, 3, 4, 5)
        c = LongCount(1, 2, 3, 4, 6)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(hash(a), hash(b))


class TestPeriodConstants(unittest.TestCase):
    def test_period_relationships(self):
        # The tun is 360, not 400 — the critical non-decimal step.
        self.assertEqual(DAYS_PER_TUN, 18 * DAYS_PER_WINAL)
        self.assertEqual(DAYS_PER_KATUN, 20 * DAYS_PER_TUN)
        self.assertEqual(DAYS_PER_BAKTUN, 20 * DAYS_PER_KATUN)
        self.assertNotEqual(DAYS_PER_TUN, 20 * DAYS_PER_WINAL)


if __name__ == "__main__":
    unittest.main()
