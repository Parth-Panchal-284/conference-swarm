import json

from src.memory_agent import (
    remember_interaction,
)

from src.shared_memory import (
    print_recommendation,
    reset_demo,
    seed_demo,
)


def run():
    reset_demo()
    seed_demo()

    print_recommendation(
        "BEFORE AGENT MEMORY"
    )

    print(
        "\nTell the Memory Agent "
        "what happened.\n"
    )

    interaction = input("> ")

    memory = remember_interaction(
        interaction
    )

    print(
        "\nMEMORY AGENT EXTRACTED:"
    )

    print(
        json.dumps(
            memory,
            indent=2,
        )
    )

    print_recommendation(
        "AFTER AGENT MEMORY"
    )


if __name__ == "__main__":
    run()
