try:
    from src.graph import get_graph
except ModuleNotFoundError:
    from graph import get_graph


DEMO_ID = "shared-memory-demo"


def reset_demo():
    """Delete only nodes belonging to this demo."""
    graph = get_graph()

    graph.query(
        """
        MATCH (n {
            demo_id: 'shared-memory-demo'
        })
        DETACH DELETE n
        """
    )


def seed_demo():
    """Seed the dense, deterministic conference graph."""
    from src.conference_simulator import seed_conference

    seed_conference()


def recommend_next():
    """Recommend using graph-derived evidence."""
    graph = get_graph()

    candidates = graph.query(
        """
        MATCH (u:User {
            name: 'Parth',
            demo_id: 'shared-memory-demo'
        })

        MATCH (p:Person {
            demo_id: 'shared-memory-demo',
            demo_candidate: true
        })

        WHERE NOT (u)-[:MET]->(p)

        RETURN p.person_id, p.name
        """
    )

    if not candidates.result_set:
        return None

    scores = {
        person_id: {
            "name": name,
            "direct": 0,
            "related": 0,
            "warm": 0,
            "scout": 0,
        }
        for person_id, name
        in candidates.result_set
    }

    direct = graph.query(
        """
        MATCH (u:User {
            name: 'Parth',
            demo_id: 'shared-memory-demo'
        })
        -[:INTERESTED_IN]->
        (topic:Topic {
            demo_id: 'shared-memory-demo'
        })
        <-[:WORKS_ON]-
        (p:Person {
            demo_id: 'shared-memory-demo'
        })

        WHERE NOT (u)-[:MET]->(p)

        RETURN
            p.person_id,
            count(DISTINCT topic) * 3
        """
    )

    for person_id, score in direct.result_set:
        if person_id in scores:
            scores[person_id]["direct"] = score

    related = graph.query(
        """
        MATCH (u:User {
            name: 'Parth',
            demo_id: 'shared-memory-demo'
        })
        -[:INTERESTED_IN]->
        (:Topic {
            demo_id: 'shared-memory-demo'
        })
        -[:RELATED_TO]->
        (topic:Topic {
            demo_id: 'shared-memory-demo'
        })
        <-[:WORKS_ON]-
        (p:Person {
            demo_id: 'shared-memory-demo'
        })

        WHERE NOT (u)-[:MET]->(p)

        RETURN
            p.person_id,
            count(DISTINCT topic)
        """
    )

    for person_id, score in related.result_set:
        if person_id in scores:
            scores[person_id]["related"] = score

    warm = graph.query(
        """
        MATCH (u:User {
            name: 'Parth',
            demo_id: 'shared-memory-demo'
        })
        -[:MET]->
        (introducer:Person)
        -[:RECOMMENDED]->
        (p:Person {
            demo_id: 'shared-memory-demo'
        })

        WHERE NOT (u)-[:MET]->(p)

        RETURN
            p.person_id,
            count(DISTINCT introducer) * 5
        """
    )

    for person_id, score in warm.result_set:
        if person_id in scores:
            scores[person_id]["warm"] = score

    scout_matches = graph.query(
        """MATCH (u:User {name: 'Parth', demo_id: 'shared-memory-demo'})
        -[:SCOUT_MATCH]->(p:Person {demo_id: 'shared-memory-demo', demo_candidate: true})
        WHERE NOT (u)-[:MET]->(p)
        RETURN p.person_id, count(DISTINCT p) * 4"""
    )
    for person_id, score in scout_matches.result_set:
        if person_id in scores:
            scores[person_id]["scout"] = score

    # Re-check eligibility after evidence queries.
    eligible = graph.query(
        """
        MATCH (u:User {
            name: 'Parth',
            demo_id: 'shared-memory-demo'
        })

        MATCH (p:Person {
            demo_id: 'shared-memory-demo',
            demo_candidate: true
        })

        WHERE NOT (u)-[:MET]->(p)

        RETURN p.person_id
        """
    )

    eligible_ids = {
        row[0]
        for row in eligible.result_set
    }

    scores = {
        person_id: parts
        for person_id, parts in scores.items()
        if person_id in eligible_ids
    }

    if not scores:
        return None

    best_id = max(
        scores,
        key=lambda person_id: (
            scores[person_id]["direct"]
            + scores[person_id]["related"]
            + scores[person_id]["warm"]
            + scores[person_id]["scout"],
            scores[person_id]["scout"],
            scores[person_id]["direct"],
            scores[person_id]["name"],
        ),
    )

    parts = scores[best_id]

    total = (
        parts["direct"]
        + parts["related"]
        + parts["warm"]
        + parts["scout"]
    )

    return (
        parts["name"],
        total,
        parts["direct"],
        parts["related"],
        parts["warm"],
        parts["scout"],
    )


def log_alice_interaction():
    """Persist one conference interaction as memory."""
    graph = get_graph()

    graph.query(
        """
        MATCH (u:User {
            name: 'Parth',
            demo_id: 'shared-memory-demo'
        })

        MATCH (alice:Person {
            person_id: 'alice',
            demo_id: 'shared-memory-demo'
        })

        MATCH (bob:Person {
            person_id: 'bob',
            demo_id: 'shared-memory-demo'
        })

        MERGE (u)-[:MET]->(alice)

        MERGE (alice)-[:RECOMMENDED]->(bob)

        MERGE (memory:Interaction {
            interaction_id:
                'alice-recommends-bob',
            demo_id:
                'shared-memory-demo'
        })

        ON CREATE SET
            memory.summary =
                'Alice recommended Bob for '
                + 'KV cache optimization',
            memory.source =
                'conference conversation'

        MERGE (u)-[:REMEMBERS]->(memory)

        MERGE (memory)-[:WITH]->(alice)

        MERGE (memory)-[:MENTIONS]->(bob)
        """
    )


def print_recommendation(label):
    """Print the current recommendation."""
    recommendation = recommend_next()

    print(f"\n{label}")

    if recommendation is None:
        print("No recommendation available.")
        return None

    (
        name,
        score,
        direct,
        related,
        warm,
        scout,
    ) = recommendation

    print(f"Recommendation: {name}")
    print(f"Score: {score}")

    print(
        "Reasoning: "
        f"direct={direct}, "
        f"related={related}, "
        f"warm_intro={warm}, "
        f"live_scout={scout}"
    )

    return name


def run_demo():
    """Run the shared-memory demonstration."""
    reset_demo()
    seed_demo()

    before = print_recommendation(
        "BEFORE SHARED MEMORY"
    )

    print(
        "\nMemory Agent learns: "
        "Parth met Alice, and Alice "
        "recommended Bob."
    )

    log_alice_interaction()

    after = print_recommendation(
        "AFTER SHARED MEMORY"
    )

    print(
        "\nRecommendation changed: "
        f"{before} -> {after}"
    )


if __name__ == "__main__":
    run_demo()
