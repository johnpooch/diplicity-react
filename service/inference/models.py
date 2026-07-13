from django.db import models
from django.utils import timezone

from common.models import BaseModel
from inference.clients.registry import get_inference_client
from inference.constants import InferenceProvider, InferenceStatus
from inference.exceptions import InferenceError


class InferenceManager(models.Manager):
    def run(
        self,
        *,
        provider,
        model,
        task,
        system="",
        messages=None,
        user_content="",
        phase=None,
        member=None,
        channel=None,
        output_schema=None,
        max_tokens=None,
    ) -> "Inference":
        if messages is None:
            messages = [{"role": "user", "content": user_content}]
        else:
            user_content = "\n\n".join(message["content"] for message in messages)

        inference = self.create(
            phase=phase,
            member=member,
            channel=channel,
            task=task,
            status=InferenceStatus.PENDING,
            provider=provider,
            model=model,
            system=system,
            user_content=user_content,
        )
        inference.status = InferenceStatus.RUNNING
        inference.started_at = timezone.now()
        inference.save(update_fields=["status", "started_at", "updated_at"])

        try:
            client = get_inference_client(provider)
            result = client.complete(
                model=model,
                system=system,
                messages=messages,
                output_schema=output_schema,
                max_tokens=max_tokens,
            )
        except InferenceError as e:
            inference.status = InferenceStatus.FAILED
            inference.error_message = str(e)
            inference.completed_at = timezone.now()
            inference.save(
                update_fields=["status", "error_message", "completed_at", "updated_at"]
            )
            raise

        inference.status = InferenceStatus.SUCCEEDED
        inference.model = result.model
        inference.response = result.text
        inference.input_tokens = result.input_tokens
        inference.output_tokens = result.output_tokens
        inference.cache_read_tokens = result.cache_read_tokens
        inference.cache_write_tokens = result.cache_write_tokens
        inference.completed_at = timezone.now()
        inference.save(
            update_fields=[
                "status",
                "model",
                "response",
                "input_tokens",
                "output_tokens",
                "cache_read_tokens",
                "cache_write_tokens",
                "completed_at",
                "updated_at",
            ]
        )
        return inference


class Inference(BaseModel):
    objects = InferenceManager()

    phase = models.ForeignKey(
        "phase.Phase",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="inferences",
    )
    member = models.ForeignKey(
        "member.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inferences",
    )
    channel = models.ForeignKey(
        "channel.Channel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inferences",
    )
    task = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=InferenceStatus.STATUS_CHOICES,
        default=InferenceStatus.PENDING,
    )
    provider = models.CharField(
        max_length=20,
        choices=InferenceProvider.PROVIDER_CHOICES,
        default=InferenceProvider.ANTHROPIC,
    )
    model = models.CharField(max_length=255)
    system = models.TextField(blank=True)
    user_content = models.TextField(blank=True)
    response = models.TextField(blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cache_read_tokens = models.PositiveIntegerField(default=0)
    cache_write_tokens = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def latency_ms(self):
        if self.started_at is None or self.completed_at is None:
            return None
        return int((self.completed_at - self.started_at).total_seconds() * 1000)

    def __str__(self):
        return f"{self.task} inference ({self.status}) for phase {self.phase_id}"
