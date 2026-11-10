import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ingestion.powerball import parse_powerball_pdf


class PowerballParserTest(unittest.TestCase):
    def test_parses_full_multiplier_and_preserves_double_play_null(self):
        source_text = "\n".join([
            "3/23/26 12 18 47 56 63 PB 1 X10 POWERBALL",
            "3/23/26 1 2 7 30 64 PB 19 POWERBALL DP",
            "3/21/26 1 2 7 30 64 PB 19 X2 POWERBALL",
        ])
        pdf = MagicMock()
        pdf.__enter__.return_value.pages = [SimpleNamespace(extract_text=lambda: source_text)]

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "powerball.jsonl"
            with patch("ingestion.powerball.pdfplumber.open", return_value=pdf):
                parse_powerball_pdf("source.pdf", output)
            records = [json.loads(line) for line in output.read_text().splitlines()]

        self.assertEqual(
            [(row["game_type"], row["multiplier"]) for row in records],
            [("POWERBALL", 10), ("POWERBALL_DP", None), ("POWERBALL", 2)],
        )
