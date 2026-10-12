"""Repair checkpointed message history so OpenAI will accept the next turn.

If a previous run died after the model emitted ``tool_calls`` but before every
``ToolMessage`` was written, the saved thread is invalid. The next user message
then fails with: an assistant message with tool_calls must be followed by tool
messages for each tool_call_id.
"""
from langchain_core.messages import RemoveMessage, ToolMessage


def _tool_call_id(tc) -> str | None:
    if isinstance(tc, dict):
        return tc.get("id")
    return getattr(tc, "id", None)


def _ai_tool_call_ids(msg) -> list[str]:
    tcs = getattr(msg, "tool_calls", None) or []
    return [tid for tid in (_tool_call_id(tc) for tc in tcs) if tid]


def _is_tool_message(msg) -> bool:
    if isinstance(msg, ToolMessage):
        return True
    return getattr(msg, "type", None) == "tool" or getattr(msg, "role", None) == "tool"


def repair_message_list(messages: list) -> list:
    """Insert stub ToolMessages for any unanswered tool_calls, in place."""
    out: list = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        out.append(msg)
        needed = _ai_tool_call_ids(msg)
        if not needed:
            i += 1
            continue
        seen: set[str] = set()
        j = i + 1
        while j < len(messages) and _is_tool_message(messages[j]):
            out.append(messages[j])
            tid = getattr(messages[j], "tool_call_id", None)
            if tid:
                seen.add(tid)
            j += 1
        for tid in needed:
            if tid not in seen:
                out.append(
                    ToolMessage(
                        content="Tool call was interrupted; no result was recorded.",
                        tool_call_id=tid,
                    )
                )
        i = j
    return out


def history_needs_repair(original: list, repaired: list) -> bool:
    if len(original) != len(repaired):
        return True
    return any(
        isinstance(a, ToolMessage) is not isinstance(b, ToolMessage)
        or getattr(a, "tool_call_id", None) != getattr(b, "tool_call_id", None)
        for a, b in zip(original, repaired)
    )


def repair_checkpoint(graph, config: dict) -> None:
    """Fix the thread in the checkpointer, if it has dangling tool_calls."""
    try:
        snapshot = graph.get_state(config)
    except Exception:
        return
    values = getattr(snapshot, "values", None) or {}
    messages = list(values.get("messages") or [])
    if not messages:
        return
    repaired = repair_message_list(messages)
    if not history_needs_repair(messages, repaired):
        return
    removals = [RemoveMessage(id=m.id) for m in messages if getattr(m, "id", None)]
    graph.update_state(config, {"messages": removals + repaired})
