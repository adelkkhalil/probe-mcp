def _run_det_checks(det: dict, trace: list, answer: str) -> tuple[list, list]:
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

    if "tools_called_excludes" in det:
        for tool in det["tools_called_excludes"]:
            if tool in tools_called:
                failed.append(f"tool '{tool}' was called but should NOT have been")
            else:
                passed.append(f"tool '{tool}' was correctly not called")

    if "tool_called_count" in det:
        actual_calls = len(trace)
        expected = det["tool_called_count"]
        if actual_calls == expected:
            passed.append(f"call count {actual_calls} matches expected {expected}")
        else:
            failed.append(f"call count {actual_calls} does not match expected {expected}")

    if "tool_params_include" in det:
        tpi = det["tool_params_include"]
        target_tool = tpi["tool"]
        required_params = tpi["params"]
        matching_calls = [e for e in trace if e["tool"] == target_tool]
        if not matching_calls:
            failed.append(f"tool '{target_tool}' was never called")
        elif any(all(p in call["params"] for p in required_params) for call in matching_calls):
            passed.append(f"tool '{target_tool}' was called with {required_params}")
        else:
            failed.append(f"tool '{target_tool}' was not called with {required_params}")

    if "answer_excludes" in det:
        excl = det["answer_excludes"]
        if excl.lower() in answer.lower():
            failed.append(f"answer contains forbidden string '{excl}'")
        else:
            passed.append(f"answer does not contain '{excl}'")

    if "no_error" in det:
        error_count = sum(1 for e in trace if e.get("error", False) is True)
        if error_count == 0:
            passed.append("no tool errors")
        else:
            failed.append(f"{error_count} tool call(s) returned errors")

    if "tools_called_sequence" in det:
        seq = det["tools_called_sequence"]
        tools_in_trace = [e["tool"] for e in trace]
        pos = 0
        sequence_ok = True
        for tool in seq:
            found = False
            while pos < len(tools_in_trace):
                if tools_in_trace[pos] == tool:
                    pos += 1
                    found = True
                    break
                pos += 1
            if not found:
                sequence_ok = False
                break
        if sequence_ok:
            passed.append(f"tools called in sequence {seq}")
        else:
            failed.append(f"tools sequence {seq} was not followed")

    return passed, failed


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
    passed, failed = _run_det_checks(det, trace, answer)

    det_score = {"passed": len(passed), "total": len(passed) + len(failed)}
    status = "PASS" if len(failed) == 0 else "FAIL"

    scored = {
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

    if "trials" in result:
        trial_verdicts = []
        for trial in result["trials"]:
            if trial["answer"].startswith("ERROR:"):
                trial_verdicts.append("FAIL")
            else:
                _, t_failed = _run_det_checks(det, trial["trace"], trial["answer"])
                trial_verdicts.append("PASS" if not t_failed else "FAIL")
        pass_count = sum(1 for v in trial_verdicts if v == "PASS")
        fail_count = len(trial_verdicts) - pass_count
        majority = "PASS" if pass_count >= fail_count else "FAIL"
        agree_count = sum(1 for v in trial_verdicts if v == majority)
        scored["consistency_score"] = agree_count / len(trial_verdicts)

    return scored
