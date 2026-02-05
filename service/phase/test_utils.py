from datetime import time, datetime
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from common.constants import PhaseFrequency
from phase.utils import calculate_next_fixed_deadline


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

    def test_hourly_returns_top_of_next_hour(self):
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

    def test_hourly_at_top_of_hour_goes_to_next(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 14, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.HOURLY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        assert local_result.hour == 15
        assert local_result.minute == 0

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

    def test_weekly_minimum_interval(self):
        target_time = time(21, 0)
        tz_name = "America/New_York"
        reference = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        result = calculate_next_fixed_deadline(
            target_time, PhaseFrequency.WEEKLY, tz_name, reference_time=reference
        )

        local_result = result.astimezone(ZoneInfo(tz_name))
        days_diff = (local_result.date() - reference.date()).days
        assert days_diff >= 6

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
