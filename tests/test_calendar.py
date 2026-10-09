import copy
import json
import unittest
from pathlib import Path
from trading_calendar import build_calendar
from research import Calendar


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((Path(__file__).resolve().parents[1]/'data/bse-2026-schedule.json').read_text(encoding='utf-8'))

    def test_reviewed_schedule_count_and_reopening_days(self):
        result = build_calendar(self.spec)
        self.assertEqual(result['scheduled_trading_date_count'], 242)
        self.assertEqual(result['basis'], 'derived')
        for day in ['2026-01-05','2026-02-24','2026-04-07','2026-05-06','2026-06-22','2026-09-28','2026-10-08','2026-10-09']:
            with self.subTest(day=day):self.assertIn(day,result['trading_dates'])
        for day in ['2026-01-01','2026-02-23','2026-04-06','2026-05-05','2026-06-19','2026-09-25','2026-10-07']:
            with self.subTest(day=day):self.assertNotIn(day,result['trading_dates'])

    def test_government_makeup_weekends_and_test_day_remain_closed(self):
        result = build_calendar(self.spec)
        for day in ['2026-02-14','2026-02-28','2026-05-09','2026-09-20','2026-10-10','2026-10-06']:
            with self.subTest(day=day):self.assertNotIn(day,result['trading_dates'])

    def test_calendar_consumable_and_cross_holiday_next_day(self):
        from datetime import date
        result = build_calendar(self.spec)
        cal = Calendar(result)
        self.assertEqual(cal.next_day(date(2026,9,30)),date(2026,10,8))
        self.assertEqual(cal.next_day(date(2026,10,9)),date(2026,10,12))
        with self.assertRaises(ValueError):cal.check(date(2027,1,4))

    def test_unbound_ranges_overlap_and_bad_weekend_fail(self):
        for change in ['unbound','overlap','weekday']:
            spec=copy.deepcopy(self.spec)
            if change=='unbound':spec['holiday_closures'][0]['source_ids']=['unknown']
            if change=='overlap':spec['holiday_closures'].append(copy.deepcopy(spec['holiday_closures'][0]))
            if change=='weekday':spec['explicit_weekend_closures']=['2026-10-09']
            with self.subTest(change=change),self.assertRaises(ValueError):build_calendar(spec)

    def test_schedule_does_not_claim_actual_market_or_broker_verification(self):
        result=build_calendar(self.spec)
        self.assertIn('no exhaustive exceptional',result['derivation']['review_scope'])
        self.assertTrue(any('broker' in warning for warning in result['warnings']))


if __name__=='__main__':unittest.main()
