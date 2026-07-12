from django.conf import settings

from harness.evals.fixtures import reply_context, select_orders_context
from harness.exceptions import ParseError
from harness.orders import group_options_by_source, option_to_selected
from harness.prompt import build_prompt
from harness.tasks import ReplyTask, SelectOrdersTask
from harness.types import TaskContext
from inference.constants import InferenceProvider
from inference.exceptions import InferenceError
from inference.models import Inference


def _check_select_orders(selections, context):
    legal_by_source = {
        source_id: [option_to_selected(option) for option in options]
        for source_id, options in group_options_by_source(context["orders"]).items()
    }
    for selection in selections:
        if selection not in legal_by_source.get(selection[0], []):
            return False, f"illegal selection {selection}"
    return True, f"{len(selections)} legal selection(s)"


def _check_reply(message, context):
    if message:
        return True, f"non-empty message ({len(message)} char(s))"
    return False, "empty message"


CASES = {
    "select_orders": (SelectOrdersTask, select_orders_context, TaskContext(), _check_select_orders),
    "reply": (ReplyTask, reply_context, TaskContext(channel_id=1), _check_reply),
}


def run(stdout, task_name=None):
    if not settings.ANTHROPIC_API_KEY:
        stdout.write("skip: ANTHROPIC_API_KEY is not set")
        return

    names = [task_name] if task_name else list(CASES)
    for name in names:
        task, context_factory, task_ctx, check = CASES[name]
        context = context_factory()
        prompt = build_prompt(task, context, task_ctx)
        try:
            inference = Inference.objects.run(
                provider=InferenceProvider.ANTHROPIC,
                model=settings.BOT_LLM_MODEL,
                task=task.name,
                system=prompt.system,
                user_content=prompt.user_content,
                output_schema=prompt.output_schema,
                max_tokens=prompt.max_tokens,
            )
        except InferenceError as e:
            stdout.write(f"{name}: FAIL — inference error: {e} (tokens: n/a)")
            continue
        tokens = inference.input_tokens + inference.output_tokens
        try:
            result = task.parse(inference.response, context=context)
        except ParseError as e:
            stdout.write(f"{name}: FAIL — parse error: {e} (tokens: {tokens})")
            continue
        passed, reason = check(result, context)
        verdict = "PASS" if passed else "FAIL"
        stdout.write(f"{name}: {verdict} — {reason} (tokens: {tokens})")
