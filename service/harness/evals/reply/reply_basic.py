from harness.evals.builder import ContextBuilder, nation
from harness.evals.runners import DeterministicEval
from harness.tasks import ReplyTask
from harness.types import TaskContext


def context():
    return (
        ContextBuilder()
        .nation("England")
        .channel(
            id=1,
            name="England, France",
            private=True,
            messages=[
                {
                    "id": 1,
                    "body": "Shall we agree the Channel stays empty this year?",
                    "sender": {"is_current_user": False, "nation": nation("France")},
                }
            ],
        )
        .build()
    )


def check(message, context):
    if message:
        return True, f"non-empty message ({len(message)} char(s))"
    return False, "empty message"


EVAL = DeterministicEval(
    name="reply.basic",
    task=ReplyTask,
    context=context,
    check=check,
    task_ctx=TaskContext(channel_id=1),
)
