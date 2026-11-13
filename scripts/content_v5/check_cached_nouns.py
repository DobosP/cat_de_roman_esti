#!/usr/bin/env python3
"""Compare pinned dump revisions with the exact cached rendered sample."""

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote
from xml.parsers import expat

from wiktionary_dump import (
    FORM, MAX_MANIFEST, DumpError, extract, parse_literal_table, read_small, receipt_for, unique_keys,
)

SAMPLE_SHA256 = "b429d57a83f2afa12d758e68584eda7505e6e4a9496cee5976717a70481efc48"
MAX_HTML = 16 * 1024 * 1024
MAX_SCRIPT = 128 * 1024
MAX_CODE = 128 * 1024
WIKI = "https://ro.wiktionary.org/wiki/"
CONFIG = re.compile(r"(?<![\w.$])RLCONF\s*=\s*(?=\{)")
JSON = json.JSONDecoder(object_pairs_hook=unique_keys)
FRESH_FETCHER = "pilot2-parser-gate-live"
RENDERED_LAYOUTS = {
    "noun": (
        "Declinarea substantivului",
        ("Nominativ-Acuzativ", "Articulat", "Genitiv-Dativ", "Vocativ"),
    ),
    "adjective": ("Declinarea adjectivului", ("Masculin", "Feminin", "Neutru")),
}
CATEGORY_KIND = {
    "adjective": "adjective",
    "invariable-marked noun": "noun",
    "plural-only noun": "noun",
    "single table with two plurals": "noun",
    "ordinary noun": "noun",
}
TABLE_CLASSES = {"substantiv-ron", "adjectiv-ron"}
STRUCTURE = {"table": {"tbody", "tr"}, "tbody": {"tr"}, "tr": {"td", "th"}}
CELL_TAGS = {"a", "b", "i", "small", "span", "strong", "em", "br"}
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
HIDDEN = {"template", "noscript", "textarea", "script", "style", "details"}
STYLES = re.compile(r"(?:(?:background|color):#[0-9a-fA-F]{3,8};?|float:right;?)+")
PRESENTATION_ATTRIBUTES = {
    "table": {"about", "cellspacing", "width", "style", "class"},
    "td": {"width", "colspan", "valign", "align", "style"},
    "th": {"width", "colspan", "valign", "align", "style"},
    "span": {"title", "style"},
    "a": {"href", "title", "rel", "id", "class"},
}


def valid_attributes(tag, pairs):
    attrs = dict(pairs)
    if len(attrs) != len(pairs) or attrs.keys() - PRESENTATION_ATTRIBUTES.get(tag, set()):
        return False
    if "style" in attrs and not STYLES.fullmatch(attrs["style"] or ""):
        return False
    if "class" in attrs and attrs["class"] not in TABLE_CLASSES | {"new", "mw-redirect"}:
        return False
    if "colspan" in attrs and attrs["colspan"] != "3":
        return False
    return True


class RenderedTable:
    def __init__(self, attributes, *, hidden):
        classes = (dict(attributes).get("class") or "").split()
        self.candidate = bool(TABLE_CLASSES.intersection(classes))
        self.invalid = hidden or not valid_attributes("table", attributes)
        self.tags = ["table"]
        self.rows = []
        self.cell = []
        self.spans = []

    def start(self, tag, attributes):
        if len(self.tags) >= 128:
            raise DumpError("rendered table nesting exceeds the comparator limit")
        parent = self.tags[-1]
        if parent in STRUCTURE:
            allowed = tag in STRUCTURE[parent]
        else:
            allowed = tag in CELL_TAGS
        if not allowed or not valid_attributes(tag, attributes):
            self.invalid = True
        if tag == "tr":
            self.rows.append([])
            self.spans.append([])
        if tag in {"td", "th"}:
            self.cell = []
            if self.spans:
                self.spans[-1].append(dict(attributes).get("colspan", "1"))
        if tag == "br":
            self.cell.append("\n")
            if len(self.rows) > 1:
                self.invalid = True
        elif tag not in VOID:
            self.tags.append(tag)

    def end(self, tag):
        if self.tags[-1] != tag:
            self.invalid = True
            if tag == "table" and "table" not in self.tags[1:]:
                self.tags.clear()
            return
        if tag in {"td", "th"} and self.rows:
            self.rows[-1].append("".join(self.cell).strip())
        self.tags.pop()

    def data(self, data):
        if self.tags[-1] in {"td", "th"} | CELL_TAGS:
            self.cell.append(data)
        elif data.strip():
            self.invalid = True


class PageHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.script = None
        self.canonical = []
        self.configs = []
        self.tables = []
        self.table = None
        self.ancestors = []

    def handle_starttag(self, tag, attributes):
        if self.table is not None:
            self.table.start(tag, attributes)
            return
        if tag == "table":
            if self.in_head:
                raise DumpError("rendered table occurs in the HTML head")
            self.table = RenderedTable(attributes, hidden=any(hidden for _, hidden in self.ancestors))
            return
        if tag == "head":
            self.in_head = True
        elif tag == "script" and self.in_head and not attributes:
            self.script = []
        elif tag == "link" and self.in_head:
            attrs = dict(attributes)
            if (attrs.get("rel") or "").lower() == "canonical":
                if len(attrs) != len(attributes):
                    raise DumpError("duplicate canonical link attributes")
                self.canonical.append(attrs.get("href"))
        if tag not in VOID:
            if len(self.ancestors) >= 128:
                raise DumpError("rendered HTML nesting exceeds the comparator limit")
            attrs = dict(attributes)
            hidden = (
                tag in HIDDEN
                or "hidden" in attrs
                or (attrs.get("aria-hidden") or "").lower() == "true"
                or "style" in attrs
                or len(attrs) != len(attributes)
            )
            self.ancestors.append((tag, hidden))

    def handle_startendtag(self, tag, attributes):
        if self.table is not None and tag not in VOID:
            self.table.invalid = True
        # HTML self-closing syntax does not close nonvoid elements.
        self.handle_starttag(tag, attributes)

    def handle_endtag(self, tag):
        if self.table is not None:
            self.table.end(tag)
            if not self.table.tags:
                self.tables.append(self.table)
                self.table = None
            return
        if tag == "script" and self.script is not None:
            text = "".join(self.script)
            self.script = None
            for match in CONFIG.finditer(text):
                if len(text) > MAX_SCRIPT:
                    raise DumpError("oversized MediaWiki page metadata script")
                value, _ = JSON.raw_decode(text, match.end())
                self.configs.append(value)
        elif tag == "head":
            self.in_head = False
        for index in range(len(self.ancestors) - 1, -1, -1):
            if self.ancestors[index][0] == tag:
                del self.ancestors[index:]
                break

    def handle_data(self, data):
        if self.table is not None:
            self.table.data(data)
        elif self.script is not None:
            self.script.append(data)

    def handle_comment(self, _data):
        if self.table is not None:
            self.table.invalid = True

    handle_decl = handle_comment
    handle_pi = handle_comment
    unknown_decl = handle_comment

    def close(self):
        super().close()
        if self.table is not None:
            raise DumpError("unclosed rendered table")

    def revision(self, title, url):
        if self.canonical != [url] or len(self.configs) != 1:
            raise DumpError("missing, ambiguous or mismatched rendered page identity")
        config, = self.configs
        revision = config.get("wgRevisionId")
        if (
            config.get("wgTitle") != title
            or config.get("wgPageName") != title
            or type(config.get("wgNamespaceNumber")) is not int
            or config["wgNamespaceNumber"] != 0
            or config.get("wgIsRedirect") is not False
            or type(revision) is not int
            or revision < 1
        ):
            raise DumpError("rendered metadata lacks the exact title and a direct revision")
        return revision


def rendered_cells(tables, title, kind):
    prefix, labels = RENDERED_LAYOUTS[kind]
    matches = [
        table for table in tables if table.candidate or (
            table.rows and table.rows[0] and table.rows[0][0].startswith(prefix)
        )
    ]
    if len(matches) != 1:
        raise DumpError("expected one rendered inflection table")
    table, = matches
    rows = table.rows
    if (
        table.invalid
        or len(rows) != len(labels) + 2
        or len(rows[0]) != 1
        or [part.strip() for part in rows[0][0].split("\n")] != [prefix, title]
        or table.spans != [["3"]] + [["1", "1", "1"]] * (len(labels) + 1)
        or any(len(row) != 3 for row in rows[1:])
        or rows[1][1:] != ["Singular", "Plural"]
        or tuple(row[0] for row in rows[2:]) != labels
    ):
        raise DumpError("unsupported rendered inflection table layout or markup")
    forms = set()
    invariable_cells = set()
    for row, singular, plural in rows[2:]:
        for column, value in (("Singular", singular), ("Plural", plural)):
            if value == "invariabil":
                invariable_cells.add((row, column))
                continue
            if value in {"", "'", "-"}:
                continue
            for token in re.split(r"[,/]", value):
                form = token.strip()
                if not FORM.fullmatch(form):
                    raise DumpError(f"nonliteral rendered cell {row} {column}")
                forms.add((row, column, form))
    return forms, invariable_cells


def bound_json(path, expected):
    raw = read_small(path, MAX_MANIFEST)
    if hashlib.sha256(raw).hexdigest() != expected:
        raise DumpError(f"unexpected manifest SHA-256 for {path.name}")
    return json.loads(raw, object_pairs_hook=unique_keys)


def load_samples(sample_path, baseline_path):
    sample = bound_json(sample_path, SAMPLE_SHA256)
    if baseline_path is None:
        rows = [
            (row["title"], row["dump_revision"], CATEGORY_KIND[row["category"]])
            for row in sample["pages"]
        ]
        expected_count = 10
        baseline_sha256 = None
    else:
        baseline_sha256 = sample["cached_comparison_sha256"]
        baseline = bound_json(baseline_path, baseline_sha256)
        rows = [
            (row["title"], row["dump_revision"], "noun") for row in baseline["cached_comparison"]
        ]
        expected_count = 20
    validate_samples(rows, expected_count)
    return sample["archive_date"], sample["archive_sha256"], rows, baseline_sha256


def validate_samples(rows, count):
    titles = {title for title, _, _ in rows}
    revisions = {revision for _, revision, _ in rows}
    if not 0 < len(rows) == len(titles) == len(revisions) == count:
        raise DumpError("expected distinct titles and distinct revision IDs for the entire sample")


def compare(cache, day, archive_sha256, samples, *, cached_baseline_sha256=None):
    fresh = cached_baseline_sha256 is None
    titles = [title for title, _, _ in samples]
    validate_samples(samples, len(samples))
    dump = extract(cache, day, titles, expected_archive_sha256=archive_sha256)
    pages = {page["title"]: page for page in dump.pop("pages")}
    result = {
        "comparison": "additional-live-sample" if fresh else "previously-cached-baseline",
        "sample_sha256": SAMPLE_SHA256,
        "parser_sha256": hashlib.sha256(read_small(Path(__file__).with_name("wiktionary_dump.py"), MAX_CODE)).hexdigest(),
        "comparator_sha256": hashlib.sha256(read_small(Path(__file__), MAX_CODE)).hexdigest(),
        "archive": dump,
        "pages": [],
    }
    if cached_baseline_sha256 is not None:
        result["cached_baseline_sha256"] = cached_baseline_sha256
    for title, revision, kind in samples:
        row = {"title": title, "kind": kind, "expected_revision": revision, "equal": False}
        result["pages"].append(row)
        try:
            if title not in pages:
                raise DumpError("missing exact dump title")
            page = pages[title]
            row["dump_revision"] = page["revision_id"]
            row["dump_text_sha256"] = page["text_sha256"]
            if page["revision_id"] != revision:
                raise DumpError("dump revision differs from the exact sample")
            url = WIKI + quote(title, safe="")
            receipt, raw_receipt = receipt_for(cache, url, MAX_HTML)
            row["cached_receipt_sha256"] = hashlib.sha256(raw_receipt).hexdigest()
            if fresh and receipt["first_fetcher"] != FRESH_FETCHER:
                raise DumpError("page lacks the additional live sample fetch provenance")
            if "dump_checksum" in receipt or "dump_manifest_recovered_outcome_sha256" in receipt:
                raise DumpError("unexpected dump fields on the rendered page receipt")
            headers = receipt.get("headers")
            if not isinstance(headers, dict) or headers.get("content-type", "").lower() != "text/html; charset=utf-8":
                raise DumpError("expected a UTF-8 HTML source receipt")
            body = read_small(cache / (receipt["sha256"] + ".body"), MAX_HTML)
            if len(body) != receipt["bytes"] or hashlib.sha256(body).hexdigest() != receipt["sha256"]:
                raise DumpError("cached HTML differs from its receipt")
            row["cached_body_sha256"] = receipt["sha256"]
            if b"\0" in body:
                raise DumpError("NUL is forbidden in rendered HTML")
            html = PageHTML()
            html.feed(body.decode("utf-8"))
            html.close()
            row["cached_revision"] = html.revision(title, url)
            if row["cached_revision"] != revision:
                raise DumpError("rendered revision differs from the exact sample")
            expected, expected_markers = rendered_cells(html.tables, title, kind)
            table = parse_literal_table(title, page["wikitext"], kind)
            actual = set(table["forms"])
            actual_markers = set(table["invariable_cells"])
            row.update(
                rendered_pair_count=len(expected),
                parsed_pair_count=len(actual),
                rendered_invariable_cells=sorted(expected_markers),
                parsed_invariable_cells=sorted(actual_markers),
                equal=expected == actual and expected_markers == actual_markers,
            )
            if not row["equal"]:
                row["rendered_only"] = sorted(expected - actual)
                row["parsed_only"] = sorted(actual - expected)
        except FileNotFoundError:
            row["error"] = "missing canonical cached receipt or HTML body"
        except (AttributeError, TypeError, ValueError, OSError, RecursionError) as exc:
            row["error"] = str(exc)
    result["equal"] = len(result["pages"]) == len(samples) and all(row["equal"] for row in result["pages"])
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cache", type=Path)
    cli.add_argument("--sample", type=Path, default=Path(__file__).with_name("official-sample.private.json"))
    cli.add_argument("--cached-baseline", type=Path, help="compare the pinned historical 20 cached titles")
    args = cli.parse_args()
    try:
        day, archive_sha256, samples, baseline_sha256 = load_samples(args.sample, args.cached_baseline)
        result = compare(args.cache, day, archive_sha256, samples, cached_baseline_sha256=baseline_sha256)
    except (DumpError, OSError, UnicodeError, expat.ExpatError, RecursionError) as exc:
        print(f"check_cached_nouns: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
