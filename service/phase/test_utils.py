from datetime import time, datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from common.constants import PhaseFrequency
from phase.utils import calculate_next_fixed_deadline, compress_deadline, FREQUENCY_INTERVALS


class TestCalculateNextFixedDeadline:

    @pytest.mark.parametrize("frequency", [
        PhaseFrequency.DAILY,
        PhaseFrequency.EVERY_2_DAYS,
        PhaseFrequency.WEEKLY,
    ])
    def test_returns_future_datetime(self, frequency):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        result = calculate_next_fixed_deadline(target_time, frequency, tz_name)
        assert result > timezone.now()

    def test_hourly_subsequent_advances_to_next_minute_mark(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 14, 30, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.HOURLY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 15
        assert local_result.minute == 0
        assert local_result.second == 0

    def test_hourly_subsequent_at_exact_mark_advances_one_interval(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 14, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.HOURLY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 15
        assert local_result.minute == 0

    def test_hourly_first_phase_uses_target_time_plus_interval(self):
        target_time = time(15, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 13, 47, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.HOURLY, tz_name, reference_time=reference, is_first_phase=True
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.day == 15
        assert local_result.hour == 16
        assert local_result.minute == 0

    def test_hourly_first_phase_target_passed_advances_to_next_day(self):
        target_time = time(15, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 15, 30, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.HOURLY, tz_name, reference_time=reference, is_first_phase=True
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.day == 16
        assert local_result.hour == 16
        assert local_result.minute == 0

    def test_hourly_first_phase_with_nonzero_minutes(self):
        target_time = time(15, 30)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 13, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.HOURLY, tz_name, reference_time=reference, is_first_phase=True
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.day == 15
        assert local_result.hour == 16
        assert local_result.minute == 30

    def test_daily_uses_target_time_same_day(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.DAILY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 21
        assert local_result.minute == 0
        assert local_result.day == 15

    def test_daily_advances_to_next_day_if_target_passed(self):
        target_time = time(9, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.DAILY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 9
        assert local_result.day == 16

    def test_daily_at_exact_target_time_advances(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 21, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.DAILY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.day == 16

    def test_daily_first_phase_adds_one_day_to_next_occurrence(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.DAILY, tz_name, reference_time=reference, is_first_phase=True
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.day == 16
        assert local_result.hour == 21

    def test_daily_first_phase_target_passed_adds_one_day(self):
        target_time = time(9, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.DAILY, tz_name, reference_time=reference, is_first_phase=True
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.day == 17
        assert local_result.hour == 9

    def test_every_2_days_minimum_interval(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.EVERY_2_DAYS, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        days_diff = (local_result.date() - reference.date()).days
        assert days_diff >= 2

    def test_every_2_days_uses_target_time(self):
        target_time = time(15, 30)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.EVERY_2_DAYS, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 15
        assert local_result.minute == 30

    def test_every_2_days_first_phase_adds_two_days(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.EVERY_2_DAYS, tz_name, reference_time=reference, is_first_phase=True
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        days_diff = (local_result.date() - reference.date()).days
        assert days_diff >= 4
        assert local_result.hour == 21

    def test_weekly_minimum_interval(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.WEEKLY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        days_diff = (local_result.date() - reference.date()).days
        assert days_diff >= 7

    def test_weekly_uses_target_time(self):
        target_time = time(18, 45)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.WEEKLY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 18
        assert local_result.minute == 45

    def test_weekly_first_phase_adds_seven_days(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.WEEKLY, tz_name, reference_time=reference, is_first_phase=True
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        days_diff = (local_result.date() - reference.date()).days
        assert days_diff >= 14
        assert local_result.hour == 21

    def test_timezone_conversion_pacific(self):
        target_time = time(21, 0)
        tz_name = "America/Los_Angeles"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("UTC"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.DAILY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 21

    def test_timezone_conversion_europe(self):
        target_time = time(20, 0)
        tz_name = "Europe/London"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("UTC"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.DAILY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 20

    def test_invalid_frequency_raises_error(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"

        with pytest.raises(ValueError, match="Unknown frequency"):
            calculate_next_fixed_deadline(target_time, "invalid", tz_name)

    def test_defaults_to_now_when_no_reference(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"

        result = calculate_next_fixed_deadline(target_time, PhaseFrequency.DAILY, tz_name)
        assert result > timezone.now()

    def test_result_is_timezone_aware(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"

        result = calculate_next_fixed_deadline(target_time, PhaseFrequency.DAILY, tz_name)
        assert result.tzinfo is not None


NOW = datetime(2026, 1, 10, 9, 0, 0, tzinfo=dt_timezone.utc)
DAY = timedelta(hours=24)
HOUR = timedelta(hours=1)
WEEK = timedelta(days=7)
TWO_DAYS = timedelta(days=2)


class TestCompressDeadline:

    def test_daily_on_time_resolution_one_cycle_out_is_unchanged(self):
        next_deadline = NOW + DAY

        result = compress_deadline(next_deadline, PhaseFrequency.DAILY, NOW)

        assert result == NOW + DAY

    def test_daily_run_of_one_and_a_quarter_cycles_is_unchanged(self):
        next_deadline = NOW + timedelta(hours=30)

        result = compress_deadline(next_deadline, PhaseFrequency.DAILY, NOW)

        assert result == NOW + timedelta(hours=30)

    def test_daily_run_just_under_two_cycles_is_unchanged(self):
        next_deadline = NOW + timedelta(hours=47)

        result = compress_deadline(next_deadline, PhaseFrequency.DAILY, NOW)

        assert result == NOW + timedelta(hours=47)

    def test_daily_run_of_exactly_two_cycles_compresses_to_one_cycle(self):
        next_deadline = NOW + timedelta(hours=48)

        result = compress_deadline(next_deadline, PhaseFrequency.DAILY, NOW)

        assert result == NOW + timedelta(hours=24)

    def test_daily_run_of_two_and_a_half_cycles_compresses_to_one_and_a_half(self):
        next_deadline = NOW + timedelta(hours=60)

        result = compress_deadline(next_deadline, PhaseFrequency.DAILY, NOW)

        assert result == NOW + timedelta(hours=36)

    def test_daily_run_of_three_cycles_compresses_to_one_cycle(self):
        next_deadline = NOW + timedelta(hours=72)

        result = compress_deadline(next_deadline, PhaseFrequency.DAILY, NOW)

        assert result == NOW + timedelta(hours=24)

    def test_daily_run_of_three_and_a_third_cycles_compresses_into_range(self):
        next_deadline = NOW + timedelta(hours=80)

        result = compress_deadline(next_deadline, PhaseFrequency.DAILY, NOW)

        assert result == NOW + timedelta(hours=32)

    def test_compression_preserves_wall_clock_grid_slot(self):
        now = datetime(2026, 1, 10, 9, 0, 0, tzinfo=dt_timezone.utc)
        next_deadline = datetime(2026, 1, 13, 21, 0, 0, tzinfo=dt_timezone.utc)

        result = compress_deadline(next_deadline, PhaseFrequency.DAILY, now)

        assert result == datetime(2026, 1, 11, 21, 0, 0, tzinfo=dt_timezone.utc)

    def test_hourly_run_of_one_and_a_half_cycles_is_unchanged(self):
        next_deadline = NOW + timedelta(minutes=90)

        result = compress_deadline(next_deadline, PhaseFrequency.HOURLY, NOW)

        assert result == NOW + timedelta(minutes=90)

    def test_hourly_run_of_two_cycles_compresses_to_one_hour(self):
        next_deadline = NOW + timedelta(minutes=120)

        result = compress_deadline(next_deadline, PhaseFrequency.HOURLY, NOW)

        assert result == NOW + timedelta(minutes=60)

    def test_hourly_run_of_two_and_a_half_cycles_compresses_to_ninety_minutes(self):
        next_deadline = NOW + timedelta(minutes=150)

        result = compress_deadline(next_deadline, PhaseFrequency.HOURLY, NOW)

        assert result == NOW + timedelta(minutes=90)

    def test_every_2_days_run_of_two_and_a_half_cycles_compresses(self):
        next_deadline = NOW + timedelta(hours=120)

        result = compress_deadline(next_deadline, PhaseFrequency.EVERY_2_DAYS, NOW)

        assert result == NOW + timedelta(hours=72)

    def test_weekly_run_of_two_cycles_compresses_to_one_week(self):
        next_deadline = NOW + timedelta(days=14)

        result = compress_deadline(next_deadline, PhaseFrequency.WEEKLY, NOW)

        assert result == NOW + timedelta(days=7)

    def test_weekly_run_of_almost_three_cycles_compresses_into_range(self):
        next_deadline = NOW + timedelta(days=20)

        result = compress_deadline(next_deadline, PhaseFrequency.WEEKLY, NOW)

        assert result == NOW + timedelta(days=13)

    def test_unknown_frequency_returns_deadline_unchanged(self):
        next_deadline = NOW + timedelta(hours=200)

        result = compress_deadline(next_deadline, "invalid", NOW)

        assert result == NOW + timedelta(hours=200)

    @pytest.mark.parametrize("frequency", [
        PhaseFrequency.HOURLY,
        PhaseFrequency.DAILY,
        PhaseFrequency.EVERY_2_DAYS,
        PhaseFrequency.WEEKLY,
    ])
    @pytest.mark.parametrize("cycles", [1.0, 1.1, 1.5, 1.99, 2.0, 2.5, 3.0, 3.5, 5.0, 10.0])
    def test_result_always_lands_in_one_to_two_cycle_range(self, frequency, cycles):
        interval = FREQUENCY_INTERVALS[frequency]
        next_deadline = NOW + interval * cycles

        result = compress_deadline(next_deadline, frequency, NOW)

        run = result - NOW
        assert interval <= run < 2 * interval

    @pytest.mark.parametrize("frequency", [
        PhaseFrequency.HOURLY,
        PhaseFrequency.DAILY,
        PhaseFrequency.EVERY_2_DAYS,
        PhaseFrequency.WEEKLY,
    ])
    @pytest.mark.parametrize("cycles", [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 5.0, 10.0])
    def test_compression_only_subtracts_whole_intervals(self, frequency, cycles):
        interval = FREQUENCY_INTERVALS[frequency]
        next_deadline = NOW + interval * cycles

        result = compress_deadline(next_deadline, frequency, NOW)

        pulled_in = next_deadline - result
        assert pulled_in.total_seconds() % interval.total_seconds() == 0
