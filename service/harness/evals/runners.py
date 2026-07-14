from dataclasses import dataclass, field
from typing import Callable

from django.conf import settings

from harness.exceptions import ParseError
from harness.prompt import build_prompt
from harness.tasks.base import TaskDefinition
from harness.types import ContextData, TaskContext
from inference.constants import InferenceProvider
from inference.exceptions import InferenceError
from inference.models import Inference


@dataclass
class DeterministicEval:
    name: str
    task: type[TaskDefinition]
    context: Callable[[], ContextData]
    check: Callable[[object, ContextData], tuple[bool, str]]
    task_ctx: TaskContext = field(default_factory=TaskContext)

    def run(self, stdout):
        context = self.context()
        prompt = build_prompt(self.task, context, self.task_ctx)
        try:
            inference = Inference.objects.run(
                provider=InferenceProvider.ANTHROPIC,
                model=settings.BOT_LLM_MODEL,
                task=self.task.name,
                system=prompt.system,
                user_content=prompt.user_content,
                output_schema=prompt.output_schema,
                max_tokens=prompt.max_tokens,
            )
        except InferenceError as e:
            stdout.write(f"{self.name}: FAIL — inference error: {e} (tokens: n/a)")
            return
        tokens = inference.input_tokens + inference.output_tokens
        try:
            result = self.task.parse(inference.response, context=context)
        except ParseError as e:
            stdout.write(f"{self.name}: FAIL — parse error: {e} (tokens: {tokens})")
            return
        passed, reason = self.check(result, context)
        verdict = "PASS" if passed else "FAIL"
        stdout.write(f"{self.name}: {verdict} — {reason} (tokens: {tokens})")
