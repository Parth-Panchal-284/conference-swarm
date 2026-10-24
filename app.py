import streamlit as st

from src.memory_agent import (
    remember_interaction,
)
from src.scout_agent import scout
from src.shared_memory import (
    recommend_next,
    reset_demo,
    seed_demo,
)


st.set_page_config(
    page_title="Conference Swarm",
    page_icon="🧠",
    layout="wide",
)


def reset_state():
    reset_demo()
    seed_demo()

    st.session_state.last_memory = None
    st.session_state.scout_results = None


if "initialized" not in st.session_state:
    reset_state()
    st.session_state.initialized = True


def get_recommendation():
    result = recommend_next()

    if result is None:
        return None

    name, score, direct, related, warm = result

    return {
        "name": name,
        "score": score,
        "direct": direct,
        "related": related,
        "warm": warm,
    }


st.title("Conference Swarm")

st.caption(
    "AI agents that discover, remember, and "
    "coordinate through shared graph memory."
)


with st.sidebar:
    st.header("Agent Swarm")

    st.markdown(
        """
        🔎 **Scout Agent**  
        Bright Data live web intelligence

        🧠 **Memory Agent**  
        OpenAI conversation extraction

        🤝 **Matchmaker Agent**  
        Graph-based recommendations

        🕸️ **Shared Brain**  
        FalkorDB
        """
    )

    st.divider()

    if st.button(
        "Reset demo",
        use_container_width=True,
    ):
        reset_state()
        st.rerun()


# -----------------------------
# LIVE WEB SCOUT
# -----------------------------

st.subheader("🔎 Scout Agent")

st.caption(
    "Discover relevant people from the live web "
    "using Bright Data."
)

scout_col1, scout_col2 = st.columns(
    [2, 1]
)

with scout_col1:
    scout_goal = st.text_input(
        "What are you looking for?",
        value=(
            "LLM inference, sparse attention, "
            "AI agents, and ML systems"
        ),
    )

with scout_col2:
    st.write("")
    st.write("")

    scout_clicked = st.button(
        "Scout live web",
        type="primary",
        use_container_width=True,
    )


if scout_clicked:
    with st.spinner(
        "Scout Agent searching live web "
        "through Bright Data..."
    ):
        results = scout(
            scout_goal
        )

    st.session_state.scout_results = (
        results
    )


scout_results = (
    st.session_state.scout_results
)

if scout_results:
    people = scout_results.get(
        "people",
        [],
    )

    st.success(
        "Scout Agent searched "
        f"{scout_results.get('evidence_count', 0)} "
        "live web results and wrote discoveries "
        "into FalkorDB."
    )

    if people:
        columns = st.columns(
            min(len(people), 3)
        )

        for index, person in enumerate(
            people[:3]
        ):
            with columns[index]:
                st.markdown(
                    f"### {person['name']}"
                )

                st.caption(
                    person["affiliation"]
                )

                if person["topics"]:
                    st.write(
                        "**Topics:** "
                        + ", ".join(
                            person["topics"]
                        )
                    )

                st.write(
                    person["why_relevant"]
                )

                st.link_button(
                    "View live source",
                    person["source_url"],
                    use_container_width=True,
                )

    with st.expander(
        "Scout Agent output"
    ):
        st.json(
            scout_results
        )


st.divider()


# -----------------------------
# SHARED MEMORY / MATCHMAKER
# -----------------------------

current = get_recommendation()

left, right = st.columns(
    [1, 1],
    gap="large",
)


with left:
    st.subheader(
        "🤝 Who should I meet next?"
    )

    if current:
        st.metric(
            "Top recommendation",
            current["name"],
            f"score {current['score']}",
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Direct",
            current["direct"],
        )

        c2.metric(
            "Graph relation",
            current["related"],
        )

        c3.metric(
            "Warm intro",
            current["warm"],
        )

        if current["warm"] > 0:
            st.success(
                "Warm introduction discovered "
                "through shared graph memory."
            )

    st.divider()

    st.subheader(
        "🧠 Memory Agent"
    )

    interaction = st.text_area(
        "Tell the agent what happened",
        value=(
            "I just met Alice. She told me Bob "
            "works on KV Cache Optimization and "
            "said I should mention that she "
            "referred me."
        ),
        height=150,
    )

    if st.button(
        "Remember interaction",
        use_container_width=True,
    ):
        with st.spinner(
            "Memory Agent extracting facts..."
        ):
            memory = remember_interaction(
                interaction
            )

        st.session_state.last_memory = (
            memory
        )

        st.rerun()


with right:
    st.subheader(
        "🕸️ Shared FalkorDB memory"
    )

    memory = st.session_state.last_memory

    if memory:
        st.success(
            "Memory persisted into "
            "the shared graph."
        )

        st.json(
            memory
        )

    else:
        st.info(
            "No conversation memory "
            "added yet."
        )

    st.divider()

    st.subheader(
        "Graph reasoning"
    )

    if (
        current
        and current["name"] == "Alice"
    ):
        st.graphviz_chart(
            """
            digraph {
                rankdir=LR

                Parth [shape=box]

                Sparse [
                    label="Sparse Attention"
                ]

                Alice [shape=box]

                Parth -> Sparse [
                    label="INTERESTED_IN"
                ]

                Alice -> Sparse [
                    label="WORKS_ON"
                ]
            }
            """,
            use_container_width=True,
        )

        st.caption(
            "Before memory: Alice is the "
            "strongest direct match."
        )

    elif current:
        st.graphviz_chart(
            """
            digraph {
                rankdir=LR

                Parth [shape=box]

                Sparse [
                    label="Sparse Attention"
                ]

                KV [
                    label="KV Cache Optimization"
                ]

                Alice [shape=box]
                Bob [shape=box]

                Parth -> Sparse [
                    label="INTERESTED_IN"
                ]

                Sparse -> KV [
                    label="RELATED_TO"
                ]

                Bob -> KV [
                    label="WORKS_ON"
                ]

                Parth -> Alice [
                    label="MET"
                ]

                Alice -> Bob [
                    label="RECOMMENDED"
                ]
            }
            """,
            use_container_width=True,
        )

        st.caption(
            "Bob becomes the best match "
            "through topic relevance plus "
            "Alice's warm introduction."
        )


st.divider()

st.markdown(
    """
    ### One shared brain, multiple agents

    **Scout Agent** observes the live world
    through Bright Data.

    **Memory Agent** converts real conversations
    into structured persistent memory.

    **Matchmaker Agent** independently reads the
    graph and changes its decisions.

    The agents do not share a prompt or context
    window. They coordinate asynchronously through
    **FalkorDB**.
    """
)