from falkordb import FalkorDB


GRAPH_NAME = "conference_swarm"


def get_graph():
    db = FalkorDB(
        host="localhost",
        port=6379,
    )
    return db.select_graph(GRAPH_NAME)


def bootstrap_graph():
    graph = get_graph()

    result = graph.query(
        """
        MERGE (app:System {
            name: 'Conference Swarm'
        })
        SET app.status = 'online'
        RETURN app.name, app.status
        """
    )

    return result.result_set[0]


if __name__ == "__main__":
    name, status = bootstrap_graph()
    print(f"{name}: {status}")
