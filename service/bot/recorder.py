import logging

from member.models import Member

from bot.constants import LLMCallStatus
from bot.models import LLMCall

logger = logging.getLogger(__name__)


class LLMCallRecorder:
    def __init__(self, *, game_id, user_id, phase_id, stage, channel_id=None):
        self.game_id = game_id
        self.user_id = user_id
        self.phase_id = phase_id
        self.stage = stage
        self.channel_id = channel_id

    def record_success(
        self,
        *,
        model,
        system,
        user_content,
        response,
        input_tokens,
        output_tokens,
        cache_read_tokens,
        cache_write_tokens,
        latency_ms,
    ):
        self._create(
            status=LLMCallStatus.SUCCESS,
            model=model,
            system=system,
            user_content=user_content,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            latency_ms=latency_ms,
        )

    def record_error(self, *, model, system, user_content, error_message, latency_ms):
        self._create(
            status=LLMCallStatus.ERROR,
            model=model,
            system=system,
            user_content=user_content,
            error_message=error_message,
            latency_ms=latency_ms,
        )

    def _create(self, **fields):
        if self.phase_id is None:
            logger.warning(f"[bot.llm] no phase id; skipping LLMCall record for stage={self.stage}")
            return
        try:
            member = Member.objects.filter(game_id=self.game_id, user_id=self.user_id).first()
            LLMCall.objects.create(
                phase_id=self.phase_id,
                member=member,
                channel_id=self.channel_id,
                stage=self.stage,
                **fields,
            )
        except Exception as e:
            logger.error(f"[bot.llm] failed to record LLMCall: {e}")
