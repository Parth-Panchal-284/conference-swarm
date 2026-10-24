import hashlib
import json
import re

from dotenv import load_dotenv
from openai import OpenAI

from src.graph import get_graph


load_dotenv()

client = OpenAI()

DEMO_ID = "shared-memory-demo"


MEMORY_SCHEMA = {
    "type": "object",
    "properties": {
        "met_person": {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"],
                    "additionalProperties": False,
                },
                {"type": "null"},
            ]
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
        "summary": {
            "type": "string"
        },
    },
    "required": [
        "met_person",
        "recommendations",
        "person_topics",
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
    response = client.responses.create(
        model="gpt-6-luna",
        instructions=(
            "You are a conference memory agent. "
            "Extract only facts explicitly stated "
            "by the user. Do not invent facts. "
            "A recommendation includes one person "
	    "suggesting, referring, introducing, or "
	    "telling the user to meet another person. "
            "person_topics means a person is said "
            "to work on or focus on that topic."
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

    met_person = memory.get(
        "met_person"
    )

    if met_person:
        person_id = ensure_person(
            graph,
            met_person["name"],
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

    for item in memory["person_topics"]:
        person_id = ensure_person(
            graph,
            item["person"],
        )

        graph.query(
            """
            MATCH (p:Person {
                person_id: $person_id,
                demo_id: $demo_id
            })

            MERGE (t:Topic {
                name: $topic,
                demo_id: $demo_id
            })

            MERGE (p)-[:WORKS_ON]->(t)
            """,
            params={
                "person_id": person_id,
                "topic": item["topic"],
                "demo_id": DEMO_ID,
            },
        )

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


def remember_interaction(text):
    memory = extract_memory(text)

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
