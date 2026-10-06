"""Every logging call must have as many arguments as its format string has placeholders.

A mismatch only shows up when the message is formatted (e.g. with debug logging enabled) - pytest then raises,
in production the log line is lost. This already broke board setup once (10 placeholders, 9 arguments).
"""
import ast
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LEVELS = {"debug", "info", "warning", "error", "exception", "critical"}
PLACEHOLDER = re.compile(r"%(?!%)[-#0 +]*\d*(?:\.\d+)?[sdifrx]")


def test_logging_placeholders_match_arguments():
    mismatches = []
    for base, _dirs, files in os.walk(os.path.join(ROOT, "custom_components")):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(base, name)
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), path)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in LEVELS
                        and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    need = len(PLACEHOLDER.findall(node.args[0].value))
                    have = len(node.args) - 1
                    if need != have:
                        mismatches.append("%s:%s: %s placeholders, %s arguments" % (os.path.relpath(path, ROOT), node.lineno, need, have))
    assert mismatches == []
