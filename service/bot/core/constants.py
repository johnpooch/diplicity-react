class PhaseType:
    MOVEMENT = "Movement"
    RETREAT = "Retreat"
    ADJUSTMENT = "Adjustment"


class OrderType:
    MOVE = "Move"
    MOVE_VIA_CONVOY = "MoveViaConvoy"
    HOLD = "Hold"
    SUPPORT = "Support"
    CONVOY = "Convoy"
    BUILD = "Build"
    DISBAND = "Disband"


class UnitType:
    ARMY = "Army"
    FLEET = "Fleet"


class ProvinceType:
    LAND = "land"
    SEA = "sea"
    COASTAL = "coastal"
    NAMED_COAST = "named_coast"


class ResponseMode:
    LIGHT = "light"
    FULL = "full"


BASIC_BOT_REPLY = "I'm a basic bot, so I can't chat. I'll just play my orders."
