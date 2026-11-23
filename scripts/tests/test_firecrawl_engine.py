import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from url_to_markdown.engines import FirecrawlEngine


class FirecrawlEngineTests(unittest.TestCase):
    def test_monid_key_only_scrapes_with_firecrawl(self):
        url = "https://example.com/正文"
        document = {"markdown": "# 正文", "metadata": {"title": "正文"}}
        response = Mock(status_code=200)
        response.json.return_value = {"output": {"success": True, "data": document}}

        with patch.dict("os.environ", {"MONID_API_KEY": "test-key"}, clear=True):
            with patch("requests.post", return_value=response) as post:
                result = FirecrawlEngine().fetch(url)

        post.assert_called_once()
        self.assertEqual(post.call_args.args, ("https://api.monid.ai/v1/run",))
        self.assertEqual(post.call_args.kwargs["headers"], {
            "Authorization": "Bearer test-key",
            "Content-Type": "application/json; charset=utf-8",
        })
        body = post.call_args.kwargs["data"]
        self.assertIn("正文".encode("utf-8"), body)
        self.assertEqual(json.loads(body), {
            "provider": "firecrawl",
            "endpoint": "/scrape",
            "input": {"body": {"url": url, "formats": ["markdown"]}},
        })
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], document["markdown"])
        self.assertEqual(result["metadata"], document["metadata"])

    def test_monid_batch_preserves_vendor_error_and_continues(self):
        urls = ["https://example.com/missing", "https://example.com/found"]
        missing = Mock(status_code=200)
        missing.json.return_value = {
            "status": "COMPLETED",
            "providerResponse": {"httpStatus": 404, "error": {"error": "No match"}},
        }
        found = Mock(status_code=200)
        found.json.return_value = {"output": {"data": {"markdown": "Found"}}}

        with patch.dict("os.environ", {"MONID_API_KEY": "test-key"}, clear=True):
            with patch("requests.post", side_effect=[missing, found]) as post:
                results = FirecrawlEngine().fetch_batch(urls)

        self.assertEqual([json.loads(call.kwargs["data"])["input"]["body"]["url"]
                          for call in post.call_args_list], urls)
        self.assertEqual(results[0], {
            "url": urls[0],
            "success": False,
            "error": "Firecrawl failed: Unexpected error during scrape: Status code 404. "
                     "No match - No additional error details provided.",
        })
        self.assertEqual(results[1]["content"], "Found")

    def test_monid_polls_the_same_run_until_complete(self):
        accepted = Mock(status_code=202)
        accepted.json.return_value = {"runId": "run-test"}
        pending = Mock()
        pending.json.return_value = {"status": "RUNNING"}
        completed = Mock()
        completed.json.return_value = {
            "status": "COMPLETED",
            "output": {"data": {"markdown": "Done"}},
        }

        with (
            patch.dict("os.environ", {"MONID_API_KEY": "test-key"}, clear=True),
            patch("requests.post", return_value=accepted) as post,
            patch("requests.get", side_effect=[pending, completed]) as get,
            patch("url_to_markdown.engines.firecrawl_engine.time.sleep"),
        ):
            result = FirecrawlEngine().fetch("https://example.com", timeout=15)

        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["timeout"], 15)
        self.assertEqual(get.call_count, 2)
        for call in get.call_args_list:
            self.assertEqual(call.args, ("https://api.monid.ai/v1/runs/run-test",))
            self.assertGreater(call.kwargs["timeout"], 0)
            self.assertLessEqual(call.kwargs["timeout"], 15)
        self.assertEqual(result["content"], "Done")

    def test_direct_firecrawl_uses_sdk_without_monid(self):
        url = "https://example.com"
        with patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key"}, clear=True):
            with patch("firecrawl.Firecrawl") as sdk:
                scrape = sdk.return_value.scrape
                scrape.return_value.model_dump.return_value = {"markdown": "# Direct"}
                result = FirecrawlEngine().fetch(url)

        sdk.assert_called_once_with(api_key="test-key")
        scrape.assert_called_once_with(url, formats=["markdown"])
        self.assertEqual(result["content"], "# Direct")
