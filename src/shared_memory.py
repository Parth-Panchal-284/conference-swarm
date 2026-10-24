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
    """Seed a small conference knowledge graph."""
    graph = get_graph()

    graph.query(
        """
        MERGE (u:User {
            name: 'Parth',
            demo_id: 'shared-memory-demo'
        })

        MERGE (sparse:Topic {
            name: 'Sparse Attention',
            demo_id: 'shared-memory-demo'
        })

        MERGE (kv:Topic {
            name: 'KV Cache Optimization',
            demo_id: 'shared-memory-demo'
        })

        MERGE (alice:Person {
            name: 'Alice',
            demo_id: 'shared-memory-demo'
        })

        MERGE (bob:Person {
            name: 'Bob',
            demo_id: 'shared-memory-demo'
        })

        MERGE (u)-[:INTERESTED_IN]->(sparse)

        MERGE (sparse)-[:RELATED_TO]->(kv)

        MERGE (alice)-[:WORKS_ON]->(sparse)

        MERGE (bob)-[:WORKS_ON]->(kv)
        """
    )


def recommend_next():
    """Recommend the next person from graph context."""
    graph = get_graph()

    result = graph.query(
        """
        MATCH (u:User {
            name: 'Parth',
            demo_id: 'shared-memory-demo'
        })

        MATCH (p:Person {
            demo_id: 'shared-memory-demo'
        })

        WHERE NOT (u)-[:MET]->(p)

        OPTIONAL MATCH
            (u)-[:INTERESTED_IN]->
            (direct:Topic {
                demo_id: 'shared-memory-demo'
            })
            <-[:WORKS_ON]-(p)

        WITH
            u,
            p,
            count(DISTINCT direct) * 3
                AS direct_score

        OPTIONAL MATCH
            (u)-[:INTERESTED_IN]->
            (:Topic {
                demo_id: 'shared-memory-demo'
            })
            -[:RELATED_TO]->
            (related:Topic {
                demo_id: 'shared-memory-demo'
            })
            <-[:WORKS_ON]-(p)

        WITH
            u,
            p,
            direct_score,
            count(DISTINCT related)
                AS related_score

        OPTIONAL MATCH
            (u)-[:MET]->
            (m:Person {
                demo_id: 'shared-memory-demo'
            })
            -[:RECOMMENDED]->(p)

        WITH
            p,
            direct_score,
            related_score,
            count(DISTINCT m) * 5
                AS warm_score

        RETURN
            p.name,
            direct_score
                + related_score
                + warm_score AS score,
            direct_score,
            related_score,
            warm_score

        ORDER BY score DESC
        LIMIT 1
        """
    )

    if not result.result_set:
        return None

    return result.result_set[0]


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
            name: 'Alice',
            demo_id: 'shared-memory-demo'
        })

        MATCH (bob:Person {
            name: 'Bob',
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
    ) = recommendation

    print(f"Recommendation: {name}")
    print(f"Score: {score}")

    print(
        "Reasoning: "
        f"direct={direct}, "
        f"related={related}, "
        f"warm_intro={warm}"
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
