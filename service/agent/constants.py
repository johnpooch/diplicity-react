class AgentTaskKind:
    PLAN = "plan"
    FINALIZE = "finalize"
    REPLY = "reply"

    KIND_CHOICES = (
        (PLAN, "Plan"),
        (FINALIZE, "Finalize"),
        (REPLY, "Reply"),
    )


class AgentTaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (RUNNING, "Running"),
        (SUCCEEDED, "Succeeded"),
        (FAILED, "Failed"),
    )
