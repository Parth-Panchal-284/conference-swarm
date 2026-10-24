import hashlib
import json
import re

from dotenv import load_dotenv
from openai import OpenAI

from src.graph import get_graph


load_dotenv()

client = None


def _get_client():
    global client
    if client is None:
        client = OpenAI()
    return client

DEMO_ID = "shared-memory-demo"


MEMORY_SCHEMA = {
    "type": "object",
    "properties": {
        "met_people": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    }
                },
                "required": [
                    "name"
                ],
                "additionalProperties": False,
            },
        },
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from_person": {
                        "type": "string"
                    },
                    "to_person": {
                        "type": "string"
                    },
                },
                "required": [
                    "from_person",
                    "to_person",
                ],
                "additionalProperties": False,
            },
        },
        "person_topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "person": {
                        "type": "string"
                    },
                    "topic": {
                        "type": "string"
                    },
                },
                "required": [
                    "person",
                    "topic",
                ],
                "additionalProperties": False,
            },
        },
        "recommended_sessions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from_person": {"type": "string"},
                    "session": {"type": "string"},
                },
                "required": ["from_person", "session"],
                "additionalProperties": False,
            },
        },
        "summary": {
            "type": "string"
        },
    },
    "required": [
        "met_people",
        "recommendations",
        "person_topics",
        "recommended_sessions",
        "summary",
    ],
    "additionalProperties": False,
}


def slugify(value):
    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )

    return value.strip("-")


def extract_memory(text):
    response = _get_client().responses.create(
        model="gpt-6-luna",
        instructions=(
            "You are a conference memory agent. "
            "Extract only facts explicitly stated "
            "by the user. Do not invent facts. "
            "met_people must contain every person "
            "the user explicitly says they met. "
            "A recommendation includes one person "
            "suggesting, referring, introducing, "
            "or telling the user to meet another "
            "person. person_topics means a person "
            "is explicitly said to work on, focus "
            "on, research, or build something "
            "related to that topic."
            " recommended_sessions contains sessions "
            "explicitly suggested by a person."
        ),
        input=text,
        text={
            "format": {
                "type": "json_schema",
                "name": "conference_memory",
                "strict": True,
                "schema": MEMORY_SCHEMA,
            }
        },
    )

    return json.loads(
        response.output_text
    )


def ensure_person(graph, name):
    person_id = slugify(name)

    graph.query(
        """
        MERGE (p:Person {
            person_id: $person_id,
            demo_id: $demo_id
        })

        SET p.name = $name
        """,
        params={
            "person_id": person_id,
            "demo_id": DEMO_ID,
            "name": name,
        },
    )

    return person_id


def ensure_topic(graph, topic):
    normalized_topic = topic.strip()

    graph.query(
        """
        MERGE (t:Topic {
            name: $topic,
            demo_id: $demo_id
        })
        """,
        params={
            "topic": normalized_topic,
            "demo_id": DEMO_ID,
        },
    )

    return normalized_topic


def persist_memory(text, memory):
    graph = get_graph()

    graph.query(
        """
        MERGE (u:User {
            name: 'Parth',
            demo_id: $demo_id
        })
        """,
        params={
            "demo_id": DEMO_ID
        },
    )

    involved_person_ids = set()

    # Persist every explicitly met person.
    for met_person in memory["met_people"]:
        person_id = ensure_person(
            graph,
            met_person["name"],
        )

        involved_person_ids.add(
            person_id
        )

        graph.query(
            """
            MATCH (u:User {
                name: 'Parth',
                demo_id: $demo_id
            })

            MATCH (p:Person {
                person_id: $person_id,
                demo_id: $demo_id
            })

            MERGE (u)-[:MET]->(p)
            """,
            params={
                "demo_id": DEMO_ID,
                "person_id": person_id,
            },
        )

    # Persist warm introductions / recommendations.
    for recommendation in memory[
        "recommendations"
    ]:
        from_id = ensure_person(
            graph,
            recommendation[
                "from_person"
            ],
        )

        to_id = ensure_person(
            graph,
            recommendation[
                "to_person"
            ],
        )

        involved_person_ids.add(
            from_id
        )

        involved_person_ids.add(
            to_id
        )

        graph.query(
            """
            MATCH (a:Person {
                person_id: $from_id,
                demo_id: $demo_id
            })

            MATCH (b:Person {
                person_id: $to_id,
                demo_id: $demo_id
            })

            MERGE (a)-[:RECOMMENDED]->(b)
            """,
            params={
                "from_id": from_id,
                "to_id": to_id,
                "demo_id": DEMO_ID,
            },
        )

    # Persist person -> topic knowledge.
    for item in memory[
        "person_topics"
    ]:
        person_id = ensure_person(
            graph,
            item["person"],
        )
        involved_person_ids.add(
            person_id
        )

        topic = ensure_topic(
            graph,
            item["topic"],
        )

        graph.query(
            """
            MATCH (p:Person {
                person_id: $person_id,
                demo_id: $demo_id
            })

            MATCH (t:Topic {
                name: $topic,
                demo_id: $demo_id
            })

            MERGE (p)-[:WORKS_ON]->(t)
            """,
            params={
                "person_id": person_id,
                "topic": topic,
                "demo_id": DEMO_ID,
            },
        )

    # Persist recommendations to actual conference sessions.
    for item in memory.get("recommended_sessions", []):
        person_id = ensure_person(graph, item["from_person"])
        involved_person_ids.add(person_id)
        graph.query(
            """MATCH (p:Person {person_id: $person_id, demo_id: $demo_id})
            MATCH (s:Session {name: $session, demo_id: $demo_id})
            MERGE (p)-[:RECOMMENDED_SESSION]->(s)""",
            params={"person_id": person_id, "session": item["session"], "demo_id": DEMO_ID},
        )

    # Create a deterministic interaction ID so
    # submitting the same memory twice does not
    # create duplicate interaction nodes.
    interaction_id = (
        "memory-"
        + hashlib.sha1(
            text.encode()
        ).hexdigest()[:12]
    )

    graph.query(
        """
        MATCH (u:User {
            name: 'Parth',
            demo_id: $demo_id
        })

        MERGE (m:Interaction {
            interaction_id: $interaction_id,
            demo_id: $demo_id
        })

        SET
            m.summary = $summary,
            m.raw_text = $raw_text,
            m.source = 'memory agent'

        MERGE (u)-[:REMEMBERS]->(m)
        """,
        params={
            "demo_id": DEMO_ID,
            "interaction_id":
                interaction_id,
            "summary":
                memory["summary"],
            "raw_text": text,
        },
    )

    # Link the memory itself to all people
    # involved in the interaction.
    for person_id in involved_person_ids:
        graph.query(
            """
            MATCH (m:Interaction {
                interaction_id:
                    $interaction_id,
                demo_id: $demo_id
            })

            MATCH (p:Person {
                person_id: $person_id,
                demo_id: $demo_id
            })

            MERGE (m)-[:INVOLVES]->(p)
            """,
            params={
                "interaction_id":
                    interaction_id,
                "person_id":
                    person_id,
                "demo_id":
                    DEMO_ID,
            },
        )


def remember_interaction(text):
    memory = extract_memory(
        text
    )

    persist_memory(
        text,
        memory,
    )

    return memory


if __name__ == "__main__":
    interaction = input(
        "What happened? "
    )

    result = remember_interaction(
        interaction
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )
