from src.graph import get_graph


def reset_demo():
    graph = get_graph()
    graph.query("MATCH (n) DETACH DELETE n")


def seed_demo():
    graph = get_graph()

    graph.query(
        """
        MERGE (u:User {name: 'Parth'})

        MERGE (sparse:Topic {
            name: 'Sparse Attention'
        })

        MERGE (kv:Topic {
            name: 'KV Cache Optimization'
        })

        MERGE (alice:Person {
            name: 'Alice'
        })

        MERGE (bob:Person {
            name: 'Bob'
        })

        MERGE (u)-[:INTERESTED_IN]->(sparse)

        MERGE (sparse)-[:RELATED_TO]->(kv)

        MERGE (alice)-[:WORKS_ON]->(sparse)

        MERGE (bob)-[:WORKS_ON]->(kv)
        """
    )


def recommend_next():
    graph = get_graph()

    result = graph.query(
        """
        MATCH (u:User {name: 'Parth'})
        MATCH (p:Person)

        WHERE NOT (u)-[:MET]->(p)

        OPTIONAL MATCH
          (u)-[:INTERESTED_IN]->(direct:Topic)
          <-[:WORKS_ON]-(p)

        WITH
          u,
          p,
          count(direct) * 3 AS direct_score

        OPTIONAL MATCH
          (u)-[:INTERESTED_IN]->(:Topic)
          -[:RELATED_TO]->(related:Topic)
          <-[:WORKS_ON]-(p)

        WITH
          u,
          p,
          direct_score,
          count(related) AS related_score

        OPTIONAL MATCH
          (u)-[:MET]->(m:Person)
          -[:RECOMMENDED]->(p)

        WITH
          p,
          direct_score,
          related_score,
          count(m) * 5 AS warm_score

        RETURN
          p.name,
          direct_score + related_score
            + warm_score AS score,
          direct_score,
          related_score,
          warm_score

        ORDER BY score DESC
        LIMIT 1
        """
    )

    return result.result_set[0]


def log_alice_interaction():
    graph = get_graph()

    graph.query(
        """
        MATCH (u:User {name: 'Parth'})
        MATCH (alice:Person {name: 'Alice'})
        MATCH (bob:Person {name: 'Bob'})

        MERGE (u)-[:MET]->(alice)

        MERGE (alice)-[:RECOMMENDED]->(bob)

        CREATE (memory:Interaction {
            summary:
              'Alice recommended Bob for KV cache optimization',
            source: 'conference conversation'
        })

        CREATE (u)-[:REMEMBERS]->(memory)
        CREATE (memory)-[:WITH]->(alice)
        CREATE (memory)-[:MENTIONS]->(bob)
        """
    )


def print_recommendation(label):
    (
        name,
        score,
        direct,
        related,
        warm,
    ) = recommend_next()

    print(f"\n{label}")
    print(f"Recommendation: {name}")
    print(f"Score: {score}")
    print(
        "Reasoning: "
        f"direct={direct}, "
        f"related={related}, "
        f"warm_intro={warm}"
    )

    return name


if __name__ == "__main__":
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
        f"\nRecommendation changed: "
        f"{before} -> {after}"
    )
