from harness.prompts import load_prompt
from harness.types import Persona

PERSONA_PREAMBLE = load_prompt("persona_system.txt")


def render_persona(persona: Persona) -> str:
    return (
        f"{PERSONA_PREAMBLE}\n\n"
        f"Your persona:\n"
        f"Disposition: {persona.disposition}\n"
        f"Voice: {persona.voice}"
    )
