import json

from brightdata import SyncBrightDataClient
from dotenv import load_dotenv
from openai import OpenAI

from src.graph import get_graph
from src.memory_agent import (
    DEMO_ID,
    ensure_person,
)


load_dotenv()

client = OpenAI()


SCOUT_SCHEMA = {
    "type": "object",
    "properties": {
        "people": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "affiliation": {
                        "type": "string"
                    },
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    },
                    "why_relevant": {
                        "type": "string"
                    },
                    "source_url": {
                        "type": "string"
                    },
                    "source_title": {
                        "type": "string"
                    },
                },
                "required": [
                    "name",
                    "affiliation",
                    "topics",
                    "why_relevant",
                    "source_url",
                    "source_title",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": [
        "people"
    ],
    "additionalProperties": False,
}


def brightdata_search(query):
    """
    Search the live public web through Bright Data.
    """
    with SyncBrightDataClient(
        auto_create_zones=True
    ) as bd:
        result = bd.search.google(
            query=query,
            num_results=8,
        )

    if not result.success:
        return []

    rows = []

    for item in result.data:
        url = (
            item.get("url")
            or item.get("link")
            or ""
        )

        if not url:
            continue

        rows.append(
            {
                "title":
                    item.get("title") or "",
                "url":
                    url,
                "description":
                    item.get("description") or "",
            }
        )

    return rows


def collect_live_evidence(goal):
    """
    Run several targeted searches so one weak SERP
    does not determine the whole Scout result.
    """
    queries = [
        (
            '"Patch the Conference" '
            'hackathon judges AI agents '
            'LLM infrastructure'
        ),
        (
            '"Patch the Conference" '
            'FalkorDB Bright Data '
            'OpenAI judges'
        ),
        (
            f'"Patch the Conference" {goal}'
        ),
        (
            f'"GitHub Universe" '
            f'"San Francisco" {goal}'
        ),
    ]

    combined = []
    seen_urls = set()

    for query in queries:
        results = brightdata_search(
            query
        )

        for result in results:
            url = result["url"]

            if url in seen_urls:
                continue

            seen_urls.add(url)

            result["search_query"] = query

            combined.append(
                result
            )

    return combined


def extract_people(goal, evidence):
    """
    Use OpenAI to convert Bright Data SERP
    evidence into graph-ready entities.
    """
    evidence_json = json.dumps(
        evidence,
        indent=2,
    )

    response = client.responses.create(
        model="gpt-6-luna",
        instructions=(
    		"You are the Scout Agent for a "
    		"conference networking system. "
    		"You receive live web search evidence "
    		"retrieved through Bright Data. "
    		"Find up to 5 real named people who are "
    		"EXPLICITLY connected in the supplied "
    		"evidence to Patch the Conference, "
    		"WeMakeDevs, its judges, organizers, "
    		"sponsors, or GitHub Universe. "
    		"They should also be relevant to the "
    		"user's technical goal when possible. "
    		"Do not return unrelated people just "
    		"because they match the technical topic. "
    		"If only 2 qualified people exist, "
    		"return only 2. "
    		"Do not invent names, affiliations, "
    		"topics, or URLs. "
    		"Every returned person must be supported "
    		"by one supplied source URL. "
    		"Use short technical topic labels."
	),
        input=(
            f"USER GOAL:\n{goal}\n\n"
            "BRIGHT DATA LIVE WEB EVIDENCE:\n"
            f"{evidence_json}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name":
                    "conference_scout_results",
                "strict": True,
                "schema": SCOUT_SCHEMA,
            }
        },
    )

    return json.loads(
        response.output_text
    )


def persist_scout_results(
    goal,
    scout_results,
):
    """
    Persist live Scout discoveries into the
    same FalkorDB graph used by other agents.
    """
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

    for person in scout_results[
        "people"
    ]:
        person_id = ensure_person(
            graph,
            person["name"],
        )

        graph.query(
            """
            MATCH (p:Person {
                person_id: $person_id,
                demo_id: $demo_id
            })

            SET
                p.affiliation =
                    $affiliation,
                p.scout_reason =
                    $why_relevant,
                p.discovered_by =
                    'Bright Data Scout Agent'
            """,
            params={
                "person_id": person_id,
                "demo_id": DEMO_ID,
                "affiliation":
                    person["affiliation"],
                "why_relevant":
                    person["why_relevant"],
            },
        )

        graph.query(
            """
            MERGE (s:Source {
                url: $url,
                demo_id: $demo_id
            })

            SET
                s.title = $title,
                s.provider = 'Bright Data'

            WITH s

            MATCH (p:Person {
                person_id: $person_id,
                demo_id: $demo_id
            })

            MERGE (p)-[:SOURCED_FROM]->(s)
            """,
            params={
                "url":
                    person["source_url"],
                "title":
                    person["source_title"],
                "person_id":
                    person_id,
                "demo_id":
                    DEMO_ID,
            },
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

            MERGE (u)-[r:SCOUT_MATCH]->(p)

            SET
                r.goal = $goal,
                r.reason = $reason,
                r.source = 'Bright Data'
            """,
            params={
                "person_id": person_id,
                "demo_id": DEMO_ID,
                "goal": goal,
                "reason":
                    person["why_relevant"],
            },
        )

        for topic in person["topics"]:
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
                    "person_id":
                        person_id,
                    "topic":
                        topic.strip(),
                    "demo_id":
                        DEMO_ID,
                },
            )


def scout(goal):
    """
    Full Scout Agent:
    Bright Data -> OpenAI -> FalkorDB.
    """
    evidence = collect_live_evidence(
        goal
    )

    if not evidence:
        return {
            "people": [],
            "evidence_count": 0,
        }

    results = extract_people(
        goal,
        evidence,
    )

    persist_scout_results(
        goal,
        results,
    )

    results[
        "evidence_count"
    ] = len(evidence)

    return results


if __name__ == "__main__":
    goal = (
        "LLM inference, sparse attention, "
        "AI agent infrastructure, and "
        "machine learning systems"
    )

    print(
        "\nScout Agent searching live web "
        "through Bright Data...\n"
    )

    result = scout(goal)

    print(
        json.dumps(
            result,
            indent=2,
        )
    )
