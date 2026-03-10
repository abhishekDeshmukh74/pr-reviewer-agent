"""Evaluation harness for the PR review agent.

Run evaluations on known diffs with expected findings.
Usage: python -m app.evals.run_evals
"""

from __future__ import annotations

import asyncio
import json
import sys

from app.agent.graph import review_graph

# ─── Test Cases ──────────────────────────────────────────────────────

EVAL_CASES = [
    {
        "name": "SQL injection in Python",
        "diff": '''\
diff --git a/app/db.py b/app/db.py
--- a/app/db.py
+++ b/app/db.py
@@ -10,6 +10,10 @@ import sqlite3
 def get_user(user_id):
     conn = sqlite3.connect("app.db")
-    cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
+    cursor = conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
     return cursor.fetchone()
''',
        "expected_categories": ["Security"],
        "expected_min_issues": 1,
        "must_mention": ["injection", "sql"],
    },
    {
        "name": "Missing null check in JS",
        "diff": '''\
diff --git a/src/utils.js b/src/utils.js
--- a/src/utils.js
+++ b/src/utils.js
@@ -5,4 +5,8 @@
 function processUser(data) {
-  if (data && data.user) {
-    return data.user.name;
-  }
+  return data.user.name.toUpperCase();
 }
''',
        "expected_categories": ["Bugs & Logic Errors"],
        "expected_min_issues": 1,
        "must_mention": ["null", "undefined"],
    },
    {
        "name": "N+1 query in loop",
        "diff": '''\
diff --git a/app/views.py b/app/views.py
--- a/app/views.py
+++ b/app/views.py
@@ -1,5 +1,8 @@
 def list_orders(request):
     orders = Order.objects.all()
+    for order in orders:
+        customer = Customer.objects.get(id=order.customer_id)
+        order.customer_name = customer.name
     return render(request, "orders.html", {"orders": orders})
''',
        "expected_categories": ["Performance"],
        "expected_min_issues": 1,
        "must_mention": ["n+1", "query", "loop"],
    },
]


async def run_eval(case: dict) -> dict:
    """Run a single eval case and check results."""
    print(f"\n{'='*60}")
    print(f"EVAL: {case['name']}")
    print(f"{'='*60}")

    result = await review_graph.ainvoke(
        {
            "raw_diff": case["diff"],
            "parsed_files": [],
            "reviews": [],
            "suggested_patch": "",
            "overall_summary": "",
            "test_suggestions": "",
            "status": "",
        }
    )

    reviews = result["reviews"]
    all_issues = []
    found_categories = set()

    for review in reviews:
        if review.issues:
            found_categories.add(review.category)
            all_issues.extend(review.issues)

    # Check expected categories
    category_pass = any(
        expected.lower() in cat.lower()
        for expected in case["expected_categories"]
        for cat in found_categories
    )

    # Check minimum issues found
    issue_count_pass = len(all_issues) >= case["expected_min_issues"]

    # Check must_mention keywords
    all_text = " ".join(
        f"{i.title} {i.description} {i.suggestion}" for i in all_issues
    ).lower()
    keyword_pass = any(kw in all_text for kw in case["must_mention"])

    passed = category_pass and issue_count_pass and keyword_pass

    print(f"  Categories found: {found_categories}")
    print(f"  Issues found: {len(all_issues)}")
    print(f"  Category match: {'PASS' if category_pass else 'FAIL'}")
    print(f"  Issue count:     {'PASS' if issue_count_pass else 'FAIL'}")
    print(f"  Keyword match:   {'PASS' if keyword_pass else 'FAIL'}")
    print(f"  Overall: {'PASS' if passed else 'FAIL'}")

    return {"name": case["name"], "passed": passed, "issues": len(all_issues)}


async def main():
    results = []
    for case in EVAL_CASES:
        result = await run_eval(case)
        results.append(result)

    print(f"\n{'='*60}")
    print("EVAL SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for r in results if r["passed"])
    print(f"  {passed}/{len(results)} passed")

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['name']} ({r['issues']} issues)")

    if passed < len(results):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
