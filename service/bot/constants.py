BOT_USER_USERNAME = "diplicitybot"
BOT_USER_NAME = "Diplicity Bot"


class LLMCallStage:
    PLAN = "plan"
    NEGOTIATE = "negotiate"
    COMMIT = "commit"
    REPLY = "reply"

    STAGE_CHOICES = (
        (PLAN, "Plan"),
        (NEGOTIATE, "Negotiate"),
        (COMMIT, "Commit"),
        (REPLY, "Reply"),
    )


class LLMCallStatus:
    SUCCESS = "success"
    ERROR = "error"

    STATUS_CHOICES = (
        (SUCCESS, "Success"),
        (ERROR, "Error"),
    )
