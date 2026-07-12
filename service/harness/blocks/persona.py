from harness.prompts import load_prompt
from harness.types import Persona


def render_persona(persona: Persona) -> str:
    preamble = load_prompt("persona_system.txt")
    return (
        f"{preamble}\n\n"
        f"Your persona:\n"
        f"Disposition: {persona.disposition}\n"
        f"Voice: {persona.voice}"
    )
