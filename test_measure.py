"""Offline unit tests and optional true-encoding integration checks."""

from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import measure


class ByteDouble:
    """Test double checks orchestration only; it is not a BPE tokenizer."""

    def encode_ordinary(self, value):
        return list(value.encode("utf-8"))

    def decode_bytes(self, ids):
        return bytes(ids)


class UnitTests(unittest.TestCase):
    def setUp(self):
        self.rows = measure.load_fixtures(measure.ROOT / "fixtures.json")
        self.stub = {"fixture-byte-double": ByteDouble()}

    def test_repeatable_fixture_report_and_round_trips(self):
        first = measure.make_report(self.rows, self.stub, "none")
        second = measure.make_report(self.rows, self.stub, "none")
        self.assertEqual(measure.json_text(first), measure.json_text(second))
        self.assertTrue(all(item["encodings"]["fixture-byte-double"]["round_trip"]
                            for item in first["rows"]))
        empty = next(item for item in first["rows"] if item["id"] == "empty")
        self.assertEqual(empty["encodings"]["fixture-byte-double"]["count"], 0)

    def test_normalization_is_explicit_and_preserves_original(self):
        report = measure.make_report(self.rows, self.stub, "NFC")
        rows = {item["id"]: item for item in report["rows"]}
        a, b = rows["ko-nfc"], rows["ko-nfd"]
        self.assertNotEqual(a["input"], b["input"])
        self.assertEqual(a["analyzed"], b["analyzed"])
        self.assertEqual(a["encodings"], b["encodings"])

    def test_cli_blocks_uncached_vocab_fetch(self):
        original_reader = Mock(return_value=b"network should not run")
        loader = SimpleNamespace(read_file=original_reader)
        fake = SimpleNamespace(
            load=loader, get_encoding=lambda _name: loader.read_file("vocabulary")
        )
        with patch.object(measure.metadata, "version", return_value=measure.TIKTOKEN_VERSION):
            with patch.dict(sys.modules, {"tiktoken": fake}):
                with self.assertRaisesRegex(RuntimeError, "cache missing or invalid"):
                    measure.load_encodings()
        self.assertIs(loader.read_file, original_reader)
        original_reader.assert_not_called()

    def test_duplicate_fixture_rejected(self):
        with tempfile.TemporaryDirectory() as where:
            target = Path(where) / "invalid.json"
            target.write_text(measure.json_text([self.rows[0], self.rows[0]]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                measure.load_fixtures(target)


class CacheIntegrationTests(unittest.TestCase):
    def test_offline_real_encodings(self):
        try:
            encodings = measure.load_encodings()
        except RuntimeError as err:
            self.skipTest(str(err))
        rows = measure.load_fixtures(measure.ROOT / "fixtures.json")
        first = measure.make_report(rows, encodings, "none")
        self.assertEqual(measure.json_text(first),
                         measure.json_text(measure.make_report(rows, encodings, "none")))
        self.assertEqual(tuple(encodings), measure.ENCODINGS)
        for row in first["rows"]:
            for m in row["encodings"].values():
                self.assertTrue(m["round_trip"])
                self.assertEqual(m["count"], len(m["ids"]))
        english = encodings["cl100k_base"]
        self.assertEqual(english.encode_ordinary("hello"), [15339])
        self.assertEqual(encodings["o200k_base"].encode_ordinary("hello"), [24912])


if __name__ == "__main__":
    unittest.main()
