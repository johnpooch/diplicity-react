from harness.evals.builder import ContextBuilder


def base_context():
    return (
        ContextBuilder()
        .nation("England")
        .order("lon", "Hold")
        .order("lon", "Move", target="wal")
        .order("nth", "Hold")
        .order("nth", "Move", target="edi")
        .build()
    )
