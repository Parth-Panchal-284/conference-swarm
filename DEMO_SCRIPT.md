# Conference Swarm · concise demo

## Before recording

1. Open the dashboard at `localhost:8501` and the FalkorDB Browser at `localhost:3000` in separate tabs.
2. Run **Scout the live web** before the take; let the real search finish. Leave the dashboard at stage zero—**do not reset after Scout**.
3. In FalkorDB Browser select `conference_swarm`, paste/run the query below once, and leave it ready in the query bar. After each conversation replay, return to this tab and press **Enter/Run** to refresh the visualization. The database writes immediately; Browser does not poll on its own.

```cypher
MATCH (n)-[r]->(m)
WHERE n.demo_id = 'shared-memory-demo'
  AND m.demo_id = 'shared-memory-demo'
RETURN n, r, m LIMIT 1500
```

## Spoken track · about 75–90 seconds

**0:00–0:13 · Emotion + problem**
“The best part of a conference is a hallway conversation. The worst part is how quickly you forget who said what—or waste the next hour deciding where to go. Conference Swarm remembers the human context and turns it into a better next move.”

**0:13–0:29 · Agents + sponsors**
“These are four independent agents sharing FalkorDB: Scout uses Bright Data to find live, sourced conference contacts; Memory uses OpenAI to turn conversations into graph facts; Matchmaker follows expertise and warm-introduction paths; Planner reorders sessions and people around time and location. Qodo reviewed our changes and caught real memory and identity bugs we fixed.”

**0:29–0:44 · First conversation**
**Show:** Scout result and current top match. Click **Replay Alice → Bob introduction**.
“Alice tells me Bob works on KV-cache optimization and refers me. Memory writes that conversation to FalkorDB. The Matchmaker never saw the conversation, but Bob rises because it independently reads Alice’s introduction and Bob’s topic path.”

**0:44–0:55 · Prove it in FalkorDB**
**Show:** Switch to FalkorDB Browser and press **Enter/Run**. Point at the new `MET`, `RECOMMENDED`, and `WORKS_ON` edges.
“That conversation is now persistent graph state—not just chat history. I rerun the Browser query to show the newly written edges.”

**0:55–1:10 · Replan**
**Show:** Return to app; click **Replay Bob → Cameron + session**; switch back to Browser and run the query again.
“Bob refers me to Cameron and recommends the Agent Memory session. The graph changes again, and the Planner moves that session to now and Cameron to the next warm introduction.”

**1:10–1:20 · Close**
“Bright Data sees the public conference. OpenAI understands what I heard. FalkorDB lets independent agents share and reason over it. Conference Swarm gives me back the time—and the people—I came here for.”

## Keep claims grounded

- The crowd-scale population is synthetic demo data. Bright Data discoveries are real public profiles, with source links and only the affiliations supported by those sources.
- Don't claim TrueFoundry integration; it isn't in this build. Select FalkorDB, Bright Data, and Qodo tracks only if their required evidence is ready.
- If time is tight, skip the optional feedback fields; complete the required project and track answers.
