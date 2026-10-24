"""Deterministic conference-scale graph seed for the live demo."""

import random

from src.graph import get_graph
from src.memory_agent import DEMO_ID


TOPICS = [
    "AI Agents", "Sparse Attention", "KV Cache Optimization", "LLM Inference",
    "GraphRAG", "Agent Memory", "ML Systems", "GPU Systems", "AI Security",
    "Developer Tools", "Open Source", "Evaluation", "Multimodal AI",
    "Retrieval", "Data Infrastructure", "Model Serving", "Robotics",
    "Privacy Engineering", "Observability", "Distributed Training",
]
COMPANIES = [
    "Northstar AI", "Vector Forge", "Open Systems Lab", "Cloudframe",
    "SignalWorks", "Tensor Harbor", "Graphline", "Prompt Foundry",
    "Orbit Compute", "Model Harbor", "Circuit AI", "Fieldnote",
    "Deepstack", "Runtime Labs", "Brightpath", "Kernel Works",
    "Atlas Data", "Relay Robotics", "Traceform", "Common Ground",
]
ZONES = [
    "Main Stage", "Expo Hall A", "Expo Hall B", "AI Lounge",
    "Developer Lounge", "Workshop Wing", "Cafe", "Atrium",
]
SESSIONS = [
    ("Agent Memory in Production", "Stage 2", "Agent Memory"),
    ("Scaling LLM Inference", "Main Stage", "LLM Inference"),
    ("GraphRAG for Agent Systems", "Workshop Wing", "GraphRAG"),
    ("Sparse Models, Fast Systems", "Stage 2", "Sparse Attention"),
    ("Building Reliable AI Agents", "Main Stage", "AI Agents"),
    ("Open Source Model Serving", "Expo Hall A", "Open Source"),
    ("GPU Systems Roundtable", "Workshop Wing", "GPU Systems"),
    ("Securing Agent Workflows", "Expo Hall B", "AI Security"),
    ("Evaluation Beyond Benchmarks", "Atrium", "Evaluation"),
    ("Multimodal Retrieval Lab", "Workshop Wing", "Multimodal AI"),
    ("The Future of Developer Tools", "Developer Lounge", "Developer Tools"),
    ("Training at the Edge", "Main Stage", "Distributed Training"),
]
HERO_PEOPLE = [
    {"name": "Alice", "person_id": "alice", "topics": ["Sparse Attention"], "zone": "Expo Hall A", "booth": "A7", "company": "Northstar AI"},
    {"name": "Bob", "person_id": "bob", "topics": ["KV Cache Optimization", "LLM Inference"], "zone": "Expo Hall B", "booth": "B12", "company": "Tensor Harbor"},
    {"name": "Cameron", "person_id": "cameron", "topics": ["AI Agents", "Agent Memory"], "zone": "AI Lounge", "booth": "A3", "company": "Graphline"},
]


def _write_nodes(graph, label, rows):
    graph.query(
        f"""UNWIND $rows AS row
        MERGE (n:{label} {{id: row.id, demo_id: $demo_id}})
        SET n += row""",
        params={"rows": rows, "demo_id": DEMO_ID},
    )


def _write_edges(graph, cypher, rows):
    if rows:
        graph.query(cypher, params={"rows": rows, "demo_id": DEMO_ID})


def seed_conference(reset=False):
    """Build a clearly labeled synthetic 150-attendee conference graph."""
    graph = get_graph()
    if reset:
        graph.query(
            "MATCH (n {demo_id: $demo_id}) DETACH DELETE n",
            params={"demo_id": DEMO_ID},
        )

    _write_nodes(graph, "Event", [{"id": "patch-the-conference", "name": "Patch the Conference", "date": "2026-10-24", "location": "San Francisco", "simulated": False}])
    _write_nodes(graph, "Zone", [{"id": z.lower().replace(" ", "-"), "name": z, "kind": "conference-zone"} for z in ZONES])
    _write_nodes(graph, "Topic", [{"id": t.lower().replace(" ", "-"), "name": t} for t in TOPICS])
    _write_nodes(graph, "Company", [{"id": c.lower().replace(" ", "-"), "name": c} for c in COMPANIES])
    booths = [{"id": f"booth-{i+1}", "name": f"Booth {i+1}", "code": f"{'A' if i < 6 else 'B'}{i+1}", "zone": ZONES[i % 8]} for i in range(12)]
    _write_nodes(graph, "Booth", booths)
    sessions = [{"id": f"session-{i+1}", "name": name, "zone": zone, "topic": topic, "starts_in_minutes": [18, 32, 48, 64, 78, 90, 24, 42, 56, 70, 84, 96][i]} for i, (name, zone, topic) in enumerate(SESSIONS)]
    _write_nodes(graph, "Session", sessions)

    rng = random.Random(42)
    people = []
    for hero in HERO_PEOPLE:
        people.append({"id": hero["person_id"], "person_id": hero["person_id"], "name": hero["name"], "simulated": True, "demo_candidate": True, "demo_id": DEMO_ID})
    for i in range(150):
        pid = f"attendee-{i+1:03d}"
        people.append({"id": pid, "person_id": pid, "name": f"Attendee {i+1:03d}", "simulated": True, "demo_candidate": False, "demo_id": DEMO_ID})
    # _write_nodes uses the ID as a stable key and preserves the synthetic-data marker.
    _write_nodes(graph, "Person", people)

    work_rows, company_rows, location_rows, attend_rows = [], [], [], []
    for i, person in enumerate(people):
        if i < len(HERO_PEOPLE):
            h = HERO_PEOPLE[i]
            topics, company, zone = h["topics"], h["company"], h["zone"]
        else:
            topics = rng.sample(TOPICS, 3)
            company, zone = rng.choice(COMPANIES), rng.choice(ZONES)
        for topic in topics:
            work_rows.append({"person_id": person["person_id"], "topic_id": topic.lower().replace(" ", "-")})
        company_rows.append({"person_id": person["person_id"], "company_id": company.lower().replace(" ", "-")})
        location_rows.append({"person_id": person["person_id"], "zone_id": zone.lower().replace(" ", "-")})
        attend_rows.append({"person_id": person["person_id"], "session_id": f"session-{(i % len(SESSIONS))+1}"})

    _write_edges(graph, """UNWIND $rows AS row
        MATCH (p:Person {person_id: row.person_id, demo_id: $demo_id})
        MATCH (t:Topic {id: row.topic_id, demo_id: $demo_id})
        MERGE (p)-[:WORKS_ON]->(t)""", work_rows)
    _write_edges(graph, """UNWIND $rows AS row
        MATCH (p:Person {person_id: row.person_id, demo_id: $demo_id})
        MATCH (c:Company {id: row.company_id, demo_id: $demo_id})
        MERGE (p)-[:AFFILIATED_WITH]->(c)""", company_rows)
    _write_edges(graph, """UNWIND $rows AS row
        MATCH (p:Person {person_id: row.person_id, demo_id: $demo_id})
        MATCH (z:Zone {id: row.zone_id, demo_id: $demo_id})
        MERGE (p)-[:LOCATED_AT]->(z)""", location_rows)
    _write_edges(graph, """UNWIND $rows AS row
        MATCH (p:Person {person_id: row.person_id, demo_id: $demo_id})
        MATCH (s:Session {id: row.session_id, demo_id: $demo_id})
        MERGE (p)-[:ATTENDS]->(s)""", attend_rows)

    for rel, from_key, from_label, to_key, to_label, rows in [
        ("IN_ZONE", "id", "Session", "zone_id", "Zone", [{"id": s["id"], "zone_id": s["zone"].lower().replace(" ", "-")} for s in sessions]),
        ("IN_ZONE", "id", "Booth", "zone_id", "Zone", [{"id": b["id"], "zone_id": b["zone"].lower().replace(" ", "-")} for b in booths]),
        ("ABOUT", "id", "Session", "topic_id", "Topic", [{"id": s["id"], "topic_id": s["topic"].lower().replace(" ", "-")} for s in sessions]),
    ]:
        _write_edges(graph, f"""UNWIND $rows AS row
            MATCH (a:{from_label} {{{from_key}: row.{from_key}, demo_id: $demo_id}})
            MATCH (b:{to_label} {{id: row.{to_key}, demo_id: $demo_id}})
            MERGE (a)-[:{rel}]->(b)""", rows)

    company_booths = [{"company_id": c.lower().replace(" ", "-"), "booth_id": f"booth-{i+1}"} for i, c in enumerate(COMPANIES[:12])]
    _write_edges(graph, """UNWIND $rows AS row
        MATCH (c:Company {id: row.company_id, demo_id: $demo_id})
        MATCH (b:Booth {id: row.booth_id, demo_id: $demo_id})
        MERGE (c)-[:EXHIBITS_AT]->(b)""", company_booths)

    related = [{"from_id": TOPICS[i].lower().replace(" ", "-"), "to_id": TOPICS[(i+1) % len(TOPICS)].lower().replace(" ", "-")} for i in range(len(TOPICS))]
    _write_edges(graph, """UNWIND $rows AS row
        MATCH (a:Topic {id: row.from_id, demo_id: $demo_id})
        MATCH (b:Topic {id: row.to_id, demo_id: $demo_id})
        MERGE (a)-[:RELATED_TO]->(b)""", related)

    for rel, left_label, right_label, rows in [
        ("HAS_SESSION", "Event", "Session", [{"left_id": "patch-the-conference", "right_id": s["id"]} for s in sessions]),
        ("HAS_BOOTH", "Event", "Booth", [{"left_id": "patch-the-conference", "right_id": b["id"]} for b in booths]),
        ("HAS_ZONE", "Event", "Zone", [{"left_id": "patch-the-conference", "right_id": z.lower().replace(" ", "-")} for z in ZONES]),
    ]:
        _write_edges(graph, f"""UNWIND $rows AS row
            MATCH (a:{left_label} {{id: row.left_id, demo_id: $demo_id}})
            MATCH (b:{right_label} {{id: row.right_id, demo_id: $demo_id}})
            MERGE (a)-[:{rel}]->(b)""", rows)

    know_rows = []
    attendee_ids = [p["person_id"] for p in people[3:]]
    for pid in attendee_ids:
        for other in rng.sample(attendee_ids, 2):
            if pid != other:
                know_rows.append({"from_id": pid, "to_id": other})
    _write_edges(graph, """UNWIND $rows AS row
        MATCH (a:Person {person_id: row.from_id, demo_id: $demo_id})
        MATCH (b:Person {person_id: row.to_id, demo_id: $demo_id})
        MERGE (a)-[:KNOWS]->(b)""", know_rows)

    graph.query("""MERGE (u:User {name: 'Parth', demo_id: $demo_id})
        SET u.current_zone = 'Developer Lounge'
        WITH u
        MATCH (t:Topic {name: 'Sparse Attention', demo_id: $demo_id})
        MERGE (u)-[:INTERESTED_IN]->(t)""", params={"demo_id": DEMO_ID})
    graph.query("""MATCH (a:Topic {name: 'Sparse Attention', demo_id: $demo_id})
        MATCH (b:Topic {name: 'KV Cache Optimization', demo_id: $demo_id})
        MERGE (a)-[:RELATED_TO]->(b)""", params={"demo_id": DEMO_ID})

    summary = graph.query("""MATCH (n {demo_id: $demo_id})
        OPTIONAL MATCH (n)-[r]->(m {demo_id: $demo_id})
        RETURN count(DISTINCT n), count(r)""", params={"demo_id": DEMO_ID})
    return {"nodes": summary.result_set[0][0], "relationships": summary.result_set[0][1], "people": len(people), "sessions": len(sessions), "booths": len(booths), "topics": len(TOPICS), "companies": len(COMPANIES), "zones": len(ZONES)}
