#!/usr/bin/env python3
"""Private ADR-0231 draft. Extract raw revisions and inspect literal inflection tables."""

import argparse
import bz2
import codecs
from contextlib import contextmanager
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from xml.parsers import expat

CHUNK = 64 * 1024
MAX_ARCHIVE = 256 * 1024 * 1024
MAX_XML = 2 * 1024 * 1024 * 1024
MAX_BZIP_STREAMS = 16_384
MAX_XML_TOKEN = 1024 * 1024
MAX_TEXT = 2 * 1024 * 1024
MAX_RESULTS = 16 * 1024 * 1024
MAX_TITLES = 64
MAX_RECEIPT = 512 * 1024
MAX_HOST_STATE = 256 * 1024
MAX_MANIFEST = 1024 * 1024
MAX_DIAGNOSTIC = 32 * 1024
DUPLICATE_MANIFEST_FAILURE = {
    "code": "dump_checksum_invalid",
    "message": "published SHA-1 manifest repeats a filename",
}
SHA256 = re.compile(r"[a-f0-9]{64}")
IDENTIFIER = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}")
MANIFEST_ENTRY = re.compile(rb"([0-9a-fA-F]{40})[ \t]+\*?([A-Za-z0-9][A-Za-z0-9._-]*)")
DECIMAL = re.compile(r"0|[1-9][0-9]{0,19}")
XMLNS = "http://www.mediawiki.org/xml/export-"
XML_NAMESPACES = {f"{XMLNS}{version}/" for version in ("0.10", "0.11")}


class DumpError(ValueError):
    """Invalid cache material, archive structure or requested evidence."""


class UnsupportedTable(DumpError):
    """A raw revision cannot be represented by the supported noun syntax."""


@contextmanager
def open_regular(path, maximum):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum:
        raise DumpError(f"invalid size or file type for {path.name}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(before, opened) or before.st_size != opened.st_size:
            raise DumpError(f"{path.name} changed while opening")
        yield stream, opened.st_size


def read_small(path, maximum):
    with open_regular(path, maximum) as (stream, size):
        data = stream.read(size + 1)
        if len(data) != size:
            raise DumpError(f"{path.name} changed while reading")
    return data


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DumpError(f"receipt repeats key {key!r}")
        result[key] = value
    return result


def receipt_for(cache, url, maximum, *, recovered=False):
    key = hashlib.sha256(url.encode("ascii")).hexdigest()
    raw = read_small(cache / (key + ".receipt.json"), MAX_RECEIPT)
    receipt = json.loads(raw, object_pairs_hook=unique_keys)
    if not isinstance(receipt, dict):
        raise DumpError("expected a receipt object")
    fetcher = receipt.get("first_fetcher")
    digest = receipt.get("sha256")
    size = receipt.get("bytes")
    if (
        receipt.get("url") != url
        or type(receipt.get("status")) is not int
        or receipt["status"] != 200
        or receipt.get("origin") != "v5"
        or receipt.get("first_fetch_origin") != "v5"
        or receipt.get("fetched_by_role") != "script"
        or receipt.get("attempt_role") != "script"
        or not isinstance(fetcher, str)
        or not IDENTIFIER.fullmatch(fetcher)
        or receipt.get("attempt_fetcher") != fetcher
        or receipt.get("body_problem")
        or type(size) is not int
        or not 0 < size <= maximum
        or not isinstance(digest, str)
        or not SHA256.fullmatch(digest)
    ):
        raise DumpError("receipt does not describe a complete script-fetched dated file")
    if recovered:
        if receipt.get("dump_failure") != DUPLICATE_MANIFEST_FAILURE or "dump_checksum" in receipt:
            raise DumpError("manifest receipt does not describe the original duplicate-filename refusal")
    elif "dump_failure" in receipt:
        raise DumpError("dated file receipt records a failure")
    return receipt, raw


def recovered_manifest(cache, url, marker):
    if not isinstance(marker, str) or not SHA256.fullmatch(marker):
        raise DumpError("invalid manifest recovery marker")
    manifest, raw = receipt_for(cache, url, MAX_DIAGNOSTIC, recovered=True)
    url_key = hashlib.sha256(url.encode("ascii")).hexdigest()
    state_raw = read_small(cache / "dumps.wikimedia.org.v5-state.json", MAX_HOST_STATE)
    state = json.loads(state_raw, object_pairs_hook=unique_keys)
    attempts = state.get("dump_attempts") if isinstance(state, dict) else None
    attempt = attempts.get(url_key) if isinstance(attempts, dict) else None
    if (
        not raw.endswith(b"\n")
        or hashlib.sha256(raw[:-1]).hexdigest() != marker
        or not isinstance(attempt, dict)
        or attempt.get("outcome_sha256") != marker
    ):
        raise DumpError("recovered manifest receipt disagrees with the shared attempt outcome")
    return manifest


def published_checksum(body, name):
    requested = name.encode("ascii")
    published = None
    for line in body.rstrip(b"\r\n").split(b"\n"):
        match = MANIFEST_ENTRY.fullmatch(line.removesuffix(b"\r"))
        if not match:
            raise DumpError("malformed checksum manifest")
        digest, entry = match.groups()
        if entry != requested:
            continue
        if published is not None:
            raise DumpError("checksum manifest repeats the requested archive filename")
        published = digest.decode("ascii").lower()
    if published is None:
        raise DumpError("checksum manifest lacks the requested archive filename")
    return published


def archive_receipt(cache, day):
    if not re.fullmatch(r"[0-9]{8}", day):
        raise DumpError("dump date must be YYYYMMDD")
    try:
        parsed_date = date(int(day[:4]), int(day[4:6]), int(day[6:]))
    except ValueError as exc:
        raise DumpError("invalid dump date") from exc
    if parsed_date.year < 2001:
        raise DumpError("invalid dump date")
    directory = f"https://dumps.wikimedia.org/rowiktionary/{day}/rowiktionary-{day}-"
    name = f"rowiktionary-{day}-pages-articles.xml.bz2"
    archive, raw = receipt_for(cache, directory + "pages-articles.xml.bz2", MAX_ARCHIVE)
    checksum = archive.get("dump_checksum")
    if not isinstance(checksum, dict):
        raise DumpError("archive receipt lacks a checksum binding")
    manifest_url = directory + "sha1sums.txt"
    expected = {}
    if "recovered_outcome_sha256" in checksum:
        marker = checksum["recovered_outcome_sha256"]
        manifest = recovered_manifest(cache, manifest_url, marker)
        suffix, maximum = ".diagnostic", MAX_DIAGNOSTIC
        expected["recovered_outcome_sha256"] = marker
    else:
        manifest, _ = receipt_for(cache, manifest_url, MAX_MANIFEST)
        if "dump_checksum" in manifest:
            raise DumpError("ordinary manifest receipt has an unexpected checksum binding")
        suffix, maximum = ".body", MAX_MANIFEST
    digest = manifest["sha256"]
    body = read_small(cache / (digest + suffix), maximum)
    if len(body) != manifest["bytes"] or hashlib.sha256(body).hexdigest() != digest:
        raise DumpError("checksum manifest does not match its receipt")

    expected.update(url=manifest_url, sha256=digest, sha1=published_checksum(body, name))
    if checksum != expected:
        raise DumpError("archive receipt disagrees with the published checksum")
    return archive, hashlib.sha256(raw).hexdigest()


class RevisionScan:
    """Expat callbacks keep only metadata and requested revision text in memory."""

    def __init__(self, titles):
        self.titles = set(titles)
        self.results = {}
        self.results_bytes = 0
        self.path = []
        self.namespace = None
        self.dbname = None
        self.page = None
        self.capture = None
        self.parts = []
        self.size = 0
        self.capture_limit = 0

    @staticmethod
    def reject_markup(*_):
        raise DumpError("XML declarations with entities, DTDs or alternate encodings are unsupported")

    def declaration(self, _version, encoding, _standalone):
        if encoding is not None and encoding.upper() != "UTF-8":
            self.reject_markup()

    def start(self, qualified_name, attributes):
        if self.capture is not None:
            raise DumpError("unexpected child element inside a scalar XML field")
        namespace, _, name = qualified_name.rpartition(" ")
        if not self.path:
            if namespace not in XML_NAMESPACES or name != "mediawiki":
                raise DumpError("expected a MediaWiki export root")
            self.namespace = namespace
        if namespace != self.namespace or len(self.path) >= 32:
            raise DumpError("unexpected XML namespace or nesting depth")
        self.path.append(name)
        location = self.path[1:]
        if location == ["siteinfo", "dbname"]:
            self.begin_capture("dbname", 64)
        if location == ["page"]:
            if self.dbname != "rowiktionary":
                raise DumpError("expected rowiktionary site metadata before pages")
            self.page = {}
        if self.page is None:
            return
        if location in (["page", "title"], ["page", "ns"]):
            self.begin_capture(name, 1024)
        if location == ["page", "redirect"]:
            self.page["redirect"] = True
        if location == ["page", "revision"]:
            if "title" not in self.page or "ns" not in self.page:
                raise DumpError("page revision precedes title or namespace")
            if self.selected:
                if self.page.get("revision"):
                    raise DumpError(f"multiple revisions for {self.page['title']!r}")
                self.page["revision"] = True
        if self.selected and location[:2] == ["page", "revision"] and len(location) == 3:
            if name in {"id", "model", "format"}:
                self.begin_capture(name, 64)
            if name == "text":
                declared = attributes.get("bytes", "")
                if "deleted" in attributes or "suppressed" in attributes or not DECIMAL.fullmatch(declared):
                    raise DumpError(f"unavailable or unbounded text for {self.page['title']!r}")
                self.page["declared_text_bytes"] = int(declared)
                self.begin_capture(name, MAX_TEXT)

    @property
    def selected(self):
        return self.page.get("ns") == "0" and self.page.get("title") in self.titles

    def begin_capture(self, name, limit):
        self.capture = name
        self.capture_limit = limit
        self.parts = []
        self.size = 0

    def characters(self, text):
        if self.capture is not None:
            self.size += len(text.encode("utf-8"))
            if self.size > self.capture_limit:
                raise DumpError(f"XML field {self.capture!r} exceeds its byte limit")
            self.parts.append(text)

    def end(self, _name):
        if self.capture is not None:
            name = self.capture
            self.capture = None
            value = "".join(self.parts)
            self.parts = []
            if name == "dbname":
                if self.dbname is not None:
                    raise DumpError("duplicate MediaWiki database name")
                self.dbname = value
            else:
                if name in self.page:
                    raise DumpError(f"duplicate XML field {name!r}")
                self.page[name] = value
        if self.path == ["mediawiki", "page"]:
            self.finish_page()
            self.page = None
        self.path.pop()

    def finish_page(self):
        title = self.page.get("title")
        namespace = self.page.get("ns")
        if not title or namespace is None or not DECIMAL.fullmatch(namespace):
            raise DumpError("page lacks a valid title or namespace")
        if not self.selected:
            return
        if title in self.results or self.page.get("redirect"):
            raise DumpError(f"duplicate page or redirect for {title!r}")
        revision = self.page.get("id", "")
        text = self.page.get("text")
        if (
            not self.page.get("revision")
            or not DECIMAL.fullmatch(revision)
            or revision == "0"
            or self.page.get("model") != "wikitext"
            or self.page.get("format") != "text/x-wiki"
            or text is None
        ):
            raise DumpError(f"{title!r} lacks a direct wikitext revision")
        raw = text.encode("utf-8")
        if len(raw) != self.page["declared_text_bytes"]:
            raise DumpError(f"revision text byte count differs for {title!r}")
        self.results_bytes += len(raw)
        if self.results_bytes > MAX_RESULTS:
            raise DumpError("requested revisions exceed the aggregate byte limit")
        self.results[title] = {
            "title": title,
            "revision_id": int(revision),
            "text_sha256": hashlib.sha256(raw).hexdigest(),
            "text_bytes": len(raw),
            "wikitext": text,
        }


def scan_archive(path, receipt, titles):
    scan = RevisionScan(titles)
    parser = expat.ParserCreate(encoding="UTF-8", namespace_separator=" ")
    utf8 = codecs.getincrementaldecoder("utf-8")()
    parser.XmlDeclHandler = scan.declaration
    parser.StartDoctypeDeclHandler = scan.reject_markup
    parser.EntityDeclHandler = scan.reject_markup
    parser.ExternalEntityRefHandler = scan.reject_markup
    parser.StartElementHandler = scan.start
    parser.EndElementHandler = scan.end
    parser.CharacterDataHandler = scan.characters
    sha256 = hashlib.sha256()
    sha1 = hashlib.sha1(usedforsecurity=False)
    compressed_size = 0
    xml_size = 0
    decoder = None
    streams = 0
    with open_regular(path, MAX_ARCHIVE) as (stream, size):
        if size != receipt["bytes"]:
            raise DumpError("archive byte count differs from the receipt")
        while data := stream.read(CHUNK):
            compressed_size += len(data)
            if compressed_size > size:
                raise DumpError("archive grew while reading")
            sha256.update(data)
            sha1.update(data)
            while data or (decoder is not None and not decoder.eof and not decoder.needs_input):
                if decoder is None or decoder.eof:
                    streams += 1
                    if streams > MAX_BZIP_STREAMS:
                        raise DumpError("archive exceeds the bzip2 stream limit")
                    decoder = bz2.BZ2Decompressor()
                chunk = decoder.decompress(data, CHUNK)
                xml_size += len(chunk)
                if xml_size > MAX_XML:
                    raise DumpError("archive exceeds the decompressed byte limit")
                if b"\x00" in chunk:
                    raise DumpError("NUL is forbidden in UTF-8 XML")
                if b"\r" in chunk:
                    raise DumpError("literal CR prevents an exact XML text byte binding")
                try:
                    utf8.decode(chunk, final=False)
                except UnicodeDecodeError as exc:
                    raise DumpError("XML must use valid UTF-8 bytes") from exc
                parser.Parse(chunk, False)
                if xml_size - parser.CurrentByteIndex > MAX_XML_TOKEN:
                    raise DumpError("XML contains an oversized unfinished token")
                data = decoder.unused_data if decoder.eof else b""
    if decoder is None or not decoder.eof:
        raise DumpError("truncated bzip2 stream")
    if (
        compressed_size != size
        or sha256.hexdigest() != receipt["sha256"]
        or sha1.hexdigest() != receipt["dump_checksum"]["sha1"]
    ):
        raise DumpError("archive does not match the pinned SHA-256 and published SHA-1")
    try:
        utf8.decode(b"", final=True)
    except UnicodeDecodeError as exc:
        raise DumpError("XML must use valid UTF-8 bytes") from exc
    parser.Parse(b"", True)
    if scan.dbname != "rowiktionary":
        raise DumpError("missing rowiktionary site metadata")
    return scan.results


def extract(cache, day, titles, *, expected_archive_sha256=None):
    if not 0 < len(titles) <= MAX_TITLES or len(set(titles)) != len(titles):
        raise DumpError(f"request 1 to {MAX_TITLES} distinct exact titles")
    if any(not title or len(title.encode("utf-8")) > 1024 or any(ord(c) < 32 for c in title) for title in titles):
        raise DumpError("invalid requested title")
    receipt, receipt_sha = archive_receipt(cache, day)
    digest = receipt["sha256"]
    if expected_archive_sha256 is not None and digest != expected_archive_sha256:
        raise DumpError("archive receipt does not match the requested SHA-256")
    pages = scan_archive(cache / (digest + ".dump"), receipt, titles)
    return {
        "archive_url": receipt["url"],
        "archive_sha256": digest,
        "archive_receipt_sha256": receipt_sha,
        "pages": [pages[title] for title in titles if title in pages],
        "missing_titles": [title for title in titles if title not in pages],
    }


# Visible labels and adjective cell mappings from Format:substantiv-ron
# revision 1004026 and Format:adjectiv-ron revision 1153974.
# Format:inv revision 23577 renders "invariabil", which is never a form.
NOUN_CELLS = {
    "nom-sg": ("Nominativ-Acuzativ", "Singular"),
    "nom-pl": ("Nominativ-Acuzativ", "Plural"),
    "art-sg": ("Articulat", "Singular"),
    "art-pl": ("Articulat", "Plural"),
    "dat-sg": ("Genitiv-Dativ", "Singular"),
    "dat-pl": ("Genitiv-Dativ", "Plural"),
    "voc-sg": ("Vocativ", "Singular"),
    "voc-pl": ("Vocativ", "Plural"),
}
ADJECTIVE_CELLS = {
    "m-sg": (("Masculin", "Singular"), ("Neutru", "Singular")),
    "m-pl": (("Masculin", "Plural"),),
    "f-sg": (("Feminin", "Singular"),),
    "f-pl": (("Feminin", "Plural"), ("Neutru", "Plural")),
}
TABLE_NAMES = {"noun": "substantiv", "adjective": "adjectiv"}
ROMANIAN = re.compile(r"==[ \t]*\{\{limba[ \t]*\|[ \t]*ron[ \t]*\}\}[ \t]*==[ \t]*$")
TABLE_FIELD = re.compile(r"\|[ \t]*([a-z-]+)[ \t]*=([^\n]*)")
GENDER = re.compile(r"\{\{[mfn]\}\}(?: și \{\{[mfn]\}\})?")
FORM = re.compile(r"[A-Za-zĂÂÎȘȚăâîșț]+")
TOKEN = re.compile(
    r"\n|<!--|\{\{\{|\{\{|\}\}|\[\[|\]\]|\{\||\|\}|"
    r"</?[a-z][a-z0-9-]*(?:\s(?:[^\x22\x27<>]|\x22[^\x22]*\x22|\x27[^\x27]*\x27)*)?/?>|</?[a-z!]",
    re.IGNORECASE,
)
OPAQUE_TAGS = frozenset(
    "nowiki pre source syntaxhighlight ref references gallery math code poem score timeline "
    "templatedata".split()
)
CLOSERS = {"{{": "}}", "[[": "]]", "{|": "|}"}
TAG = re.compile(r"<(/?)([a-z][a-z0-9-]*)")
VOID_TAGS = frozenset("br hr wbr".split())
OPAQUE_CLOSE = {name: re.compile(r"</" + name + r"[ \t\n]*>", re.IGNORECASE)
                for name in OPAQUE_TAGS}



def top_level_lines(text):
    """Locate standalone constructs without expanding other wikitext."""
    starts = {0}
    stack = []
    tag = None
    tag_depth = 0
    comments = []
    unsupported = len(text)
    cursor = 0
    while match := TOKEN.search(text, cursor):
        if tag in OPAQUE_TAGS:
            # Inside an opaque extension tag, apparent comments and quoted HTML
            # attributes are literal text. Find the real closing delimiter first.
            close = OPAQUE_CLOSE[tag].search(text, cursor)
            if close is None:
                raise UnsupportedTable("unclosed opaque wikitext tag")
            cursor = close.end()
            tag = None
            tag_depth = 0
            continue
        raw_token = match[0]
        token = raw_token.lower()
        cursor = match.end()
        if tag is not None:
            element = TAG.match(token)
            if element and element[2] == tag:
                if re.fullmatch(r"</[a-z][a-z0-9-]*[ \t\n]*>", token):
                    tag_depth -= 1
                    if not tag_depth:
                        tag = None
                elif tag not in OPAQUE_TAGS and not element[1] and token.endswith(">") and not token.endswith("/>"):
                    tag_depth += 1
            continue
        if token != "<!--" and token.startswith("<") and "<!--" in raw_token:
            raise UnsupportedTable("ambiguous comment inside a wikitext tag")
        if token == "<!--":
            end = text.find("-->", cursor)
            if end == -1:
                raise UnsupportedTable("unclosed wikitext comment")
            cursor = end + 3
            comments.append((match.start(), cursor))
            if "\n" in text[match.start():cursor]:
                unsupported = min(unsupported, match.start())
            continue
        if token == "\n":
            if not stack:
                starts.add(match.end())
        elif token.startswith("<"):
            element = TAG.match(token)
            if element is None or not token.endswith(">"):
                raise UnsupportedTable("malformed wikitext tag")
            closing, name = element.groups()
            if name not in OPAQUE_TAGS | VOID_TAGS or (closing and name not in VOID_TAGS):
                unsupported = min(unsupported, match.start())
            if not closing and not token.endswith("/>") and name not in VOID_TAGS:
                tag = name
                tag_depth = 1
        elif token == "{{{":
            raise UnsupportedTable("parameter expansion occurs in the raw page")
        elif token in CLOSERS:
            stack.append(CLOSERS[token])
            if len(stack) > 32:
                raise UnsupportedTable("wikitext nesting exceeds the parser limit")
        elif token in CLOSERS.values():
            if not stack or stack.pop() != token:
                raise UnsupportedTable("ambiguous wikitext nesting")
    if stack or tag is not None:
        raise UnsupportedTable("unclosed wikitext construct")
    return starts, comments, unsupported


def section_headings(text, starts, comments):
    """Find level-one and level-two headings with same-line comments removed."""
    comments = iter(comments)
    comment = next(comments, None)
    offset = 0
    for line in text.split("\n"):
        end = offset + len(line)
        parts = []
        cursor = offset
        while comment is not None and comment[0] < end:
            parts.append(text[cursor:comment[0]])
            cursor = comment[1]
            comment = next(comments, None)
        if offset in starts and cursor <= end:
            clean = ("".join(parts) + text[cursor:end]).rstrip(" \t")
            leading = len(clean) - len(clean.lstrip("="))
            trailing = len(clean) - len(clean.rstrip("="))
            if 0 < min(leading, trailing) <= 2 and leading + trailing < len(clean):
                yield offset, end + 1, ROMANIAN.fullmatch(clean) is not None
        offset = end + 1


def literal_parameters(wikitext, table_name):
    """Find one supported invocation without expanding the rest of the page."""
    if len(wikitext.encode("utf-8")) > MAX_TEXT:
        raise UnsupportedTable("raw page exceeds the parser limit")
    if "\r" in wikitext or "\0" in wikitext:
        raise UnsupportedTable("unsupported control characters in raw page")
    starts, comments, unsupported = top_level_lines(wikitext)
    sections = []
    romanian = None
    for heading_start, next_line, is_romanian in section_headings(wikitext, starts, comments):
        if romanian is not None:
            sections.append((romanian, heading_start))
        romanian = next_line if is_romanian else None
    if romanian is not None:
        sections.append((romanian, len(wikitext)))
    if len(sections) != 1:
        raise UnsupportedTable("expected one standalone Romanian language heading")
    start, end = sections[0]
    section = wikitext[start:end]
    name = re.compile(r"\{\{[ \t]*(?:Format:[ \t]*)?" + table_name + r"[-_ ]ron\b", re.IGNORECASE)
    candidates = list(name.finditer(section))
    if len(candidates) != 1:
        raise UnsupportedTable(f"expected exactly one {table_name} invocation in the Romanian section")
    match = candidates[0]
    line_start = start + match.start()
    if unsupported < line_start:
        raise UnsupportedTable("unsupported markup before the table invocation")
    if line_start not in starts:
        raise UnsupportedTable("table invocation is not standalone")
    preceding = section[:match.start()].rstrip(" \t\n")
    marker = preceding.rsplit("\n", 1)[-1]
    marker_start = start + len(preceding) - len(marker)
    heading = r"\{\{-" + table_name + r"-[ \t]*\|[ \t]*ron[ \t]*\}\}[ \t]*"
    if marker_start not in starts or not re.fullmatch(heading, marker):
        raise UnsupportedTable("table invocation lacks a standalone Romanian part-of-speech heading")

    lines = iter(section[match.start():].split("\n"))
    opening = next(lines)
    if opening.rstrip(" \t") != "{{" + table_name + "-ron":
        raise UnsupportedTable("unsupported table invocation opening")
    fields = {}
    line_start += len(opening) + 1
    for line in lines:
        if line.rstrip(" \t") == "}}":
            if unsupported < line_start + len(line):
                raise UnsupportedTable("unsupported markup within the table invocation")
            return fields
        field = TABLE_FIELD.fullmatch(line)
        if field is None or field[1] in fields:
            raise UnsupportedTable("unsupported or duplicate table parameter")
        fields[field[1]] = field[2].strip(" \t")
        line_start += len(line) + 1
    raise UnsupportedTable("unclosed table invocation")


def noun_table(title, fields):
    if fields.keys() != NOUN_CELLS.keys() | {"gen"} or not GENDER.fullmatch(fields["gen"]):
        raise UnsupportedTable("unrecognized noun parameter set or gender")
    if fields["nom-sg"] == "{{inv}}":
        if fields["nom-pl"] != title or any(fields[key] != "{{inv}}" for key in NOUN_CELLS if key.endswith("-sg")):
            raise UnsupportedTable("unsupported plural-only noun pattern")
    elif fields["nom-sg"] != title:
        raise UnsupportedTable("singular nominative differs from the exact page title")

    two_plurals = "/" in fields["nom-pl"]
    forms = []
    invariable_cells = []
    for key, (row, column) in NOUN_CELLS.items():
        value = fields[key]
        if value == "{{inv}}":
            invariable_cells.append((row, column))
            continue
        if value in {"", "-"}:
            continue
        if "/" in value:
            if not two_plurals or column != "Plural" or value.count("/") != 1:
                raise UnsupportedTable(f"unsupported slash alternatives in noun cell {key}")
            parts = value.split("/")
        else:
            parts = value.split(",")
        tokens = [part.strip(" \t") for part in parts]
        if any(not FORM.fullmatch(token) for token in tokens) or len(set(tokens)) != len(tokens):
            raise UnsupportedTable(f"unsupported or repeated form in noun cell {key}")
        forms.extend((row, column, token) for token in tokens)
    return {"forms": forms, "invariable_cells": invariable_cells}


def adjective_table(title, fields):
    if fields.keys() != ADJECTIVE_CELLS.keys() or fields["m-sg"] != title:
        raise UnsupportedTable("unrecognized adjective parameters or masculine singular")
    forms = []
    for key, labels in ADJECTIVE_CELLS.items():
        token = fields[key]
        if key != "m-sg" and token.startswith("[[") and token.endswith("]]"):
            token = token[2:-2]
        if not FORM.fullmatch(token):
            raise UnsupportedTable(f"unsupported form in adjective cell {key}")
        forms.extend((row, column, token) for row, column in labels)
    return {"forms": forms, "invariable_cells": []}


def parse_literal_table(title, wikitext, kind):
    """Return visible form triples and exact invariable cell labels."""
    table_name = TABLE_NAMES[kind]
    fields = literal_parameters(wikitext, table_name)
    if kind == "noun":
        return noun_table(title, fields)
    return adjective_table(title, fields)


def parse_literal_noun_table(title, wikitext):
    """Return the literal noun form triples."""
    return parse_literal_table(title, wikitext, "noun")["forms"]

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--cache", required=True, type=Path)
    cli.add_argument("--date", required=True, dest="day")
    cli.add_argument("--literal-table", choices=TABLE_NAMES, help="inspect an ungated table subset")
    cli.add_argument("titles", nargs="+")
    args = cli.parse_args()
    try:
        result = extract(args.cache, args.day, args.titles)
        if args.literal_table:
            result["parser_status"] = "ungated-literal-table-subset"
            for page in result["pages"]:
                try:
                    page["table"] = parse_literal_table(page["title"], page["wikitext"], args.literal_table)
                except UnsupportedTable as exc:
                    page["unsupported_table"] = str(exc)
        # Emit JSON with ASCII escaping so raw wikitext is never interpreted as
        # terminal controls, regardless of the shell's configured encoding.
        json.dump(result, sys.stdout, indent=2)
        print()
    except (DumpError, OSError, UnicodeError, expat.ExpatError, RecursionError, json.JSONDecodeError) as exc:
        print(f"wiktionary_dump: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
