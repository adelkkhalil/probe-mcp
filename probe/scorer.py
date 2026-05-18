def score_task(result: dict) -> dict:
    """Score a single task result against its expectations."""
    expect = result["expect"]
    trace = result["trace"]
    answer = result["answer"]

    passed = []
    failed = []

    tools_called = [t["tool"] for t in trace]

    if "tools_called_includes" in expect:
        for tool in expect["tools_called_includes"]:
            if tool in tools_called:
                passed.append(f"tool '{tool}' was called")
            else:
                failed.append(f"tool '{tool}' was NOT called")

    if "max_calls" in expect:
            actual_calls = len(trace)
            if actual_calls <= expect["max_calls"]:
                passed.append(f"call count {actual_calls} within limit {expect['max_calls']}")
            else:
                failed.append(f"call count {actual_calls} exceeded limit {expect['max_calls']}")

    if "answer_includes" in expect:
        if expect["answer_includes"].lower() in answer.lower():
            passed.append(f"answer contains '{expect['answer_includes']}'")
        else:
            failed.append(f"answer missing '{expect['answer_includes']}'")

    status = "PASS" if len(failed) == 0 else "FAIL"

    return {
        "id": result["id"],
        "status": status,
        "passed": passed,
        "failed": failed,
        "call_count": len(trace),
        "answer": answer,
    }
