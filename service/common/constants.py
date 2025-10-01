ADJUDICATION_BASE_URL = "https://godip-adjudication.appspot.com"


class GameStatus:
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
    )


class MovementPhaseDuration:
    TWENTY_FOUR_HOURS = "24 hours"
    FORTY_EIGHT_HOURS = "48 hours"

    MOVEMENT_PHASE_DURATION_CHOICES = (
        (TWENTY_FOUR_HOURS, "24 hours"),
        (FORTY_EIGHT_HOURS, "48 hours"),
    )


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
    HOLD = "Hold"
    SUPPORT = "Support"
    CONVOY = "Convoy"
    BUILD = "Build"
    DISBAND = "Disband"

    ORDER_TYPE_CHOICES = (
        (MOVE, "Move"),
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
    COMPLETED = "completed"

    ORDER_CREATION_STEP_CHOICES = (
        (SELECT_ORDER_TYPE, "select-order-type"),
        (SELECT_UNIT_TYPE, "select-unit-type"),
        (SELECT_TARGET, "select-target"),
        (SELECT_AUX, "select-aux"),
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

    STATUS_CHOICES = (
        (SUCCEEDED, "Succeeded"),
        (ILLEGAL_MOVE, "Illegal move"),
        (ILLEGAL_DESTINATION, "Illegal destination"),
        (BOUNCED, "Bounced"),
        (INVALID_SUPPORT_ORDER, "Invalid support order"),
        (ILLEGAL_SUPPORT_DESTINATION, "Illegal support destination"),
        (INVALID_DESTINATION, "Invalid destination"),
        (MISSING_SUPPORT_UNIT, "Missing support unit"),
    )
