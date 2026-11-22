#!/usr/bin/env python3
"""Prints a GitHub-flavoured Markdown summary of JUnit XML reports.

Usage: junit-summary.py "<title>" <glob> [<glob> ...]
Append the output to $GITHUB_STEP_SUMMARY.
"""
import glob
import sys
import xml.etree.ElementTree as ET

PIPE_ESCAPE = "\\|"


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def suites_in(root):
    if local_name(root.tag) == "testsuite":
        return [root]
    return [el for el in root if local_name(el.tag) == "testsuite"]


def summarize_suite(suite, failures):
    passed = failed = skipped = 0
    for case in (c for c in suite.iter() if local_name(c.tag) == "testcase"):
        children = {local_name(c.tag): c for c in case}
        if "failure" in children or "error" in children:
            failed += 1
            problem = children["failure"] if "failure" in children else children["error"]
            message = (problem.get("message") or problem.text or "").strip().splitlines()
            failures.append((suite.get("name") or "suite", case.get("name") or "test",
                             message[0][:300] if message else ""))
        elif "skipped" in children:
            skipped += 1
        else:
            passed += 1
    return passed, failed, skipped, float(suite.get("time") or 0)


def main():
    title, patterns = sys.argv[1], sys.argv[2:]
    files = sorted({f for p in patterns for f in glob.glob(p, recursive=True)})
    rows, failures = [], []
    totals = [0, 0, 0, 0.0]
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for suite in suites_in(root):
            passed, failed, skipped, seconds = summarize_suite(suite, failures)
            if passed + failed + skipped == 0:
                continue
            rows.append((suite.get("name") or path, passed, failed, skipped, seconds))
            for i, value in enumerate((passed, failed, skipped, seconds)):
                totals[i] += value

    total = int(sum(totals[:3]))
    icon = "❌" if totals[1] else "✅"
    print(f"## {icon} {title}\n")
    if not rows:
        print("_No test reports were found._")
        return
    print(f"**{total} tests** — {totals[0]} passed, {totals[1]} failed, {totals[2]} skipped "
          f"({totals[3]:.1f}s)\n")
    print("| Suite | Passed | Failed | Skipped | Time (s) |")
    print("|---|---:|---:|---:|---:|")
    for name, passed, failed, skipped, seconds in sorted(rows):
        mark = "❌ " if failed else ""
        safe_name = name.replace("|", PIPE_ESCAPE)
        print(f"| {mark}{safe_name} | {passed} | {failed} | {skipped} | {seconds:.1f} |")
    if failures:
        print("\n### Failed tests\n")
        for suite, name, message in failures:
            print(f"- **{suite}** › {name}" + (f"\n  > {message}" if message else ""))


if __name__ == "__main__":
    main()
