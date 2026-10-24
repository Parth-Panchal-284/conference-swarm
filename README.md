# Conference Swarm

**Make every conference minute count.** Conference Swarm turns a conference into a shared, living graph of people, expertise, sessions, booths, locations, and conversations. Independent agents read and write that graph, then re-rank what to do next.

## The demo

The app starts with a deterministic conference-scale graph: 150 explicitly synthetic attendee profiles, 20 topics, 20 companies, 12 sessions, 12 booths, and 8 zones. Alice, Bob, and Cameron are also marked as synthetic demo profiles. Bright Data Scout discoveries are real public-web results and keep their source URLs and provider provenance.

The prepared story starts with live Scout results already in the graph, then runs in two clicks:

1. Bright Data Scout adds sourced public conference contacts to the recommendation pool; the live result can outrank the initial direct expertise match.
2. Replay the Alice → Bob conversation. Memory stores the meeting, warm introduction, and Bob's expertise in FalkorDB. Matchmaker independently reads the new graph paths; Bob rises to the top.
3. Replay Bob → Cameron. The graph gains the warm path, expertise, and a recommendation for the actual *Agent Memory in Production* session. The 90-minute plan changes.

If `OPENAI_API_KEY` is available, Memory uses OpenAI structured extraction. Without it, the prepared conversation uses an explicitly labeled deterministic replay so the on-stage demo still works. Bright Data Scout requires `BRIGHTDATA_API_KEY` and working Bright Data credits. No secrets belong in source control.

## Run it

From the project folder:

```bash
cp .env.example .env
# Add your own OPENAI_API_KEY and BRIGHTDATA_API_KEY to .env
./run_demo.sh
```

The launcher starts FalkorDB v4.22.0, prepares the Python environment, and opens Streamlit. App: <http://localhost:8501>. FalkorDB Browser: <http://localhost:3000>.

In FalkorDB Browser select graph `conference_swarm` and run:

```cypher
MATCH (n)-[r]->(m)
WHERE n.demo_id = 'shared-memory-demo'
  AND m.demo_id = 'shared-memory-demo'
RETURN n, r, m
LIMIT 1500
```

## 90-second sponsor demo

The exact cue sheet is in [DEMO_SCRIPT.md](DEMO_SCRIPT.md). Run Scout before recording and keep its result in the session; don't reset after Scout. Keep the FalkorDB Browser query ready in a second tab. The story lands on three proof points: Bright Data adds live, attributed evidence that enters the recommendation pool; FalkorDB holds shared state across independent agents; OpenAI turns conversation into structured memory.

## Architecture

- **Scout** — Bright Data live search → OpenAI structured extraction → sourced entities and topics in FalkorDB.
- **Memory** — conversation → structured people, introductions, expertise, and session recommendations → persistent FalkorDB edges.
- **Matchmaker** — multi-hop topic relevance, warm introductions, and Scout evidence change candidate scores from graph state.
- **Planner** — uses the updated candidate and session path to surface the next route.

The scale population is synthetic and clearly labeled. It exists to make graph structure and density visible, not to claim these are real attendees.
