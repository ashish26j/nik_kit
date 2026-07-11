#!/usr/bin/env python3
"""Nik_kiT phase test runner — the gate every feature phase must pass.

Lightweight, stdlib-only, runs against the LIVE localhost stack.

Usage:
    python3 tests/run_tests.py            # run ALL phases
    python3 tests/run_tests.py P1         # run only P1 tests
    python3 tests/run_tests.py P0 P1      # run P0 and P1

Prereqs: local stack running →  cd infra && docker compose up -d
         (and `python manage.py seed_menu` for P1 data).

Exit code 0 = all passed, 1 = something failed (usable as a CI/pre-push gate).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lib  # noqa: E402

# Importing the modules registers their @test cases.
import test_p0  # noqa: E402,F401
import test_p1  # noqa: E402,F401
import test_p2  # noqa: E402,F401
import test_p3  # noqa: E402,F401
import test_p4  # noqa: E402,F401
import test_p5  # noqa: E402,F401
import test_p7  # noqa: E402,F401


def main():
    phases = [a.upper() for a in sys.argv[1:]]
    tests = lib.all_tests()
    if phases:
        tests = [t for t in tests if any(f"_{p}_" in t[0] for p in phases)]
    tests.sort(key=lambda t: t[0])

    if not tests:
        print("No tests matched.", "phases=" + ",".join(phases) if phases else "")
        sys.exit(1)

    print(f"Nik_kiT tests → {lib.BASE_URL}  ({len(tests)} test(s))\n")
    passed = failed = 0
    for tid, desc, fn in tests:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL  {tid}  {desc}")
            print(f"           → {type(e).__name__}: {e}")
            failed += 1
        else:
            print(f"  PASS  {tid}  {desc}")
            passed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        print("\nIf everything looks down: is the stack up? "
              "cd infra && docker compose up -d  (and manage.py seed_menu)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
