"""Checkpoint repair: dangling tool_calls must get stub ToolMessages."""
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.repair import history_needs_repair, repair_message_list


def test_inserts_stubs_before_the_next_user_message():
    messages = [
        HumanMessage(content="look around"),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "search_worldbook", "args": {"query": "bog"}, "id": "call_a"},
                {"name": "ask_archivist", "args": {"question": "gold"}, "id": "call_b"},
                {"name": "search_worldbook", "args": {"query": "rules"}, "id": "call_c"},
            ],
        ),
        HumanMessage(content="end the role-play"),
    ]
    repaired = repair_message_list(messages)
    assert history_needs_repair(messages, repaired)
    assert [type(m) for m in repaired] == [
        HumanMessage, AIMessage, ToolMessage, ToolMessage, ToolMessage, HumanMessage
    ]
    assert [m.tool_call_id for m in repaired[2:5]] == ["call_a", "call_b", "call_c"]
    assert repaired[-1].content == "end the role-play"


def test_complete_tool_round_is_left_alone():
    messages = [
        HumanMessage(content="inventory?"),
        AIMessage(
            content="",
            tool_calls=[{"name": "ask_archivist", "args": {"question": "inv"}, "id": "call_1"}],
        ),
        ToolMessage(content="3 draughts", tool_call_id="call_1"),
        AIMessage(content="You carry three draughts."),
    ]
    repaired = repair_message_list(messages)
    assert history_needs_repair(messages, repaired) is False
    assert repaired == messages


def test_partial_tool_results_get_the_missing_stubs():
    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "search_worldbook", "args": {}, "id": "call_ok"},
                {"name": "ask_archivist", "args": {}, "id": "call_missing"},
            ],
        ),
        ToolMessage(content="lore", tool_call_id="call_ok"),
        HumanMessage(content="go on"),
    ]
    repaired = repair_message_list(messages)
    assert [getattr(m, "tool_call_id", None) for m in repaired] == [
        None, "call_ok", "call_missing", None
    ]
