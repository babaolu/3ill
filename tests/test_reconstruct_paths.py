"""Focused regression tests for pipeline/reconstruct.py path handling.

Bug: relative --session paths broke COLMAP invocation because commands run
with cwd=work/ while paths were relative to the caller's cwd. Fix: absolutize
the session dir up front. These tests run reconstruct.main() against a stub
`colmap` executable (no COLMAP install needed).

Run:  python3 -m unittest discover tests
"""
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import reconstruct


STUB = """#!/bin/sh
echo "$PWD|$@" >> "$COLMAP_STUB_LOG"
exit 0
"""


class ReconstructPathsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="3ill-test-")
        self.session = os.path.join(self.tmp, "session")
        os.makedirs(self.session)
        for name in ("a.jpg", "b.JPG", "note.txt"):
            with open(os.path.join(self.session, name), "w") as f:
                f.write("x")
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(bindir)
        stub = os.path.join(bindir, "colmap")
        with open(stub, "w") as f:
            f.write(STUB)
        os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC)
        self.log = os.path.join(self.tmp, "calls.log")
        self.old = (os.getcwd(), os.environ.get("PATH"), list(sys.argv),
                    os.environ.get("COLMAP_STUB_LOG"))
        os.chdir(self.tmp)
        os.environ["PATH"] = bindir + os.pathsep + os.environ.get("PATH", "")
        os.environ["COLMAP_STUB_LOG"] = self.log

    def tearDown(self):
        cwd, path, argv, stublog = self.old
        os.chdir(cwd)
        os.environ["PATH"] = path
        sys.argv = argv
        if stublog is None:
            os.environ.pop("COLMAP_STUB_LOG", None)
        else:
            os.environ["COLMAP_STUB_LOG"] = stublog
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_session_photos_finds_images_only(self):
        self.assertEqual(reconstruct.session_photos(self.session),
                         ["a.jpg", "b.JPG"])

    def test_relative_session_passes_absolute_paths(self):
        sys.argv = ["reconstruct.py", "--session", "session"]
        reconstruct.main()
        with open(self.log) as f:
            calls = [ln.rstrip("\n").split("|", 1) for ln in f]
        self.assertEqual(len(calls), 3)  # extractor, matcher, mapper
        for cwd, args in calls:
            toks = args.split()
            for flag in ("--database_path", "--image_path", "--output_path"):
                if flag in toks:
                    val = toks[toks.index(flag) + 1]
                    self.assertTrue(os.path.isabs(val), (flag, val))
                    # Parent must exist as seen from the command's cwd.
                    parent = os.path.join(cwd, val) if not os.path.isabs(val) else val
                    self.assertTrue(os.path.isdir(os.path.dirname(parent)),
                                    (flag, val, cwd))


if __name__ == "__main__":
    unittest.main()
