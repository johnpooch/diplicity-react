from typing import Optional

from adjudicator.types import ResolutionCode


class GameStatus:
    PENDING = "pending"
    MUSTERING = "mustering"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (MUSTERING, "Mustering"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (ABANDONED, "Abandoned"),
    )


class ResolutionJob:
    TASK_NAME = "phase.resolve_phase"

    TODO = "todo"
    DOING = "doing"
    CANCELLED = "cancelled"

    PENDING_STATUSES = (TODO, DOING)

    @staticmethod
    def lock_for_game(game_id):
        return f"resolve-game-{game_id}"


class MusterJob:
    TASK_NAME = "game.start_if_mustered"
    REMINDER_TASK_NAME = "game.send_muster_reminder"

    TODO = "todo"
    CANCELLED = "cancelled"

    lock_for_game = ResolutionJob.lock_for_game


class MovementPhaseDuration:
    ONE_HOUR = "1 hour"
    TWO_HOURS = "2 hours"
    FOUR_HOURS = "4 hours"
    EIGHT_HOURS = "8 hours"
    TWELVE_HOURS = "12 hours"
    TWENTY_FOUR_HOURS = "24 hours"
    FORTY_EIGHT_HOURS = "48 hours"
    THREE_DAYS = "3 days"
    FOUR_DAYS = "4 days"
    ONE_WEEK = "1 week"
    TWO_WEEKS = "2 weeks"

    MOVEMENT_PHASE_DURATION_CHOICES = (
        (ONE_HOUR, "1 hour"),
        (TWO_HOURS, "2 hours"),
        (FOUR_HOURS, "4 hours"),
        (EIGHT_HOURS, "8 hours"),
        (TWELVE_HOURS, "12 hours"),
        (TWENTY_FOUR_HOURS, "24 hours"),
        (FORTY_EIGHT_HOURS, "48 hours"),
        (THREE_DAYS, "3 days"),
        (FOUR_DAYS, "4 days"),
        (ONE_WEEK, "1 week"),
        (TWO_WEEKS, "2 weeks"),
    )


class DeadlineMode:
    DURATION = "duration"
    FIXED_TIME = "fixed_time"

    DEADLINE_MODE_CHOICES = (
        (DURATION, "Duration"),
        (FIXED_TIME, "Fixed Time"),
    )


class PhaseFrequency:
    HOURLY = "hourly"
    DAILY = "daily"
    EVERY_2_DAYS = "every_2_days"
    WEEKLY = "weekly"

    PHASE_FREQUENCY_CHOICES = (
        (HOURLY, "Hourly"),
        (DAILY, "Daily"),
        (EVERY_2_DAYS, "Every 2 days"),
        (WEEKLY, "Weekly"),
    )


def duration_to_seconds(duration: Optional[str]) -> Optional[int]:
    if duration is None:
        return None
    duration_map = {
        MovementPhaseDuration.ONE_HOUR: 1 * 60 * 60,
        MovementPhaseDuration.TWO_HOURS: 2 * 60 * 60,
        MovementPhaseDuration.FOUR_HOURS: 4 * 60 * 60,
        MovementPhaseDuration.EIGHT_HOURS: 8 * 60 * 60,
        MovementPhaseDuration.TWELVE_HOURS: 12 * 60 * 60,
        MovementPhaseDuration.TWENTY_FOUR_HOURS: 24 * 60 * 60,
        MovementPhaseDuration.FORTY_EIGHT_HOURS: 48 * 60 * 60,
        MovementPhaseDuration.THREE_DAYS: 3 * 24 * 60 * 60,
        MovementPhaseDuration.FOUR_DAYS: 4 * 24 * 60 * 60,
        MovementPhaseDuration.ONE_WEEK: 7 * 24 * 60 * 60,
        MovementPhaseDuration.TWO_WEEKS: 14 * 24 * 60 * 60,
    }
    return duration_map.get(duration, 0)


class PressType:
    FULL_PRESS = "full_press"
    NO_PRESS = "no_press"

    PRESS_TYPE_CHOICES = (
        (FULL_PRESS, "Full Press"),
        (NO_PRESS, "No Press"),
    )


class MinReliability:
    OPEN = "open"
    RELIABLE_AND_NEW = "reliable_and_new"
    RELIABLE_ONLY = "reliable_only"

    MIN_RELIABILITY_CHOICES = (
        (OPEN, "Open"),
        (RELIABLE_AND_NEW, "Reliable + New Players"),
        (RELIABLE_ONLY, "Reliable only"),
    )


class Commitment:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNDEFINED = "undefined"

    COMMITMENT_CHOICES = (
        (HIGH, "High"),
        (MEDIUM, "Medium"),
        (LOW, "Low"),
        (UNDEFINED, "New"),
    )


class UserKind:
    HUMAN = "human"
    LLM = "llm"
    DUMBBOT = "dumbbot"

    KIND_CHOICES = (
        (HUMAN, "Human"),
        (LLM, "LLM"),
        (DUMBBOT, "DumbBot"),
    )

    BOT_KINDS = (LLM, DUMBBOT)


class CommitmentRequirement:
    OPEN = "open"
    COMMITTED = "committed"

    COMMITMENT_REQUIREMENT_CHOICES = (
        (OPEN, "Open"),
        (COMMITTED, "Committed"),
    )


class CommitmentEligibility:
    ELIGIBLE = "eligible"
    COMMITTED_LOCKED = "committed_locked"
    LOW_LOCKED = "low_locked"


class VariantStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    STATUS_CHOICES = (
        (DRAFT, "Draft"),
        (PUBLISHED, "Published"),
        (ARCHIVED, "Archived"),
    )


class PhaseStatus:
    PENDING = "pending"
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    TEMPLATE = "template"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (PROCESSING, "Processing"),
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
    SUCCEEDED = ResolutionCode.SUCCEEDED
    ILLEGAL_MOVE = ResolutionCode.ILLEGAL_MOVE
    ILLEGAL_DESTINATION = ResolutionCode.ILLEGAL_DESTINATION
    BOUNCED = ResolutionCode.BOUNCED
    INVALID_SUPPORT_ORDER = ResolutionCode.INVALID_SUPPORT_ORDER
    ILLEGAL_SUPPORT_DESTINATION = ResolutionCode.ILLEGAL_SUPPORT_DESTINATION
    INVALID_DESTINATION = ResolutionCode.INVALID_DESTINATION
    MISSING_SUPPORT_UNIT = ResolutionCode.MISSING_SUPPORT_UNIT
    MISSING_UNIT = ResolutionCode.MISSING_UNIT
    SUPPORT_BROKEN = ResolutionCode.SUPPORT_BROKEN
    MISSING_CONVOY_PATH = ResolutionCode.MISSING_CONVOY_PATH
    CONVOY_DISLODGED = ResolutionCode.CONVOY_DISLODGED

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
        (MISSING_CONVOY_PATH, "Missing convoy path"),
        (CONVOY_DISLODGED, "Convoy dislodged"),
    )
