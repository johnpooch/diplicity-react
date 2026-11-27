class BotKind:
    BASIC = "basic"
    AI = "ai"

    KIND_CHOICES = (
        (BASIC, "Basic"),
        (AI, "AI"),
    )


class RunStep:
    DRAW_DECISION = "draw_decision"

    STEP_CHOICES = ((DRAW_DECISION, "Draw decision"),)


class RunStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (RUNNING, "Running"),
        (SUCCEEDED, "Succeeded"),
        (FAILED, "Failed"),
        (TIMED_OUT, "Timed out"),
        (SKIPPED, "Skipped"),
    )


COORDINATE_TASK = "bot.coordinate"
