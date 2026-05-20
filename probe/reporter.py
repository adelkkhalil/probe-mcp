import re


def print_results(scored: list, server_name: str):
    total = len(scored)
    passed = sum(1 for r in scored if r["status"] == "PASS")
    print(f"\nResults: {passed}/{total} passed\n")

    for r in scored:
        icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {icon} {r['id']} ({r['call_count']} calls)")
        for msg in r["failed"]:
            if not r["answer"].startswith("ERROR:"):
                print(f"      FAIL: {msg}")
        for msg in r["passed"]:
            print(f"      pass: {msg}")
        answer = r["answer"]
        if answer.startswith("ERROR:"):
            match = re.search(r"'message': '([^']+)'", answer)
            if match:
                print(f"      error: {match.group(1)[:120]}")
            else:
                print(f"      error: {answer[7:127]}")
        else:
            truncated = answer[:80]
            if len(answer) > 80:
                last_space = truncated.rfind(" ")
                if last_space > 40:
                    truncated = truncated[:last_space]
            print(f"      answer: {truncated}...")
        print()


def print_compare_table(scored1: list, scored2: list, server1_name: str, server2_name: str):
    scored2_by_id = {r["id"]: r for r in scored2}
    col1 = max(len(server1_name), 20)
    col2 = max(len(server2_name), 20)
    task_col = max(len(r["id"]) for r in scored1) + 2

    print(f"\n{'Task':<{task_col}}  {server1_name:<{col1}}  {server2_name:<{col2}}")
    print("-" * (task_col + col1 + col2 + 4))

    for r1 in scored1:
        r2 = scored2_by_id.get(r1["id"])
        s1 = f"PASS ({r1['call_count']} calls)" if r1["status"] == "PASS" else f"{r1['status']} ({r1['call_count']} calls)"
        s2 = (
            f"PASS ({r2['call_count']} calls)"
            if r2 and r2["status"] == "PASS"
            else f"{r2['status']} ({r2['call_count']} calls)"
            if r2
            else "FAIL"
        )
        print(f"{r1['id']:<{task_col}}  {s1:<{col1}}  {s2:<{col2}}")


def print_summary(server_name: str, passed: int, total: int):
    print(f"\n{server_name}: {passed}/{total}")
