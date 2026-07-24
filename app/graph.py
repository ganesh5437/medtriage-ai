"""
graph.py — LangGraph orchestration.

Phase 1 flow: emergency_check -> [emergency: emergency_response -> END]
                              -> [safe: intake_node -> symptom_extraction_node -> END]

Phase 2+ will extend this same graph with rag_retrieval_node,
differential_reasoning_node, lab_parser_node, report_synthesis_node —
do not rebuild the graph, add nodes to it.
"""
from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.llm import check_emergency, emergency_reply, extract_symptoms, generate_reply
from app.rag import retrieve_relevant_knowledge
from app.schemas import SymptomExtraction


class GraphState(TypedDict, total=False):
    message: str
    history: list[str]
    is_emergency: bool
    emergency_reason: str | None
    extracted: SymptomExtraction
    reply: str
    retrieved_knowledge: list[dict]
    differential: list[dict]


def emergency_check(state: GraphState) -> GraphState:
    is_emergency, reason = check_emergency(state["message"])
    state["is_emergency"] = is_emergency
    state["emergency_reason"] = reason
    return state


def emergency_response(state: GraphState) -> GraphState:
    state["reply"] = emergency_reply()
    state["extracted"] = SymptomExtraction()
    return state


def intake_node(state: GraphState) -> GraphState:
    # Phase 1: history is just passed through. Phase 2+ will merge full
    # session context here.
    state.setdefault("history", [])
    return state


def symptom_extraction_node(state: GraphState) -> GraphState:
    extracted = extract_symptoms(state["message"])
    state["extracted"] = extracted
    state["reply"] = generate_reply(state["message"], extracted)
    return state



def rag_retrieval_node(state: GraphState) -> GraphState:
    """Query ChromaDB for relevant medical knowledge based on extracted symptoms."""
    symptoms = state.get("extracted", SymptomExtraction()).symptoms or []
    if not symptoms:
        state["retrieved_knowledge"] = []
        return state
    
    try:
        retrieved = retrieve_relevant_knowledge(symptoms, top_k=5)
        state["retrieved_knowledge"] = retrieved
    except Exception as exc:
        # RAG failure — log and continue without knowledge (gap-fix: graceful degradation)
        import logging
        logging.getLogger("medtriage.graph").error("RAG retrieval failed: %s", exc)
        state["retrieved_knowledge"] = []
    
    return state


def differential_reasoning_node(state: GraphState) -> GraphState:
    """
    Reason over retrieved knowledge to generate differential diagnosis.
    Output: list of possible conditions with confidence language.
    Never definitive — always frames as "consistent with / may suggest / evaluate for".
    """
    extracted = state.get("extracted", SymptomExtraction())
    retrieved = state.get("retrieved_knowledge", [])
    
    # Build differential based on retrieved knowledge
    differential = []
    if retrieved:
        for kb_entry in retrieved[:3]:  # top 3 most relevant
            differential.append({
                "condition": kb_entry["condition"],
                "confidence": "Possible — consistent with reported symptoms",
                "reasoning": f"Symptoms align with {kb_entry['condition']}",
                "recommended_tests": kb_entry.get("recommended_tests", []),
                "red_flags": kb_entry.get("red_flags", []),
            })
    else:
        # No knowledge retrieved, generic response
        differential.append({
            "condition": "Requires further clinical evaluation",
            "confidence": "Limited information available",
            "reasoning": "Knowledge base retrieval did not find strong matches",
            "recommended_tests": [],
            "red_flags": [],
        })
    
    state["differential"] = differential
    return state

def _route_after_emergency_check(state: GraphState) -> str:
    return "emergency_response" if state.get("is_emergency") else "intake_node"


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("emergency_check", emergency_check)
    graph.add_node("emergency_response", emergency_response)
    graph.add_node("intake_node", intake_node)
    graph.add_node("symptom_extraction_node", symptom_extraction_node)
    graph.add_node("rag_retrieval_node", rag_retrieval_node)
    graph.add_node("differential_reasoning_node", differential_reasoning_node)

    graph.set_entry_point("emergency_check")
    graph.add_conditional_edges(
        "emergency_check",
        _route_after_emergency_check,
        {"emergency_response": "emergency_response", "intake_node": "intake_node"},
    )
    graph.add_edge("emergency_response", END)
    graph.add_edge("intake_node", "symptom_extraction_node")
    graph.add_edge("symptom_extraction_node", "rag_retrieval_node")
    graph.add_edge("rag_retrieval_node", "differential_reasoning_node")
    graph.add_edge("differential_reasoning_node", END)

    return graph.compile()


compiled_graph = build_graph()


def run_turn(message: str) -> GraphState:
    initial: GraphState = {"message": message, "history": []}
    return compiled_graph.invoke(initial)
