from typing import Optional

ADJUDICATION_BASE_URL = "https://godip-adjudication.appspot.com"


class GameStatus:
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (ABANDONED, "Abandoned"),
    )


class MovementPhaseDuration:
    ONE_HOUR = "1 hour"
    TWELVE_HOURS = "12 hours"
    TWENTY_FOUR_HOURS = "24 hours"
    FORTY_EIGHT_HOURS = "48 hours"
    THREE_DAYS = "3 days"
    FOUR_DAYS = "4 days"
    ONE_WEEK = "1 week"
    TWO_WEEKS = "2 weeks"

    MOVEMENT_PHASE_DURATION_CHOICES = (
        (ONE_HOUR, "1 hour"),
        (TWELVE_HOURS, "12 hours"),
        (TWENTY_FOUR_HOURS, "24 hours"),
        (FORTY_EIGHT_HOURS, "48 hours"),
        (THREE_DAYS, "3 days"),
        (FOUR_DAYS, "4 days"),
        (ONE_WEEK, "1 week"),
        (TWO_WEEKS, "2 weeks"),
    )


def duration_to_seconds(duration: Optional[str]) -> Optional[int]:
    if duration is None:
        return None
    duration_map = {
        MovementPhaseDuration.ONE_HOUR: 1 * 60 * 60,
        MovementPhaseDuration.TWELVE_HOURS: 12 * 60 * 60,
        MovementPhaseDuration.TWENTY_FOUR_HOURS: 24 * 60 * 60,
        MovementPhaseDuration.FORTY_EIGHT_HOURS: 48 * 60 * 60,
        MovementPhaseDuration.THREE_DAYS: 3 * 24 * 60 * 60,
        MovementPhaseDuration.FOUR_DAYS: 4 * 24 * 60 * 60,
        MovementPhaseDuration.ONE_WEEK: 7 * 24 * 60 * 60,
        MovementPhaseDuration.TWO_WEEKS: 14 * 24 * 60 * 60,
    }
    return duration_map.get(duration, 0)


class NationAssignment:
    RANDOM = "random"
    ORDERED = "ordered"

    NATION_ASSIGNMENT_CHOICES = (
        (RANDOM, "Random"),
        (ORDERED, "Ordered"),
    )


class PhaseStatus:
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    TEMPLATE = "template"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (TEMPLATE, "Template"),
    )


class PhaseType:
    MOVEMENT = "Movement"
    RETREAT = "Retreat"
    ADJUSTMENT = "Adjustment"

    TYPE_CHOICES = (
        (MOVEMENT, "Movement"),
        (RETREAT, "Retreat"),
        (ADJUSTMENT, "Adjustment"),
    )


class OrderType:
    MOVE = "Move"
    MOVE_VIA_CONVOY = "MoveViaConvoy"
    HOLD = "Hold"
    SUPPORT = "Support"
    CONVOY = "Convoy"
    BUILD = "Build"
    DISBAND = "Disband"

    ORDER_TYPE_CHOICES = (
        (MOVE, "Move"),
        (MOVE_VIA_CONVOY, "Move via Convoy"),
        (HOLD, "Hold"),
        (SUPPORT, "Support"),
        (CONVOY, "Convoy"),
        (BUILD, "Build"),
        (DISBAND, "Disband"),
    )


class OrderCreationStep:
    SELECT_ORDER_TYPE = "select-order-type"
    SELECT_UNIT_TYPE = "select-unit-type"
    SELECT_TARGET = "select-target"
    SELECT_AUX = "select-aux"
    SELECT_NAMED_COAST = "select-named-coast"
    COMPLETED = "completed"

    ORDER_CREATION_STEP_CHOICES = (
        (SELECT_ORDER_TYPE, "select-order-type"),
        (SELECT_UNIT_TYPE, "select-unit-type"),
        (SELECT_TARGET, "select-target"),
        (SELECT_AUX, "select-aux"),
        (SELECT_NAMED_COAST, "select-named-coast"),
        (COMPLETED, "completed"),
    )


class UnitType:
    ARMY = "Army"
    FLEET = "Fleet"

    UNIT_TYPE_CHOICES = (
        (ARMY, "Army"),
        (FLEET, "Fleet"),
    )


class ProvinceType:
    LAND = "land"
    SEA = "sea"
    COASTAL = "coastal"
    NAMED_COAST = "named_coast"

    TYPE_CHOICES = (
        (LAND, "Land"),
        (SEA, "Sea"),
        (COASTAL, "Coastal"),
        (NAMED_COAST, "Named coast"),
    )


class OrderResolutionStatus:
    SUCCEEDED = "OK"
    ILLEGAL_MOVE = "ErrIllegalMove"
    ILLEGAL_DESTINATION = "ErrIllegalDestination"
    BOUNCED = "ErrBounce"
    INVALID_SUPPORT_ORDER = "ErrInvalidSupporteeOrder"
    ILLEGAL_SUPPORT_DESTINATION = "ErrIllegalSupportDestination"
    INVALID_DESTINATION = "ErrInvalidDestination"
    MISSING_SUPPORT_UNIT = "ErrMissingSupportUnit"
    MISSING_UNIT = "ErrMissingUnit"
    SUPPORT_BROKEN = "ErrSupportBroken"

    STATUS_CHOICES = (
        (SUCCEEDED, "Succeeded"),
        (ILLEGAL_MOVE, "Illegal move"),
        (ILLEGAL_DESTINATION, "Illegal destination"),
        (BOUNCED, "Bounced"),
        (INVALID_SUPPORT_ORDER, "Invalid support order"),
        (ILLEGAL_SUPPORT_DESTINATION, "Illegal support destination"),
        (INVALID_DESTINATION, "Invalid destination"),
        (MISSING_SUPPORT_UNIT, "Missing support unit"),
        (MISSING_UNIT, "Missing unit"),
        (SUPPORT_BROKEN, "Support broken"),
    )
