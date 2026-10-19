from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser, Model, get_model
from inspect_ai.solver import solver

from games.play import Policy, dumbbot_seats, opening_position, play
from select_orders.context import fixture_to_context
from select_orders.exceptions import ParsingError
from select_orders.parser import parse_completion
from select_orders.prompt import system_prompt, user_prompt
from select_orders.utils import parse_json_object

GAME_STORE_KEY = "phases"


def opening_prompts(nation: str) -> tuple[str, str]:
    context = fixture_to_context(opening_position(nation))
    return system_prompt(context), user_prompt(context)


def _reasoning(completion: str) -> str | None:
    reasoning = parse_json_object(completion).get("reasoning")
    return reasoning if isinstance(reasoning, str) else None


def model_player(model: Model) -> Policy:
    async def turn(here: dict) -> dict:
        context = fixture_to_context(here)
        system, user = system_prompt(context), user_prompt(context)
        answer = {"system": system, "user": user, "completion": None, "reasoning": None, "problem": None}
        try:
            output = await model.generate([ChatMessageSystem(content=system), ChatMessageUser(content=user)])
        except Exception as e:
            return {"orders": [], **answer, "problem": f"model call failed: {e}"}
        answer["completion"] = output.completion
        if output.error:
            return {"orders": [], **answer, "problem": output.error}
        try:
            orders = parse_completion(output.completion, context)
        except ParsingError as e:
            return {"orders": [], **answer, "problem": str(e)}
        return {"orders": orders, **answer, "reasoning": _reasoning(output.completion)}

    return turn


@solver
def game_solver():
    async def solve(state, generate):
        nation, seed = state.metadata["nation"], state.metadata["seed"]
        game = await play({**dumbbot_seats(seed), nation: model_player(get_model())}, nation)
        paired = await play(dumbbot_seats(seed), nation)
        state.store.set(GAME_STORE_KEY, game["phases"])
        state.metadata.update({"centres": game["centres"], "end": game["end"], "paired_centres": paired["centres"]})
        return state

    return solve


def game_sample(nation: str, seed: int) -> Sample:
    system, user = opening_prompts(nation)
    return Sample(
        id=seed,
        input=[ChatMessageSystem(content=system), ChatMessageUser(content=user)],
        metadata={"nation": nation, "seed": seed},
    )


@task
def play_game(nation: str, first_seed: int = 0, games: int = 1):
    return Task(
        dataset=MemoryDataset([game_sample(nation, seed) for seed in range(first_seed, first_seed + games)]),
        solver=game_solver(),
    )
