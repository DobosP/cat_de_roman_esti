from contextlib import redirect_stdout
from hashlib import sha1, sha256
from io import StringIO
import bz2
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_cached_nouns as comparator
from wiktionary_dump import (
    DUPLICATE_MANIFEST_FAILURE, DumpError, UnsupportedTable, extract, main, parse_literal_noun_table, parse_literal_table,
)

TEST_SCRATCH = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd()))

DAY = "20261101"
BASE = f"https://dumps.wikimedia.org/rowiktionary/{DAY}/rowiktionary-{DAY}-"
ARCHIVE = "pages-articles.xml.bz2"
MANIFEST = "sha1sums.txt"
START = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">'
    '<siteinfo><dbname>rowiktionary</dbname></siteinfo>'
)
END = '</mediawiki>'
RAW = "  =={{limba|ron}}==\nȚ & < > &lt; \N{COMBINING COMMA BELOW}\r\n\t"


def write_json(path, value):
    path.write_bytes(json.dumps(value, separators=(",", ":")).encode() + b"\n")


def write_receipt(cache, suffix, body, extension, **extra):
    url = suffix if suffix.startswith("https://") else BASE + suffix
    digest = sha256(body).hexdigest()
    receipt = {
        "url": url, "sha256": digest, "status": 200, "bytes": len(body),
        "origin": "v5", "first_fetch_origin": "v5", "first_fetcher": "fixture",
        "fetched_by_role": "script", "attempt_fetcher": "fixture", "attempt_role": "script",
        **extra,
    }
    path = cache / (sha256(url.encode()).hexdigest() + ".receipt.json")
    write_json(path, receipt)
    (cache / (digest + extension)).write_bytes(body)
    return receipt, path


def archive(cache, xml, body=None, *, recover=False, manifest_extra=""):
    if body is None:
        body = bz2.compress(xml.encode())
    published = sha1(body, usedforsecurity=False).hexdigest()
    filename = f"rowiktionary-{DAY}-{ARCHIVE}"
    lines = f"{published} *{filename}\r\n" + manifest_extra.format(filename=filename)
    failure = {"dump_failure": DUPLICATE_MANIFEST_FAILURE} if recover else {}
    manifest, manifest_path = write_receipt(
        cache, MANIFEST, lines.encode(), ".diagnostic" if recover else ".body", **failure
    )
    checksum = {"url": manifest["url"], "sha256": manifest["sha256"], "sha1": published}
    if recover:
        url_key = sha256(manifest["url"].encode()).hexdigest()
        marker = sha256(manifest_path.read_bytes()[:-1]).hexdigest()
        state_path = cache / "dumps.wikimedia.org.v5-state.json"
        write_json(state_path, {"dump_attempts": {url_key: {"outcome_sha256": marker}}})
        checksum["recovered_outcome_sha256"] = marker
    return write_receipt(cache, ARCHIVE, body, ".dump", dump_checksum=checksum)

def page(title, *, ns=0, raw=RAW, revision=12345, duplicate_revision=False, redirect=False):
    payload = escape(raw).replace("\r", "&#13;")
    data = (
        f"<revision><id>{revision}</id><contributor><id>991</id></contributor>"
        "<model>wikitext</model><format>text/x-wiki</format>"
        f'<text bytes="{len(raw.encode())}" xml:space="preserve">{payload}</text></revision>'
    )
    return (
        f"<page><title>{escape(title)}</title><ns>{ns}</ns><id>1</id>"
        + ('<redirect title="elsewhere"/>' if redirect else "")
        + data * (2 if duplicate_revision else 1)
        + "</page>"
    )


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=TEST_SCRATCH)
        self.addCleanup(self.directory.cleanup)
        self.cache = Path(self.directory.name)

    def test_exact_namespace_and_raw_unicode_bytes(self):
        first = page("Șură", ns=10)
        second = page("șură", revision=12555)
        third = page("Șură", raw=RAW)
        receipt, receipt_path = archive(self.cache, START + first + second + third + END)
        got = extract(self.cache, DAY, ["Șură", "Sura", "Șură "])
        self.assertEqual(got["archive_sha256"], receipt["sha256"])
        self.assertEqual(got["archive_receipt_sha256"], sha256(receipt_path.read_bytes()).hexdigest())
        self.assertEqual(got["missing_titles"], ["Sura", "Șură "])
        self.assertEqual(got["pages"], [{
            "title": "Șură", "revision_id": 12345, "text_bytes": len(RAW.encode()),
            "text_sha256": sha256(RAW.encode()).hexdigest(), "wikitext": RAW,
        }])

    def test_rejects_wrong_checksum_despite_valid_pinned_file(self):
        _, path = archive(self.cache, START + page("Șură") + END)
        receipt = json.loads(path.read_bytes())
        receipt["dump_checksum"]["sha1"] = "0" * 40
        path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(DumpError, "published checksum"):
            extract(self.cache, DAY, ["Șură"])

    def test_unrelated_duplicates_allowed_but_requested_duplicate_rejected(self):
        xml = START + page("șură") + END
        duplicate = f"{'a' * 40}  unrelated.sql.gz\n" * 2
        for recover in (False, True):
            with self.subTest(recover=recover):
                archive(self.cache, xml, recover=recover, manifest_extra=duplicate)
                self.assertEqual(extract(self.cache, DAY, ["șură"])["pages"][0]["wikitext"], RAW)
                archive(
                    self.cache, xml, recover=recover, manifest_extra="b" * 40 + "  {filename}\n",
                )
                with self.assertRaisesRegex(DumpError, "repeats the requested archive filename"):
                    extract(self.cache, DAY, ["șură"])

    def test_recovery_requires_bound_original_receipt_attempt_and_diagnostic(self):
        xml = START + page("șură") + END
        duplicate = f"{'a' * 40}  unrelated.sql.gz\n" * 2
        manifest_key = sha256((BASE + MANIFEST).encode()).hexdigest()
        manifest_path = self.cache / (manifest_key + ".receipt.json")
        state_path = self.cache / "dumps.wikimedia.org.v5-state.json"
        for tamper in ("marker", "ledger", "receipt", "diagnostic", "wrong code", "partial", "role"):
            with self.subTest(tamper=tamper):
                receipt, archive_path = archive(self.cache, xml, recover=True, manifest_extra=duplicate)
                diagnostic = self.cache / (receipt["dump_checksum"]["sha256"] + ".diagnostic")
                if tamper == "marker":
                    receipt["dump_checksum"]["recovered_outcome_sha256"] = "f" * 64
                    write_json(archive_path, receipt)
                elif tamper == "ledger":
                    write_json(state_path, {"dump_attempts": {manifest_key: {"outcome_sha256": "f" * 64}}})
                elif tamper == "receipt":
                    raw = manifest_path.read_bytes()
                    manifest_path.write_bytes(raw.replace(b'"fixture"', b'"newrole"'))
                elif tamper == "diagnostic":
                    raw = diagnostic.read_bytes()
                    diagnostic.write_bytes(raw.replace(b"unrelated", b"elsewhere"))
                else:
                    manifest = json.loads(manifest_path.read_bytes())
                    if tamper == "wrong code":
                        manifest["dump_failure"]["code"] = "crawler_block"
                    elif tamper == "partial":
                        manifest["body_problem"] = "incomplete"
                    else:
                        manifest["attempt_role"] = manifest["fetched_by_role"] = "author"
                    write_json(manifest_path, manifest)
                    marker = sha256(manifest_path.read_bytes()[:-1]).hexdigest()
                    write_json(state_path, {"dump_attempts": {manifest_key: {"outcome_sha256": marker}}})
                    receipt["dump_checksum"]["recovered_outcome_sha256"] = marker
                    write_json(archive_path, receipt)
                with self.assertRaises(DumpError):
                    extract(self.cache, DAY, ["șură"])

    def test_recovery_marker_cannot_be_omitted(self):
        xml = START + page("șură") + END
        receipt, archive_path = archive(self.cache, xml, recover=True)
        del receipt["dump_checksum"]["recovered_outcome_sha256"]
        write_json(archive_path, receipt)
        with self.assertRaisesRegex(DumpError, "records a failure"):
            extract(self.cache, DAY, ["șură"])

    def test_rejects_tampered_bytes_and_never_writes_partial_output(self):
        receipt, path = archive(self.cache, START + page("Șură") + END)
        replacement = bz2.compress((START + page("Șură", revision=54321) + END).encode())
        (self.cache / (receipt["sha256"] + ".dump")).write_bytes(replacement)
        receipt["bytes"] = len(replacement)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        stdout, stderr = StringIO(), StringIO()
        with (
            patch("sys.argv", ["cmd", "--cache", str(self.cache), "--date", DAY, "Șură"]),
            redirect_stdout(stdout), patch("sys.stderr", stderr),
        ):
            self.assertEqual(main(), 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("pinned SHA-256", stderr.getvalue())

    def test_rejects_duplicate_pages_revisions_and_redirects(self):
        for payload in (
            page("șură") + page("șură"),
            page("șură", duplicate_revision=True),
            page("șură", redirect=True),
        ):
            with self.subTest(payload=payload):
                archive(self.cache, START + payload + END)
                with self.assertRaises(DumpError):
                    extract(self.cache, DAY, ["șură"])

    def test_rejects_truncation_after_requested_page(self):
        xml = START + page("șură") + page("other") + END
        archive(self.cache, xml, body=bz2.compress(xml.encode())[:-5])
        with self.assertRaisesRegex(DumpError, "truncated"):
            extract(self.cache, DAY, ["șură"])

    def test_rejects_dtd_and_decompression_limit(self):
        xml = START.replace("?>", '?><!DOCTYPE mediawiki [<!ENTITY invalid "expand">]>')
        archive(self.cache, xml + page("șură") + END)
        with self.assertRaisesRegex(DumpError, "entities, DTDs"):
            extract(self.cache, DAY, ["șură"])
        archive(self.cache, START + page("șură") + END)
        with patch("wiktionary_dump.MAX_XML", 100):
            with self.assertRaisesRegex(DumpError, "decompressed byte limit"):
                extract(self.cache, DAY, ["șură"])

    def test_rejects_large_unfinished_xml_token(self):
        archive(self.cache, START + "<!--" + "q" * 2000 + "-->" + END)
        with patch("wiktionary_dump.MAX_XML_TOKEN", 256), patch("wiktionary_dump.CHUNK", 64):
            with self.assertRaisesRegex(DumpError, "oversized unfinished token"):
                extract(self.cache, DAY, ["șură"])

    def test_rejects_xml_carriage_return_normalization(self):
        archive(self.cache, START + page("șură", raw="\r").replace("&#13;", "\r") + END)
        with self.assertRaisesRegex(DumpError, "literal CR"):
            extract(self.cache, DAY, ["șură"])

    def test_rejects_utf16_with_and_without_bom_and_declared_alternate_encoding(self):
        xml = START.split("\n", 1)[1] + page("șură") + END
        with patch("wiktionary_dump.CHUNK", 7):
            for encoding in ("utf-16", "utf-16le", "utf-16be"):
                with self.subTest(encoding=encoding):
                    archive(self.cache, xml, body=bz2.compress(xml.encode(encoding)))
                    with self.assertRaisesRegex(DumpError, "UTF-8 XML|valid UTF-8 bytes"):
                        extract(self.cache, DAY, ["șură"])
        xml = (START + page("șură") + END).replace('encoding="UTF-8"', 'encoding="iso-8859-1"')
        archive(self.cache, xml)
        with self.assertRaisesRegex(DumpError, "alternate encodings"):
            extract(self.cache, DAY, ["șură"])

    def test_utf8_validation_crosses_chunks_and_bzip_members(self):
        xml = (START + page("șură") + END).encode("utf-8")
        split = xml.index("ș".encode("utf-8")) + 1
        with patch("wiktionary_dump.CHUNK", 7):
            body = bz2.compress(xml[:split]) + bz2.compress(xml[split:])
            archive(self.cache, None, body=body)
            self.assertEqual(extract(self.cache, DAY, ["șură"])["pages"][0]["wikitext"], RAW)
            archive(self.cache, None, body=bz2.compress(xml[:split] + b"!" + xml[split + 1:]))
            with self.assertRaisesRegex(DumpError, "valid UTF-8 bytes"):
                extract(self.cache, DAY, ["șură"])
        archive(self.cache, None, body=bz2.compress(xml + b"\xc8"))
        with self.assertRaisesRegex(DumpError, "valid UTF-8 bytes"):
            extract(self.cache, DAY, ["șură"])

    def test_accepts_concatenated_bz2_and_rejects_wrong_database(self):
        xml = START + page("șură") + END
        body = bz2.compress(xml[:75].encode()) + bz2.compress(xml[75:].encode())
        archive(self.cache, xml, body=body)
        self.assertEqual(extract(self.cache, DAY, ["șură"])["pages"][0]["wikitext"], RAW)
        archive(self.cache, xml.replace("rowiktionary", "rowiki"))
        with self.assertRaisesRegex(DumpError, "rowiktionary site"):
            extract(self.cache, DAY, ["șură"])

    def test_rejects_missing_and_ambiguous_text(self):
        for text_element in (
            '<text deleted="deleted" bytes="0" />',
            '<text bytes="1">pre<b/>post</text>',
            '<text bytes="1">ș</text>',
        ):
            with self.subTest(text_element=text_element):
                xml = page("șură", raw="raw")
                xml = xml.replace('<text bytes="3" xml:space="preserve">raw</text>', text_element)
                archive(self.cache, START + xml + END)
                with self.assertRaises(DumpError):
                    extract(self.cache, DAY, ["șură"])


NOUN = """=={{limba|ron}}==
{{-substantiv-|ron}}
{{substantiv-ron
|gen={{f}}
|nom-sg=mentă
|nom-pl={{inv}}
|art-sg=menta
|art-pl={{inv}}
|dat-sg=mentei
|dat-pl={{inv}}
|voc-sg=mentă, mento\x20
|voc-pl={{inv}}
}}
# definiție
"""


class NounTests(unittest.TestCase):
    def test_visible_labels_and_literal_alternatives(self):
        self.assertEqual(parse_literal_noun_table("mentă", NOUN), [
            ("Nominativ-Acuzativ", "Singular", "mentă"), ("Articulat", "Singular", "menta"),
            ("Genitiv-Dativ", "Singular", "mentei"), ("Vocativ", "Singular", "mentă"),
            ("Vocativ", "Singular", "mento"),
        ])

    def test_plural_only_cells_and_exact_placeholder_labels(self):
        plural_only = (NOUN.replace("mentă", "{{inv}}").replace("|nom-pl={{inv}}", "|nom-pl=ochelari")
            .replace("|art-sg=menta", "|art-sg={{inv}}").replace("|art-pl={{inv}}", "|art-pl=ochelarii")
            .replace("|dat-sg=mentei", "|dat-sg={{inv}}").replace("|dat-pl={{inv}}", "|dat-pl=ochelarilor")
            .replace("|voc-sg={{inv}}, mento ", "|voc-sg={{inv}}"))
        got = parse_literal_table("ochelari", plural_only, "noun")
        self.assertEqual(got["invariable_cells"], [
            ("Nominativ-Acuzativ", "Singular"), ("Articulat", "Singular"),
            ("Genitiv-Dativ", "Singular"), ("Vocativ", "Singular"), ("Vocativ", "Plural"),
        ])
        self.assertEqual(len(got["forms"]), 3)
        with self.assertRaisesRegex(UnsupportedTable, "plural-only"):
            parse_literal_table("ochelari", plural_only.replace("|art-sg={{inv}}", "|art-sg=ochelarii"), "noun")

    def test_slash_variants_stay_in_their_actual_plural_cells(self):
        raw = NOUN.replace("|nom-pl={{inv}}", "|nom-pl=mente/menturi")
        raw = raw.replace("|art-pl={{inv}}", "|art-pl=mente/menturile")
        forms = parse_literal_table("mentă", raw, "noun")["forms"]
        self.assertIn(("Nominativ-Acuzativ", "Plural", "mente"), forms)
        self.assertIn(("Articulat", "Plural", "menturile"), forms)
        for value in ("menta/mente", "menta{{inv}}"):
            with self.subTest(value=value), self.assertRaises(UnsupportedTable):
                parse_literal_table("mentă", raw.replace("|art-sg=menta", "|art-sg=" + value), "noun")

    def test_no_foreign_comment_opaque_or_nested_matches(self):
        for raw in (
            NOUN.replace("|ron", "|eng"),
            "<!--\n" + NOUN + "\n-->",
            "<nowiki\n class='>'>\n" + NOUN + "\n</nowiki>",
            "{{wrap|\n" + NOUN + "\n}}",
            NOUN + NOUN,
        ):
            with self.subTest(raw=raw), self.assertRaises(UnsupportedTable):
                parse_literal_noun_table("mentă", raw)

    def test_comment_aware_headings_end_the_romanian_section(self):
        head, rest = NOUN.split("\n", 1)
        for heading in (
            "=={{limba|eng}}== <!-- language -->",
            "=={{limba|eng}}== <!-- language with literal <span title='--> ",
            "<!-- language -->=={{limba|eng}}==",
            "=={{limba|<!-- language -->eng}}==",
            "=={{limba|eng}}<!-- delimiter -->==",
            "= Other heading =",
            "== Asymmetric heading ===",
            "=={{limba|eng}}== <!-- multi\nline -->",
        ):
            with self.subTest(heading=heading), self.assertRaises(UnsupportedTable):
                parse_literal_noun_table("mentă", f"{head}\n{heading}\n{rest}")
        raw = "<!-- title -->" + NOUN.replace(head, head + " <!-- language -->", 1)
        self.assertEqual(parse_literal_noun_table("mentă", raw), parse_literal_noun_table("mentă", NOUN))

    def test_literal_nowiki_comment_cannot_hide_a_foreign_heading(self):
        head, rest = NOUN.split("\n", 1)
        for hidden_close in ("<nowiki><!--</nowiki>-->", '<nowiki><span title="</nowiki>">'):
            raw = f"{head}\n{hidden_close}\n=={{{{limba|eng}}}}==\n<nowiki>x</nowiki>\n{rest}"
            with self.subTest(hidden_close=hidden_close), self.assertRaises(UnsupportedTable):
                parse_literal_noun_table("mentă", raw)

    def test_unsupported_wrappers_fail_closed_but_foreign_markup_is_ignored(self):
        for start, end in (
            ('<div style="display:none">', '</div>'),
            ("<blockquote>", "</blockquote>"),
            ("<includeonly/>", ""),
            ("<span title='unterminated", ""),
            ("{|", "|}"),
        ):
            with self.subTest(start=start), self.assertRaises(UnsupportedTable):
                parse_literal_noun_table("mentă", f"{start}\n{NOUN}\n{end}")
        head, rest = NOUN.split("\n", 1)
        with self.assertRaises(UnsupportedTable):
            parse_literal_noun_table("mentă", f"{head}\n<div>\n{rest}</div>")
        foreign = "=={{limba|eng}}== <!-- language -->\n#:<table><tr><td>gloss</table>\n"
        self.assertEqual(parse_literal_noun_table("mentă", NOUN + foreign), parse_literal_noun_table("mentă", NOUN))
        leading_image_table = "{|align=right\n|-\n|[[Fișier:mentă.jpg|thumb|Mentă]]\n|}\n"
        self.assertEqual(
            parse_literal_noun_table("mentă", f"{head}\n{leading_image_table}{rest}"),
            parse_literal_noun_table("mentă", NOUN),
        )

    def test_rejects_unsupported_value_or_parameter_for_whole_table(self):
        for raw in (
            NOUN.replace("|art-sg=menta", "|art-sg={{compound|ment|a}}"),
            NOUN.replace("|art-sg=menta", "|art-sg=[[menta]]"),
            NOUN.replace("|art-sg=menta", "|art-sg=menta\n|art-sg=altul"),
            NOUN.replace("|art-sg=menta", "|unknown=menta"),
            NOUN.replace("|art-sg=menta", "|art-sg=menta\n|extra=menta"),
            NOUN.replace("|art-sg=menta", "|art-sg=menta, ment[a]"),
            NOUN.replace("{{substantiv-ron", "  {{substantiv-ron"),
            NOUN.replace("|nom-sg=mentă", "|nom-sg={{inv}}"),
            NOUN.replace("|nom-sg=mentă", "|nom-sg=altul"),
        ):
            with self.subTest(raw=raw), self.assertRaises(UnsupportedTable):
                parse_literal_noun_table("mentă", raw)


class AdjectiveTests(unittest.TestCase):
    RAW = """=={{limba|ron}}==
{{-adjectiv-|ron}}
{{adjectiv-ron
|m-sg=luminos
|m-pl=[[luminoși]]
|f-sg=[[luminoasă]]
|f-pl=[[luminoase]]
}}
"""

    def test_adjective_maps_all_six_visible_cells_from_literal_parameters(self):
        self.assertEqual(parse_literal_table("luminos", self.RAW, "adjective"), {
            "forms": [
                ("Masculin", "Singular", "luminos"), ("Neutru", "Singular", "luminos"),
                ("Masculin", "Plural", "luminoși"), ("Feminin", "Singular", "luminoasă"),
                ("Feminin", "Plural", "luminoase"), ("Neutru", "Plural", "luminoase"),
            ],
            "invariable_cells": [],
        })

    def test_adjective_rejects_piped_links_template_cells_and_defaults(self):
        for value in ("[[luminoase|forme]]", "{{generate|luminoase}}", "", "[[Category:luminoase]]"):
            with self.subTest(value=value), self.assertRaises(UnsupportedTable):
                parse_literal_table("luminos", self.RAW.replace("[[luminoase]]", value), "adjective")


class ComparatorTests(unittest.TestCase):
    title = "mentă"
    revision = 1170178
    url = comparator.WIKI + "ment%C4%83"

    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=TEST_SCRATCH)
        self.addCleanup(directory.cleanup)
        self.cache = Path(directory.name)
        self.manifest = self.cache / "sample.json"
        receipt, _ = archive(self.cache, START + page(self.title, raw=NOUN, revision=self.revision) + END)
        self.archive_sha = receipt["sha256"]
        self.manifest_data = {
            "archive_date": DAY,
            "archive_sha256": self.archive_sha,
            "pages": [{"title": self.title, "dump_revision": self.revision, "category": "ordinary noun"}],
        }

    def rendered(self, cell="mentă"):
        config = json.dumps({
            "wgTitle": self.title, "wgPageName": self.title, "wgRevisionId": self.revision,
            "wgNamespaceNumber": 0, "wgIsRedirect": False,
        }, ensure_ascii=False)
        return (
            f'<html><head><link rel="canonical" href="{self.url}"><script>RLCONF={config};</script></head>'
            '<body><table class="substantiv-ron"><tbody>'
            '<tr><td colspan="3"><b>Declinarea substantivului <br/><span>mentă</span></b></td></tr>'
            '<tr><td>f.</td><td>Singular</td><td>Plural</td></tr>'
            f'<tr><td>Nominativ-Acuzativ</td><td>{cell}</td><td><i>invariabil</i></td></tr>'
            '<tr><td>Articulat</td><td>menta</td><td>invariabil</td></tr>'
            '<tr><td>Genitiv-Dativ</td><td>mentei</td><td>invariabil</td></tr>'
            '<tr><td>Vocativ</td><td>mentă, mento</td><td>invariabil</td></tr>'
            '</tbody></table></body></html>'
        )

    def cache_page(self, html, **extra):
        extra = {
            "headers": {"content-type": "text/html; charset=UTF-8"},
            "first_fetcher": comparator.FRESH_FETCHER,
            "attempt_fetcher": comparator.FRESH_FETCHER,
            **extra,
        }
        return write_receipt(self.cache, self.url, html.encode("utf-8"), ".body", **extra)

    def compare(self):
        return comparator.compare(self.cache, DAY, self.archive_sha, [(self.title, self.revision, "noun")])

    def test_exact_dump_revision_matches_and_receipt_binds_inputs(self):
        receipt, path = self.cache_page(self.rendered('<a href="/wiki/ment%C4%83" rel="mw:WikiLink">mentă</a>'))
        result = self.compare()
        self.assertTrue(result["equal"])
        row, = result["pages"]
        self.assertEqual(row["cached_revision"], self.revision)
        self.assertEqual(row["cached_receipt_sha256"], sha256(path.read_bytes()).hexdigest())
        self.assertEqual(row["cached_body_sha256"], receipt["sha256"])
        self.assertEqual(row["dump_text_sha256"], sha256(NOUN.encode()).hexdigest())
        self.assertEqual(result["parser_sha256"], sha256(Path(comparator.__file__).with_name("wiktionary_dump.py").read_bytes()).hexdigest())

    def visible_cells(self, html, title, kind):
        parsed = comparator.PageHTML()
        parsed.feed(html)
        parsed.close()
        return comparator.rendered_cells(parsed.tables, title, kind)

    def test_classless_adjective_with_localized_red_link(self):
        red_link = (
            '<a rel="mw:WikiLink" href="https://ro.wiktionary.org/wiki/luminoși?action=edit&amp;redlink=1" '
            'title="luminoși (pagină inexistentă)" class="new" typeof="mw:LocalizedAttrs" '
            """data-mw-i18n='{"title":{"lang":"x-page","key":"red-link-title","params":["luminoși"]}}'>luminoși</a>"""
        )
        html = (
            '<table cellspacing="1" width="33%" style="float:right;background:#bdb;color:#353;" about="#mwt9">'
            '<tbody><tr><td colspan="3"><b>Declinarea adjectivului <br/><span>luminos</span></b></td></tr>'
            '<tr><td></td><td><b>Singular</b></td><td><b>Plural</b></td></tr>'
            f'<tr><td>Masculin</td><td>luminos</td><td><b>{red_link}</b></td></tr>'
            '<tr><td>Feminin</td><td>luminoasă</td><td>luminoase</td></tr>'
            '<tr><td>Neutru</td><td>luminos</td><td>luminoase</td></tr></tbody></table>'
        )
        expected = {
            ("Masculin", "Singular", "luminos"), ("Masculin", "Plural", "luminoși"),
            ("Feminin", "Singular", "luminoasă"), ("Feminin", "Plural", "luminoase"),
            ("Neutru", "Singular", "luminos"), ("Neutru", "Plural", "luminoase"),
        }
        self.assertEqual(self.visible_cells(html, "luminos", "adjective"), (expected, set()))
        for old, new in (
            ('typeof="mw:LocalizedAttrs"', 'typeof="mw:Transclusion"'),
            ('typeof="mw:LocalizedAttrs" ', ""),
            ('class="new"', 'class="new" hidden'),
            ('class="new"', 'class="mw-redirect"'),
            ('"key":"red-link-title"', '"key":"red-link-title","style":"display:none"'),
            ('"lang":"x-page"', '"lang":"x-page","lang":"x-page"'),
            ('"params":["luminoși"]', '"params":["altul"]'),
            ("redlink=1", "redlink=0"),
        ):
            with self.subTest(new=new), self.assertRaisesRegex(DumpError, "unsupported rendered"):
                self.visible_cells(html.replace(old, new), "luminos", "adjective")

    def test_plural_only_noun_caption_requires_complete_singular_markers(self):
        html = (
            '<table class="substantiv-ron"><tbody>'
            '<tr><td colspan="3"><b>Declinarea substantivului <br/>'
            '<span><i><small>invariabil</small></i></span></b></td></tr>'
            '<tr><td>f.</td><td>Singular</td><td>Plural</td></tr>'
            '<tr><td>Nominativ-Acuzativ</td><td><i><small>invariabil</small></i></td><td>aplauze</td></tr>'
            '<tr><td>Articulat</td><td>invariabil</td><td>aplauzele</td></tr>'
            '<tr><td>Genitiv-Dativ</td><td>invariabil</td><td>aplauzelor</td></tr>'
            '<tr><td>Vocativ</td><td>invariabil</td><td>aplauzelor</td></tr></tbody></table>'
        )
        forms = {
            ("Nominativ-Acuzativ", "Plural", "aplauze"), ("Articulat", "Plural", "aplauzele"),
            ("Genitiv-Dativ", "Plural", "aplauzelor"), ("Vocativ", "Plural", "aplauzelor"),
        }
        self.assertEqual(
            self.visible_cells(html, "aplauze", "noun"),
            (forms, {(row, "Singular") for row, _, _ in forms}),
        )
        for old, new in (
            ("<td>aplauze</td>", "<td>aplauze / altul</td>"),
            ("<td>aplauze</td>", "<td>altul</td>"),
            ("<td>invariabil</td>", "<td>-</td>"),
            ("<span><i>", "<span hidden><i>"),
            ("<span><i><small>invariabil", "<span><i><small>aplauze"),
        ):
            with self.subTest(new=new), self.assertRaisesRegex(DumpError, "unsupported rendered"):
                self.visible_cells(html.replace(old, new), "aplauze", "noun")

    def test_rendered_breaks_and_unsupported_markup_do_not_create_forms(self):
        for cell in (
            "men<br>tă", "men<br/>tă", "mentă<br>", "men<sup>tă</sup>", "men<!-- comment -->tă",
            "men<span hidden>tă</span>", "<span style='display:none'>mentă</span>",
            "<span style='color:#335' style='display:none'>mentă</span>",
        ):
            with self.subTest(cell=cell):
                self.cache_page(self.rendered(cell))
                row, = self.compare()["pages"]
                self.assertFalse(row["equal"])
                self.assertIn("unsupported rendered", row["error"])
        self.cache_page(self.rendered().replace("<body>", "<body><div hidden>").replace("</body>", "</div></body>"))
        self.assertFalse(self.compare()["equal"])

    def test_html_ancestors_cannot_hide_a_rendered_table(self):
        for wrapper in (
            "<template/>", "<div hidden/>", "<div style='display:/**/none'>",
            "<div class='plain' class='hidden'>",
        ):
            with self.subTest(wrapper=wrapper):
                self.cache_page(self.rendered().replace("<body>", "<body>" + wrapper))
                self.assertFalse(self.compare()["equal"])
        self.cache_page(self.rendered("<span/>mentă"))
        self.assertFalse(self.compare()["equal"])

    def test_cache_refuses_wrong_identity_revision_provenance_and_body(self):
        html = self.rendered()
        for bad in (
            html.replace(self.url, comparator.WIKI + "different"),
            html.replace(str(self.revision), "12345"),
            html.replace('"wgPageName": "mentă"', '"wgPageName": "another title"'),
            html.replace('"wgRevisionId": 1170178', '"wgRevisionId": 1170178, "wgRevisionId": 12345'),
            html.replace("</head>", '<link rel="canonical" href="' + self.url + '"></head>'),
        ):
            with self.subTest(bad=bad[:120]):
                self.cache_page(bad)
                self.assertFalse(self.compare()["equal"])
        self.cache_page(html, first_fetcher="other", attempt_fetcher="other")
        self.assertIn("fetch provenance", self.compare()["pages"][0]["error"])
        receipt, receipt_path = self.cache_page(html)
        body_path = self.cache / (receipt["sha256"] + ".body")
        body_path.write_bytes(b"x" * receipt["bytes"])
        self.assertIn("differs from its receipt", self.compare()["pages"][0]["error"])
        receipt_path.rename(receipt_path.with_name("not-the-canonical-receipt.json"))
        self.assertIn("missing canonical", self.compare()["pages"][0]["error"])

    def test_different_archive_pin_and_reused_sample_evidence_are_rejected(self):
        with self.assertRaisesRegex(DumpError, "requested SHA-256"):
            comparator.compare(self.cache, DAY, "f" * 64, [(self.title, self.revision, "noun")])
        for rows in (
            [("title", 1, "noun"), ("title", 2, "noun")],
            [("first", 1, "noun"), ("second", 1, "noun")],
        ):
            with self.assertRaisesRegex(DumpError, "distinct titles and distinct revision IDs"):
                comparator.validate_samples(rows, 2)

    def test_cli_checks_pinned_sample_and_exits_nonzero_on_missing_or_mismatch(self):
        write_json(self.manifest, self.manifest_data)
        args = ["check_cached_nouns", str(self.cache), "--sample", str(self.manifest)]
        digest = sha256(self.manifest.read_bytes()).hexdigest()
        with patch("sys.argv", args), redirect_stdout(StringIO()), patch("sys.stderr", StringIO()):
            self.assertEqual(comparator.main(), 2)
        validate = comparator.validate_samples
        with (
            patch("sys.argv", args), patch.object(comparator, "SAMPLE_SHA256", digest),
            patch.object(comparator, "validate_samples", side_effect=lambda rows, _: validate(rows, 1)),
        ):
            with redirect_stdout(StringIO()) as stdout:
                self.assertEqual(comparator.main(), 1)
            self.assertIn("missing canonical", json.loads(stdout.getvalue())["pages"][0]["error"])
            self.cache_page(self.rendered("mento"))
            with redirect_stdout(StringIO()) as stdout:
                self.assertEqual(comparator.main(), 1)
            self.assertEqual(json.loads(stdout.getvalue())["pages"][0]["rendered_only"], [["Nominativ-Acuzativ", "Singular", "mento"]])
            self.cache_page(self.rendered())
            with redirect_stdout(StringIO()):
                self.assertEqual(comparator.main(), 0)


if __name__ == "__main__":
    unittest.main()
