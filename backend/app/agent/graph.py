"""LangGraph agent graph for PR review pipeline."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    generate_patch,
    generate_summary,
    guardrail_check,
    parse_diff_node,
    review_bugs,
    review_performance,
    review_readability,
    review_security,
    review_tests,
)
from app.agent.state import AgentState


def build_review_graph() -> StateGraph:
    """Build and compile the LangGraph review pipeline.

    Flow:
        guardrail_check -> parse_diff -> [5 parallel reviewers] -> generate_patch -> generate_summary -> END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("guardrail_check", guardrail_check)
    graph.add_node("parse_diff", parse_diff_node)
    graph.add_node("review_bugs", review_bugs)
    graph.add_node("review_security", review_security)
    graph.add_node("review_performance", review_performance)
    graph.add_node("review_readability", review_readability)
    graph.add_node("review_tests", review_tests)
    graph.add_node("generate_patch", generate_patch)
    graph.add_node("generate_summary", generate_summary)

    # Entry point
    graph.set_entry_point("guardrail_check")

    # Edges: guardrail -> parse -> fan-out to reviewers
    graph.add_edge("guardrail_check", "parse_diff")

    # Sequential reviewers to stay within free-tier TPM limits
    graph.add_edge("parse_diff", "review_bugs")
    graph.add_edge("review_bugs", "review_security")
    graph.add_edge("review_security", "review_performance")
    graph.add_edge("review_performance", "review_readability")
    graph.add_edge("review_readability", "review_tests")
    graph.add_edge("review_tests", "generate_patch")

    # Patch -> summary -> end
    graph.add_edge("generate_patch", "generate_summary")
    graph.add_edge("generate_summary", END)

    return graph.compile()


# Singleton compiled graph
review_graph = build_review_graph()
