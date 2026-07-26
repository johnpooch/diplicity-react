class InferenceProvider:
    ANTHROPIC = "anthropic"

    PROVIDER_CHOICES = ((ANTHROPIC, "Anthropic"),)


class InferenceStatus:
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
