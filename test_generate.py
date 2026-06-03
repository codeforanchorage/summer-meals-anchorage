#!/usr/bin/env python3
"""Stdlib-only unit tests for generate.py.

Run with:  python -m unittest -v   (or: python test_generate.py)

These cover the parsing and scoping logic that turns the raw USDA feed into the
page -- the parts most likely to break when the feed's free-text formats drift.
No network access: importing generate.py does not fetch (main() is guarded).
"""

import unittest
from datetime import date

import generate as g

TODAY = date(2026, 6, 3)  # a Wednesday


class ParseDays(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(g.parse_days(""), set())
        self.assertEqual(g.parse_days(None), set())

    def test_daily(self):
        self.assertEqual(g.parse_days("Daily"), set(range(7)))
        self.assertEqual(g.parse_days("Every day"), set(range(7)))
        self.assertEqual(g.parse_days("7 days"), set(range(7)))

    def test_weekday_weekend_words(self):
        self.assertEqual(g.parse_days("Weekdays"), {0, 1, 2, 3, 4})
        self.assertEqual(g.parse_days("Weekends"), {5, 6})

    def test_word_ranges(self):
        self.assertEqual(g.parse_days("Mon-Fri"), {0, 1, 2, 3, 4})
        self.assertEqual(g.parse_days("Monday through Friday"), {0, 1, 2, 3, 4})
        self.assertEqual(g.parse_days("Tuesday to Thursday"), {1, 2, 3})

    def test_word_lists(self):
        self.assertEqual(g.parse_days("Tuesday, Thursday"), {1, 3})
        self.assertEqual(g.parse_days("Saturday, Sunday"), {5, 6})

    def test_compact_forms(self):
        self.assertEqual(g.parse_days("M-F"), {0, 1, 2, 3, 4})
        self.assertEqual(g.parse_days("MWF"), {0, 2, 4})

    def test_letter_codes(self):
        # The format the live 2026 feed actually uses.
        self.assertEqual(g.parse_days("M,T,W,TH,F"), {0, 1, 2, 3, 4})
        self.assertEqual(g.parse_days("T,W,TH,F"), {1, 2, 3, 4})
        self.assertEqual(g.parse_days("M,T,W,TH,F,SA"), {0, 1, 2, 3, 4, 5})
        self.assertEqual(g.parse_days("M,T,W,TH"), {0, 1, 2, 3})
        self.assertEqual(g.parse_days("M,W,F"), {0, 2, 4})
        self.assertEqual(g.parse_days("W"), {2})
        self.assertEqual(g.parse_days("TH"), {3})
        self.assertEqual(g.parse_days("SA"), {5})
        self.assertEqual(g.parse_days("M / W / F"), {0, 2, 4})

    def test_no_false_positives_from_prose(self):
        # Must NOT guess weekdays out of ambiguous free text.
        self.assertEqual(g.parse_days("Call for schedule"), set())
        self.assertEqual(g.parse_days("Hours vary week to week"), set())
        self.assertEqual(g.parse_days("See website"), set())


class FormatDays(unittest.TestCase):
    def test_ranges_collapse(self):
        self.assertEqual(g.format_days({0, 1, 2, 3, 4}, "M,T,W,TH,F"), "Mon–Fri")
        self.assertEqual(g.format_days({0, 1, 2, 3}, "M,T,W,TH"), "Mon–Thu")

    def test_two_adjacent_not_a_range(self):
        self.assertEqual(g.format_days({5, 6}, "SA,SU"), "Sat, Sun")

    def test_singletons_and_gaps(self):
        self.assertEqual(g.format_days({0, 2, 4}, "M,W,F"), "Mon, Wed, Fri")
        self.assertEqual(g.format_days({2}, "W"), "Wed")

    def test_falls_back_to_raw(self):
        self.assertEqual(g.format_days(set(), "Call for schedule"),
                         "Call for schedule")


class ParseTextDate(unittest.TestCase):
    def test_slash_formats(self):
        self.assertEqual(g.parse_text_date("6/2/2026", TODAY), date(2026, 6, 2))
        self.assertEqual(g.parse_text_date("8/8/2026", TODAY), date(2026, 8, 8))

    def test_word_formats(self):
        self.assertEqual(g.parse_text_date("June 2, 2026", TODAY), date(2026, 6, 2))
        self.assertEqual(g.parse_text_date("Aug 8 2026", TODAY), date(2026, 8, 8))

    def test_iso(self):
        self.assertEqual(g.parse_text_date("2026-06-02", TODAY), date(2026, 6, 2))

    def test_year_inferred(self):
        self.assertEqual(g.parse_text_date("6/2", TODAY), date(2026, 6, 2))

    def test_unparseable(self):
        self.assertIsNone(g.parse_text_date("", TODAY))
        self.assertIsNone(g.parse_text_date("sometime in summer", TODAY))


class ParseEpochDate(unittest.TestCase):
    def test_epoch(self):
        # 2026-08-10 20:00 UTC == noon Anchorage (AKDT), so the local date is
        # unambiguously 2026-08-10 regardless of the runner's timezone.
        self.assertEqual(g.parse_epoch_date(1786392000000), date(2026, 8, 10))

    def test_blank(self):
        self.assertIsNone(g.parse_epoch_date(None))
        self.assertIsNone(g.parse_epoch_date(""))


class ModelInfo(unittest.TestCase):
    def test_congregate_onsite(self):
        self.assertEqual(g.model_info("CONGREGATE"), ("Eat on-site", "onsite"))
        self.assertEqual(g.model_info("Eat On-Site"), ("Eat on-site", "onsite"))

    def test_non_congregate_is_togo(self):
        self.assertEqual(g.model_info("NON-CONGREGATE PICK UP"),
                         ("Grab & go / pick-up", "togo"))
        self.assertEqual(g.model_info("Meals To Go"),
                         ("Grab & go / pick-up", "togo"))

    def test_empty(self):
        self.assertEqual(g.model_info(""), ("", ""))
        self.assertEqual(g.model_info("null"), ("", ""))


class Scope(unittest.TestCase):
    def _rec(self, city, name="Site"):
        return g.normalize({"Site_Name": name, "Site_City": city,
                            "Site_State": "AK"}, TODAY)

    def test_anchorage_in_scope(self):
        self.assertTrue(g.in_scope(self._rec("Anchorage")))

    def test_municipality_in_scope(self):
        self.assertTrue(g.in_scope(self._rec("Eagle River")))
        self.assertTrue(g.in_scope(self._rec("Girdwood")))
        self.assertTrue(g.in_scope(self._rec("Chugiak")))

    def test_typo_in_scope_and_corrected_for_display(self):
        rec = self._rec("Anchroage")
        self.assertTrue(g.in_scope(rec))
        self.assertEqual(rec["city"], "Anchorage")  # corrected for display

    def test_out_of_scope(self):
        self.assertFalse(g.in_scope(self._rec("Wasilla")))
        self.assertFalse(g.in_scope(self._rec("Palmer")))
        self.assertFalse(g.in_scope(self._rec("Anchor Point")))


class Status(unittest.TestCase):
    def _rec(self, **over):
        raw = {"Site_Name": "S", "Site_City": "Anchorage", "Site_State": "AK"}
        raw.update(over)
        return g.normalize(raw, TODAY)

    def test_active_when_no_dates(self):
        self.assertEqual(g.status(self._rec(), TODAY), "active")

    def test_upcoming_from_epoch_start(self):
        # starts 2026-07-20, today is 2026-06-03
        rec = self._rec(Start_date=1784505600000)
        self.assertEqual(g.status(rec, TODAY), "upcoming")

    def test_ended_from_epoch_end(self):
        rec = self._rec(End_date=1748908800000)  # 2025-06-03
        self.assertEqual(g.status(rec, TODAY), "ended")


class Normalize(unittest.TestCase):
    def test_meal_time2_fallback(self):
        rec = g.normalize({"Site_Name": "S", "Site_City": "Anchorage",
                           "Site_State": "AK", "Lunch_Time2": "12:30-1:30"}, TODAY)
        self.assertIn(("Lunch", "12:30-1:30"), rec["meals"])

    def test_pii_fields_never_surface(self):
        rec = g.normalize({"Site_Name": "S", "Site_City": "Anchorage",
                           "Site_State": "AK", "Contact_First_Name": "Jane",
                           "Contact_Last_Name": "Doe",
                           "Contact_Phone": "555-1212"}, TODAY)
        blob = repr(rec)
        self.assertNotIn("Jane", blob)
        self.assertNotIn("Doe", blob)
        self.assertNotIn("555-1212", blob)


if __name__ == "__main__":
    unittest.main(verbosity=2)
