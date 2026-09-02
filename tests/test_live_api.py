import os
import unittest
from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from core.cqvip_client import CqvipClient  # noqa: E402


@unittest.skipUnless(
    os.getenv("CQVIP_LIVE_TEST") == "1" and os.getenv("CQVIP_API_KEY"),
    "set CQVIP_LIVE_TEST=1 and CQVIP_API_KEY to run the live API test",
)
class CqvipLiveApiTests(unittest.TestCase):
    def test_simple_search(self):
        result = CqvipClient(max_retries=0).search("新能源", size=1)
        self.assertEqual(result["provider"], "cqvip")
        self.assertLessEqual(len(result["papers"]), 1)


if __name__ == "__main__":
    unittest.main()
