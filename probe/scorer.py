def score_task(result: dict) -> dict:
    """Score a single task result against its expectations."""
    expect = result["expect"]
    trace = result["trace"]
    answer = result["answer"]

    pro_score = "pending" if expect.get("probabilistic", {}).get("judge") is True else None

    if answer.startswith("ERROR:"):
        import re

        match = re.search(r"'message': '([^']+)'", answer)
        error_msg = match.group(1)[:100] if match else answer[7:107]
        return {
            "id": result["id"],
            "status": "FAIL",
            "passed": [],
            "failed": [f"task errored: {error_msg}"],
            "call_count": len(trace),
            "answer": answer,
            "det_score": {"passed": 0, "total": 0},
            "pro_score": pro_score,
        }

    det = expect.get("deterministic", {})
    tools_called = [t["tool"] for t in trace]

    passed = []
    failed = []

    if "tools_called_includes" in det:
        for tool in det["tools_called_includes"]:
            if tool in tools_called:
                passed.append(f"tool '{tool}' was called")
            else:
                failed.append(f"tool '{tool}' was NOT called")

    if "max_calls" in det:
        actual_calls = len(trace)
        if actual_calls <= det["max_calls"]:
            passed.append(f"call count {actual_calls} within limit {det['max_calls']}")
        else:
            failed.append(f"call count {actual_calls} exceeded limit {det['max_calls']}")

    if "answer_includes" in det:
        if det["answer_includes"].lower() in answer.lower():
            passed.append(f"answer contains '{det['answer_includes']}'")
        else:
            failed.append(f"answer missing '{det['answer_includes']}'")

    det_score = {"passed": len(passed), "total": len(passed) + len(failed)}
    status = "PASS" if len(failed) == 0 else "FAIL"
    return {
        "id": result["id"],
        "status": status,
        "passed": passed,
        "failed": failed,
        "call_count": len(trace),
        "answer": answer,
        "expect": expect,
        "trace": trace,
        "det_score": det_score,
        "pro_score": pro_score,
    }
