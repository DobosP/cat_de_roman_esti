"""Hermetic tests for V5 typed-link evidence, using synthetic source receipts."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import link_spans as spans  # noqa: E402

URL = "https://ro.wikipedia.org/wiki/P%C3%A2ine"
RECEIPT_NAME = spans.digest(URL.encode("ascii")) + ".receipt.json"
LINK = {"src_id": "n_paine", "dst_id": "n_faina", "relation": "made_from", "bidirectional": False}
QUOTE = "Pâinea este făcută din făină."


def article(contents, *, url=URL, head="", before="", inside=""):
    canonical = "" if url is None else f'<link rel="canonical" href="{url}">'
    return (
        '<!DOCTYPE html><html lang="ro"><head><meta charset="utf-8">'
        f"<title>Pâine – Wikipedia</title>{canonical}{head}</head>"
        '<body class="mediawiki action-view ns-0"><div><main id="content" class="mw-body">'
        f'<div id="bodyContent">{before}<div id="mw-content-text">{inside}'
        f'<div class="mw-content-ltr mw-parser-output" lang="ro">{contents}</div>'
        "</div></div></main></div></body></html>"
    ).encode()


def encode(value):
    return json.dumps(value, ensure_ascii=True).encode("ascii")


class LinkSpanTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd())).resolve()
        temporary = tempfile.TemporaryDirectory(prefix="test-link-spans-", dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.cache = Path(temporary.name)
        self.receipt_path = self.cache / RECEIPT_NAME

    def cache_source(self, body=None, **overrides):
        if body is None:
            body = article(f"<p>{QUOTE}</p>")
        self.body_sha = spans.digest(body)
        self.body_path = self.cache / (self.body_sha + ".body")
        self.body_path.write_bytes(body)
        self.receipt = {
            "url": URL,
            "sha256": self.body_sha,
            "status": 200,
            "bytes": len(body),
            "fetched_by_role": "factual",
            "fetched_at": 1794614400.1,
            "headers": {
                "content-type": "text/html; charset=UTF-8",
                "content-signal": "",
                "content-signal-present": "false",
                "location": "",
                "x-robots-tag": "",
            },
            "origin": "v5",
            "first_fetch_origin": "v5",
            "first_fetcher": "factual-intake",
            "received_at": 1794614401.2,
            "attempt_role": "factual",
            "attempt_fetcher": "factual-intake",
        }
        self.receipt.update(overrides)
        self.write_receipt()

    def write_receipt(self):
        raw = encode(self.receipt) + b"\n"
        self.receipt_sha = spans.digest(raw)
        self.receipt_path.write_bytes(raw)

    def row(self, *, link=None, quote=QUOTE, **overrides):
        row = {
            "link": dict(link or LINK),
            "url": URL,
            "receipt_sha256": self.receipt_sha,
            "body_sha256": self.body_sha,
            "quote": quote,
        }
        row.update(overrides)
        return row

    def check(self, *rows):
        return spans.check_batch(
            self.cache, encode({"schema": spans.SCHEMA, "links": list(rows) or [self.row()]})
        )

    def assert_failed(self, code, *rows):
        report = self.check(*rows)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["links"][0]["code"], code)
        self.assertNotIn("match", report["links"][0])

    def test_exact_output_and_position_for_nfc_space_entities_and_inline_markup(self):
        self.cache_source(
            article(
                "<p>Scurtă introducere.</p><p>În brutărie: <b>Pâinea</b>\neste&nbsp;făcută "
                'din&nbsp;<a href="/wiki/F%C4%83in%C4%83">făină</a>.</p>'
            )
        )
        quote = "Pa\u0302inea\t este fa\u0306cuta\u0306 din fa\u0306ina\u0306."
        row = self.row(quote=quote)
        raw = encode({"schema": spans.SCHEMA, "links": [row]})
        expected = {key: row[key] for key in row.keys() - {"quote"}}
        expected.update(
            status="pass",
            quote_sha256=spans.digest(quote.encode("utf-8")),
            match={
                "block": 1,
                "start": len("În brutărie: "),
                "end": len("În brutărie: " + QUOTE),
                "block_sha256": spans.digest(("În brutărie: " + QUOTE).encode("utf-8")),
            },
        )
        self.assertEqual(
            self.check(row),
            {
                "schema": spans.SCHEMA,
                "status": "pass",
                "batch_sha256": spans.digest(raw),
                "links": [expected],
            },
        )
        self.assertNotIn(QUOTE.encode("utf-8"), encode(self.check(row)))

    def test_reuses_source_for_links_and_reports_in_input_order(self):
        self.cache_source()
        miss = self.row(
            link={**LINK, "dst_id": "n_miere", "bidirectional": True},
            quote="Pâinea este din miere.",
        )
        third = self.row(link={**LINK, "dst_id": "n_aluat", "relation": "related_to"})
        with patch.object(spans, "extract_blocks", wraps=spans.extract_blocks) as extract:
            report = self.check(self.row(), miss, third)
        self.assertEqual(report["status"], "fail")
        self.assertEqual([x["status"] for x in report["links"]], ["pass", "fail", "pass"])
        self.assertEqual(
            [x["link"]["dst_id"] for x in report["links"]], ["n_faina", "n_miere", "n_aluat"]
        )
        extract.assert_called_once()

    def test_receipt_and_body_are_independently_bound(self):
        self.cache_source()
        old = self.row()
        self.receipt_path.write_bytes(self.receipt_path.read_bytes() + b" ")
        self.assert_failed("receipt_hash", old)
        self.write_receipt()
        self.body_path.write_bytes(b"X" * self.receipt["bytes"])
        self.assert_failed("body_integrity", old)
        self.body_path.write_bytes(b"short")
        self.assert_failed("body_integrity", old)
        self.body_path.unlink()
        self.assert_failed("body_unavailable", old)

    def test_uncached_receipt_and_cache_symlinks_are_refused(self):
        self.cache_source()
        moved = self.receipt_path.with_suffix(".moved")
        self.receipt_path.rename(moved)
        self.assert_failed("receipt_unavailable")
        try:
            self.receipt_path.symlink_to(moved)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.assert_failed("receipt_unavailable")
        self.receipt_path.unlink()
        self.write_receipt()
        moved = self.body_path.with_suffix(".moved")
        self.body_path.rename(moved)
        self.body_path.symlink_to(moved)
        self.assert_failed("body_unavailable")

    def test_refuses_receipt_metadata_failures(self):
        changes = (
            {"origin": "legacy"},
            {"first_fetch_origin": "legacy"},
            {"status": 200.0},
            {"status": 302},
            {"status": 206},
            {"body_problem": "truncated"},
            {"body_problem": None},
            {"bytes": True},
            {"first_fetcher": ""},
            {"first_fetcher": []},
            {"fetched_by_role": "author"},
            {"fetched_by_role": []},
            {"attempt_role": []},
            {"attempt_fetcher": "other worker"},
            {"received_at": 0},
            {"fetched_at": float("nan")},
            {"fetched_at": float("inf")},
            {"headers": []},
            {"dump_failure": {}},
            {"dump_checksum": {}},
            {"sha256": spans.digest(b"elsewhere")},
            {"url": "https://ro.wikipedia.org/wiki/F%C4%83in%C4%83"},
        )
        for change in changes:
            with self.subTest(change=change):
                self.cache_source(**change)
                self.assert_failed("receipt_invalid")
        self.cache_source()
        raw = self.receipt_path.read_bytes().replace(
            b'"status": 200', b'"status": 403, "status": 200'
        )
        self.receipt_path.write_bytes(raw)
        self.assert_failed("receipt_invalid", self.row(receipt_sha256=spans.digest(raw)))

    def test_checks_response_headers_and_excludes_other_formats(self):
        cases = {
            "text/plain": "unsupported_content_type",
            "application/json": "unsupported_content_type",
            "application/xhtml+xml": "unsupported_content_type",
            "text/html; charset=latin-1": "unsupported_content_type",
        }
        for value, code in cases.items():
            with self.subTest(value=value):
                self.cache_source(headers={"content-type": value})
                self.assert_failed(code)
        changes = (
            {"content-signal": "noai"},
            {"content-signal-present": "true"},
            {"x-robots-tag": "googlebot: noai"},
            {"location": "/wiki/Aluat"},
        )
        for headers in changes:
            with self.subTest(headers=headers):
                self.cache_source(headers={"content-type": "text/html", **headers})
                self.assert_failed("source_refused")
        for headers in (
            {"content-length": "1"},
            {"content-encoding": "gzip"},
            {"content-range": "bytes 0-12/999"},
        ):
            with self.subTest(headers=headers):
                self.cache_source(headers={"content-type": "text/html", **headers})
                self.assert_failed("receipt_invalid")

    def test_refuses_noncanonical_and_unsupported_receipt_urls_before_reading(self):
        self.cache_source()
        urls = (
            URL + "?",
            URL + "?oldid=1",
            URL + "#Introducere",
            URL.replace("%C3", "%c3"),
            URL.replace("/P", "/%50"),
            URL.replace("/P", "/X%2FP"),
            URL.replace("https", "http"),
            URL.replace("ro.wikipedia.org", "www.wikidata.org"),
            URL.replace("/wiki/", "/w/index.php/"),
            URL.replace("ro.wikipedia.org", "ro.wikipedia.org@evil.test"),
            "https://ro.wikipedia.org/wiki/Wikipedia:Termeni",
            "https://ro.wikipedia.org/wiki/../P%C3%A2ine",
            "https://ro.wikipedia.org/wiki/Pâine",
        )
        with patch.object(spans, "read_artifact") as reader:
            for url in urls:
                with self.subTest(url=url):
                    self.assert_failed("source_url", self.row(url=url))
            reader.assert_not_called()

    def test_page_identity_must_match_one_exact_canonical_link(self):
        for body in (
            article(f"<p>{QUOTE}</p>", url=None),
            article(f"<p>{QUOTE}</p>", url=URL + "_alt"),
            article(f"<p>{QUOTE}</p>", head=f'<link href="{URL}" rel="canonical">'),
            article(f'<link href="{URL}" rel="canonical"><p>{QUOTE}</p>', url=None),
        ):
            with self.subTest(body_sha=spans.digest(body)):
                self.cache_source(body)
                self.assert_failed("html_canonical")

    def test_rejects_policy_title_meta_and_invalid_utf8(self):
        for body in (
            article(f"<p>{QUOTE}</p>").replace(b"<title>P", b"<title>Access denied P"),
            article(f"<p>{QUOTE}</p>", head='<meta name="robots" content="noindex,noai">'),
            article(f"<p>{QUOTE}</p>", head='<meta name="content-signal" content="ai-input=no">'),
            article(
                f"<p>{QUOTE}</p>", head='<meta http-equiv="refresh" content="0;url=/wiki/Altul">'
            ),
        ):
            with self.subTest(body_sha=spans.digest(body)):
                self.cache_source(body)
                self.assert_failed("source_refused")
        self.cache_source(article(f"<p>{QUOTE}</p>").replace(b"</p>", b"\xff</p>"))
        self.assert_failed("html_utf8")

    def test_raw_go_title_refusals_run_before_article_extraction(self):
        hidden_titles = (
            '<svg><TiTlE lang="en">\nCrawler access denied!</TiTlE></svg>',
            "<!-- <title>Policy: Terms of Use</title> -->",
            "<!-- <title>Wikipedia: Termeni de utilizare</title> -->",
            "<!-- <title>\n : Termeni de utilizare</title> -->",
            "<!-- <title>\n\t: Termeni de utilizare</title> -->",
        )
        for title in hidden_titles:
            with self.subTest(title=title), patch.object(spans, "ArticleHTML") as parser:
                self.cache_source(article(f"{title}<p>{QUOTE}</p>"))
                self.assert_failed("source_refused")
                parser.assert_not_called()
        self.cache_source(article(f"<svg><title>Ilustrație</title></svg><p>{QUOTE}</p>"))
        self.assertEqual(self.check()["status"], "pass")

    def test_raw_title_scan_handles_long_overlapping_whitespace(self):
        payload = " " * (512 * 1024)
        self.assertFalse(spans.raw_title_refused(f"<title>{payload}unrelated</title>"))
        self.assertTrue(spans.raw_title_refused(f"<title>{payload}: Termeni de utilizare</title>"))
        self.assertTrue(
            spans.raw_title_refused("<title>\n Wikipedia: Termenii de utilizare</title>")
        )
        self.assertFalse(spans.raw_title_refused("<title>Access deniedness</title>"))

    def test_does_not_read_attributes_or_outside_article_region(self):
        self.cache_source(
            article(
                f'<p title="{QUOTE}" data-value="{QUOTE}">Informație.</p><!-- <p>{QUOTE}</p> -->',
                before=(
                    '<div class="mw-indicators"><div class="mw-parser-output">'
                    f"<p>{QUOTE}</p></div></div>"
                ),
                inside=f"<p>{QUOTE}</p>",
            )
        )
        self.assert_failed("span_not_found")
        self.cache_source(
            article(f"<p>{QUOTE}</p>", inside='<div class="mw-parser-output" lang="ro"></div>')
        )
        self.assert_failed("html_layout")

    def test_accepts_mediawiki_templatestyles_and_ignores_their_known_hidden_regions(self):
        self.cache_source(
            article(
                '<style typeof="mw:Extension/templatestyles mw:Transclusion">'
                ".mw-parser-output .cs1-maint {display:none}</style>"
                f'<p class="cs1-maint">{QUOTE}</p><p>Un text scurt.</p>'
            )
        )
        self.assert_failed("span_not_found")
        self.assertEqual(self.check(self.row(quote="Un text scurt."))["status"], "pass")

    def test_does_not_match_hidden_navigation_citations_or_code(self):
        templates = (
            "<div hidden><p>{q}</p></div>",
            '<p aria-hidden="true">{q}</p>',
            '<p style="dis\\70 lay:nOnE!important">{q}</p>',
            "<p inert>{q}</p>",
            '<span class="mw-visually-hidden">{q}</span>',
            '<p class="navbox-abovebelow">{q}</p>',
            '<p class="sortkey">{q}</p>',
            '<p role="navigation">{q}</p>',
            "<nav><p>{q}</p></nav>",
            "<details><p>{q}</p></details>",
            '<div class="infobox"><p>{q}</p></div>',
            '<p><sup class="mw-ref reference">{q}</sup></p>',
            '<div class="mw-references-wrap"><ol><li>{q}</li></ol></div>',
            '<p><a href="#cite_note-1">{q}</a></p>',
            "<p><script>{q}</script></p>",
            "<template><p>{q}</p></template>",
            "<noscript><p>{q}</p></noscript>",
            "<textarea><p>{q}</p></textarea>",
            "<svg><foreignObject><p>{q}</p></foreignObject></svg>",
        )
        for markup in templates:
            with self.subTest(markup=markup):
                self.cache_source(article(markup.format(q=QUOTE)))
                self.assert_failed("span_not_found")

    def test_does_not_stitch_paragraphs_items_or_nonprose(self):
        for cut in (
            "</p><p>",
            "<br>",
            "<span hidden>ignorat</span>",
            '<sup class="reference">[1]</sup>',
            "<img alt='foo'>",
            "<span style='font-weight:bold'>ignorat</span>",
        ):
            with self.subTest(cut=cut):
                self.cache_source(article(f"<p>Pâinea este {cut}făcută din făină.</p>"))
                self.assert_failed("span_not_found")
        for inner in (
            "<ul><li>Pâinea este</li><li>făcută din făină.</li></ul>",
            "<table><tr><td><p>Pâinea este făcută din făină.</p></td></tr></table>",
            f"<div>{QUOTE}</div>",
        ):
            with self.subTest(inner=inner):
                self.cache_source(article(inner))
                self.assert_failed("span_not_found")
        self.cache_source(article(f'<p>{QUOTE}<sup class="reference">[1]</sup></p>'))
        self.assertEqual(self.check()["status"], "pass")

    def test_unicode_matching_does_not_change_case_punctuation_or_accents(self):
        self.cache_source(article("<p>Șnur, făină; „copt“ &amp; unt.</p>"))
        self.assertEqual(
            self.check(self.row(quote="S\u0326nur, fa\u0306ina\u0306; „copt“ & unt."))["status"],
            "pass",
        )
        for quote in (
            "Şnur, făină",
            "șnur, făină",
            "Șnur, faina",
            "Șnur făină",
            "făină; copt",
            "&amp; unt",
        ):
            with self.subTest(quote=quote):
                self.assert_failed("span_not_found", self.row(quote=quote))

    def test_malformed_layout_fails_before_a_match_can_be_reported(self):
        bodies = (
            article(f"<p>{QUOTE}</p>").replace(b"</body></html>", b""),
            article(f"<p hidden hidden>{QUOTE}</p>"),
            article(f"<p><b>{QUOTE}</p></b>"),
            article(f"<p>{QUOTE}</p>").replace(b'<html lang="ro">', b'<html lang="en">'),
            article(f"<p>{QUOTE}</p>").replace(b"action-view ns-0", b"action-view ns-1"),
            article(f"<p>{QUOTE}</p>")
            .replace(b"<div><main", b"<table><main")
            .replace(b"</main></div>", b"</main></table>"),
            article(f"<p>{QUOTE}</p>", before='<div id="mw-content-text"></div>'),
            article(f"<style>p {{ display:none }}</style><p>{QUOTE}</p>"),
            article(f"<p>{QUOTE}</p>", head='<link rel="stylesheet" href="/local/custom.css">'),
        )
        for body in bodies:
            with self.subTest(body_sha=spans.digest(body)):
                self.cache_source(body)
                self.assert_failed("html_layout")

    def test_full_twenty_word_train_fits_and_a_161st_link_fails(self):
        self.cache_source()
        rows = [
            self.row(link={**LINK, "src_id": f"new_{word}", "dst_id": f"old_{edge}"})
            for word in range(20)
            for edge in range(8)
        ]
        report = self.check(*rows)
        self.assertEqual((report["status"], len(report["links"])), ("pass", 160))
        with self.assertRaisesRegex(spans.SpanError, "batch_schema"):
            self.check(*rows, self.row())

    def test_limits_and_invalid_batch_fail_closed(self):
        self.cache_source(article(f"<p>{QUOTE}</p><p>Încă un alineat.</p>"))
        for name, limit in (("MAX_DEPTH", 5), ("MAX_TAGS", 5), ("MAX_BLOCKS", 1)):
            with self.subTest(name=name), patch.object(spans, name, limit):
                self.assert_failed("html_limit")
        good = self.row()
        bad_link = deepcopy(good)
        bad_link["link"]["bidirectional"] = 1
        for rows, code in (
            ([], "batch_schema"),
            ([good] * (spans.MAX_LINKS + 1), "batch_schema"),
            ([good, good], "duplicate_link"),
            ([bad_link], "link_identity"),
            ([{**good, "quote": "x" * (spans.MAX_QUOTE + 1)}], "link_quote"),
            ([{**good, "quote": "\ud800"}], "link_quote"),
            ([{**good, "body_sha256": "0" * 64}], "link_hash"),
        ):
            with self.subTest(code=code), self.assertRaisesRegex(spans.SpanError, code):
                spans.check_batch(self.cache, encode({"schema": spans.SCHEMA, "links": rows}))
        with self.assertRaisesRegex(spans.SpanError, "batch_json"):
            spans.check_batch(self.cache, b'{"links": [], "links": []}')

    def test_cli_uses_exit_codes_and_never_outputs_quote(self):
        self.cache_source()
        path = self.cache / "batch.json"
        cmd = [
            sys.executable,
            "-IB",
            spans.__file__,
            "--cache",
            str(self.cache),
            "--batch",
            str(path),
        ]
        for quote, code in ((QUOTE, 0), ("Un span care lipsește.", 1)):
            with self.subTest(code=code):
                path.write_bytes(encode({"schema": spans.SCHEMA, "links": [self.row(quote=quote)]}))
                result = subprocess.run(cmd, capture_output=True, timeout=30, check=False)
                self.assertEqual(result.returncode, code)
                self.assertNotIn(encode(quote)[1:-1], result.stdout)
                self.assertNotIn(quote.encode("utf-8"), result.stderr)
                self.assertEqual(
                    json.loads(result.stdout)["status"], "pass" if code == 0 else "fail"
                )
        path.write_bytes(b'{"bad": 1}')
        result = subprocess.run(cmd, capture_output=True, timeout=30, check=False)
        self.assertEqual((result.returncode, result.stdout), (2, b""))


if __name__ == "__main__":
    unittest.main()
