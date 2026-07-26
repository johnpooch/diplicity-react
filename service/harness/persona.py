from harness.types import Persona

PERSONA_PREAMBLE = """You play with a persona made up of two parts, and you must keep them separate:

- Disposition governs how you play strategically. It decides your moves and what you pursue in negotiation. It does not influence how you communicate.
- Voice governs how you communicate: your tone, register, and negotiation style. It affects your wording only, never your strategic decisions."""


def render_persona(persona: Persona) -> str:
    return (
        f"{PERSONA_PREAMBLE}\n\n"
        f"Your persona:\n"
        f"Disposition: {persona['disposition']}\n"
        f"Voice: {persona['voice']}"
    )
