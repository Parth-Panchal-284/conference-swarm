import streamlit as st

from src.memory_agent import remember_interaction
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
    "Shared persistent graph memory for "
    "conference AI agents."
)


with st.sidebar:
    st.header("Agents")

    st.markdown(
        """
        🔎 **Scout Agent**  
        Discovers people and context

        🧠 **Memory Agent**  
        Converts conversations into graph memory

        🤝 **Matchmaker Agent**  
        Chooses who you should meet next

        **Shared state:** FalkorDB
        """
    )

    st.divider()

    if st.button(
        "Reset demo",
        use_container_width=True,
    ):
        reset_state()
        st.rerun()


current = get_recommendation()

left, right = st.columns(
    [1, 1],
    gap="large",
)


with left:
    st.subheader("Who should I meet next?")

    if current:
        st.metric(
            "Top recommendation",
            current["name"],
            f"score {current['score']}",
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Direct interest",
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
                "Warm introduction found "
                "through shared memory."
            )

    st.divider()

    st.subheader("Log an interaction")

    interaction = st.text_area(
        "What happened?",
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
        type="primary",
        use_container_width=True,
    ):
        with st.spinner(
            "Memory Agent extracting facts..."
        ):
            memory = remember_interaction(
                interaction
            )

        st.session_state.last_memory = memory

        st.rerun()


with right:
    st.subheader("Shared graph memory")

    memory = st.session_state.last_memory

    if memory:
        st.success(
            "Memory Agent updated FalkorDB."
        )

        st.json(memory)

    else:
        st.info(
            "No new interaction memory yet."
        )

    st.divider()

    st.subheader("Graph reasoning")

    if current and current["name"] == "Alice":
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
            "After memory: Bob wins through "
            "multi-hop relevance plus a "
            "warm introduction."
        )


st.divider()

st.markdown(
    """
    ### What just happened?

    The **Memory Agent** heard the conversation
    and wrote new relationships into FalkorDB.

    The **Matchmaker Agent** was never directly
    told about that conversation.

    On its next run, it independently read the
    shared graph and changed its recommendation.
    """
)
