from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import includes
from inspect_ai.solver import generate


@task
def capitals():
    return Task(
        dataset=[
            Sample(input="What is the capital of France?", target="Paris"),
            Sample(input="What is the capital of Japan?", target="Tokyo"),
        ],
        solver=generate(),
        scorer=includes(),
    )
