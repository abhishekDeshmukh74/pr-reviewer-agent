"""Tests for diff parser."""

from app.services.diff_parser import parse_diff

SAMPLE_DIFF = """\
diff --git a/src/utils.py b/src/utils.py
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,5 +1,7 @@
 def hello():
-    print("hello")
+    print("hello world")
+    return True

 def goodbye():
     print("bye")
diff --git a/src/main.js b/src/main.js
--- a/src/main.js
+++ b/src/main.js
@@ -1,3 +1,4 @@
 function main() {
+    console.log("starting");
     run();
 }
"""


def test_parse_diff_file_count():
    files = parse_diff(SAMPLE_DIFF)
    assert len(files) == 2


def test_parse_diff_filenames():
    files = parse_diff(SAMPLE_DIFF)
    names = [f["filename"] for f in files]
    assert "src/utils.py" in names
    assert "src/main.js" in names


def test_parse_diff_languages():
    files = parse_diff(SAMPLE_DIFF)
    langs = {f["filename"]: f["language"] for f in files}
    assert langs["src/utils.py"] == "python"
    assert langs["src/main.js"] == "javascript"


def test_parse_diff_additions():
    files = parse_diff(SAMPLE_DIFF)
    utils = next(f for f in files if f["filename"] == "src/utils.py")
    assert len(utils["additions"]) == 2
    assert any("hello world" in a for a in utils["additions"])


def test_parse_diff_deletions():
    files = parse_diff(SAMPLE_DIFF)
    utils = next(f for f in files if f["filename"] == "src/utils.py")
    assert len(utils["deletions"]) == 1


def test_parse_empty_diff():
    files = parse_diff("")
    assert files == []
