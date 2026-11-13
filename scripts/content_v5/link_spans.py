#!/usr/bin/env python3
"""Check literal V5 link evidence against exact cached Romanian Wikimedia HTML."""

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "landing"))
from content_registry import FIRST_FETCHER, live_source_receipt, receipt_hash  # noqa: E402
from support import digest, read_artifact, read_json  # noqa: E402

SCHEMA = "cat-v5-link-spans-1"
ARTICLE_HOSTS = {"ro.wikipedia.org", "ro.wiktionary.org"}
FIRST_ROLES = {"script", "factual", "quality", "critic"}
ATTEMPT_ROLES = FIRST_ROLES | {"author", "policy", "legacy"}
MAX_BATCH = 1024 * 1024
MAX_LINKS = 160
MAX_QUOTE = 280
MAX_RECEIPT = 512 * 1024
MAX_BODY = 16 * 1024 * 1024
MAX_DEPTH = 128
MAX_TAGS = 250_000
MAX_BLOCKS = 16_384
MAX_TITLE = 1024
EPOCH_LIMIT = 253402300800
LINK_KEYS = ("src_id", "dst_id", "relation", "bidirectional")
RELATION = re.compile(r"[a-z][a-z0-9_]{0,63}")
HTML_TYPE = re.compile(r'text/html(?:\s*;\s*charset\s*=\s*(?:utf-8|"utf-8"))?', re.IGNORECASE)
NO_AI = re.compile(r"(?:^|[\s,:;])(?:noai|noimageai)(?:$|[\s,;])", re.IGNORECASE)
# Go's source-client/policy.go tests these title patterns against the raw body.
# RE2's word boundary and whitespace classes are ASCII, and its whitespace class omits VT.
RAW_TITLE_OPEN = re.compile(r"<title(?a:\b)", re.IGNORECASE)
RE2_SPACE = re.compile(r"[\t\n\f\r ]*")
CRAWLER_TITLE = re.compile(
    r"(?:just a moment|access denied|request blocked|automated access denied|"
    r"crawler access denied)(?:\.{3}|!|[\t\n\f\r <])",
    re.IGNORECASE,
)
ENGLISH_TERMS = re.compile(r"terms of (?:use|service)[\t\n\f\r <]", re.IGNORECASE)
ROMANIAN_TERMS = re.compile(
    r"termeni(?:i)? (?:de utilizare|și condiții)[\t\n\f\r <]", re.IGNORECASE
)
POLICY_PREFIX = re.compile(r"policy[\t\n\f\r ]*:", re.IGNORECASE)
LOCAL_TERMS_PREFIX = re.compile(r"[^<>:\n]+:")
# Also recognize a refused document title after decoding HTML character references.
REFUSED_TITLE = re.compile(
    r"(?:(?:just a moment|access denied|request blocked|automated access denied|"
    r"crawler access denied)"
    r"(?:\.{3}|!|\s|$)|(?:(?:policy\s*:\s*)?terms of (?:use|service)|"
    r"(?:[^<>:\n]+:\s*)?termeni(?:i)? (?:de utilizare|și condiții))(?:\s|$))",
    re.IGNORECASE,
)
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
INLINE = set(
    "a abbr b bdi bdo cite code em i kbd mark q s samp small span strong sub sup time u var".split()
)
TEXT_BLOCKS = {"p", "li", "dd", "dt", "blockquote"}
CONTAINERS = {"div", "section", "ul", "ol", "dl"}
EXCLUDED_TAGS = set(
    "aside audio button canvas details dialog footer form header iframe input menu nav noscript "
    "noembed noframes object script select style summary template textarea video "
    "xmp svg math".split()
)
EXCLUDED_CLASSES = set(
    "ambox catlinks citation cs1-hidden-error cs1-maint dablink gallery hatnote hidden metadata "
    "mw-collapsed mw-collapsible mw-empty-li "
    "mw-empty-elt mw-jump-link mw-ref mw-visually-hidden navcontent navframe navhead noprint "
    "printfooter reference references reflist rellink screen-reader-only shortdescription "
    "sistersitebox sortkey sr-only thumb toc visually-hidden".split()
)
EXCLUDED_CLASS_PREFIXES = (
    "infobox",
    "mw-editsection",
    "mw-reference",
    "navbar",
    "navbox",
    "portalbox",
    "sidebar",
    "vertical-navbox",
)
EXCLUDED_ROLES = {
    "banner",
    "complementary",
    "contentinfo",
    "doc-backlink",
    "doc-bibliography",
    "doc-endnote",
    "doc-endnotes",
    "doc-footnote",
    "doc-noteref",
    "menu",
    "menubar",
    "navigation",
    "search",
    "tablist",
}


class SpanError(ValueError):
    """Stable diagnostic code for a failed evidence check."""


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def is_id(value):
    return isinstance(value, str) and FIRST_FETCHER.fullmatch(value) is not None


def is_epoch(value):
    return type(value) in (float, int) and 0 < value < EPOCH_LIMIT


def read_batch(raw):
    if len(raw) > MAX_BATCH:
        raise SpanError("batch_limit")
    try:
        batch = read_json(raw.decode("utf-8"))
    except (ValueError, RecursionError):
        raise SpanError("batch_json") from None
    links = batch.get("links")
    if (
        batch.keys() != {"schema", "links"}
        or batch["schema"] != SCHEMA
        or not isinstance(links, list)
        or not 0 < len(links) <= MAX_LINKS
    ):
        raise SpanError("batch_schema")
    seen = set()
    for row in links:
        if not isinstance(row, dict) or row.keys() != {
            "link",
            "url",
            "receipt_sha256",
            "body_sha256",
            "quote",
        }:
            raise SpanError("link_schema")
        link = row["link"]
        if (
            not isinstance(link, dict)
            or link.keys() != set(LINK_KEYS)
            or any(not is_id(link[k]) for k in LINK_KEYS[:2])
            or link["src_id"] == link["dst_id"]
            or not isinstance(link["relation"], str)
            or not RELATION.fullmatch(link["relation"])
            or type(link["bidirectional"]) is not bool
        ):
            raise SpanError("link_identity")
        identity = tuple(link[k] for k in LINK_KEYS)
        if identity in seen:
            raise SpanError("duplicate_link")
        seen.add(identity)
        if not isinstance(row["url"], str) or not 0 < len(row["url"]) <= 4096:
            raise SpanError("link_url")
        if any(not receipt_hash(row[k]) for k in ("receipt_sha256", "body_sha256")):
            raise SpanError("link_hash")
        quote = row["quote"]
        if (
            not isinstance(quote, str)
            or not 0 < len(quote) <= MAX_QUOTE
            or not normalize(quote)
            or any(
                unicodedata.category(c) == "Cs" or (ord(c) < 32 and c not in "\t\r\n")
                for c in quote
            )
        ):
            raise SpanError("link_quote")
    return links


def verified_body(cache, url, receipt_sha, body_sha):
    try:
        name = digest(url.encode("ascii")) + ".receipt.json"
    except UnicodeEncodeError:
        raise SpanError("source_url") from None
    if not live_source_receipt(
        {"url": url, "path": name, "sha256": receipt_sha, "body_sha256": body_sha}
    ):
        raise SpanError("source_url")
    source = urlsplit(url)
    if (
        source.netloc not in ARTICLE_HOSTS
        or source.query
        or not source.path.startswith("/wiki/")
        or source.path == "/wiki/"
    ):
        raise SpanError("source_url")
    try:
        receipt_raw = read_artifact(cache, name, MAX_RECEIPT)
    except (ValueError, OSError):
        raise SpanError("receipt_unavailable") from None
    if digest(receipt_raw) != receipt_sha:
        raise SpanError("receipt_hash")
    try:
        rec = read_json(receipt_raw.decode("utf-8"))
    except (ValueError, RecursionError):
        raise SpanError("receipt_invalid") from None
    role, attempt = rec.get("fetched_by_role"), rec.get("attempt_role")
    size, fetched, received = rec.get("bytes"), rec.get("fetched_at"), rec.get("received_at")
    headers = rec.get("headers")
    if (
        rec.get("url") != url
        or rec.get("sha256") != body_sha
        or type(rec.get("status")) is not int
        or rec["status"] != 200
        or rec.get("origin") != "v5"
        or rec.get("first_fetch_origin") != "v5"
        or not isinstance(role, str)
        or role not in FIRST_ROLES
        or not isinstance(attempt, str)
        or attempt not in ATTEMPT_ROLES
        or not is_id(rec.get("first_fetcher"))
        or not is_id(rec.get("attempt_fetcher"))
        or not is_epoch(fetched)
        or not is_epoch(received)
        or received < fetched
        or type(size) is not int
        or not 0 < size <= MAX_BODY
        or rec.get("body_problem", "") != ""
        or any(
            key in rec
            for key in ("dump_checksum", "dump_failure", "dump_manifest_recovered_outcome_sha256")
        )
        or not isinstance(headers, dict)
        or any(key != key.lower() or not isinstance(value, str) for key, value in headers.items())
    ):
        raise SpanError("receipt_invalid")
    if (
        headers.get("content-signal")
        or headers.get("content-signal-present", "false") != "false"
        or NO_AI.search(headers.get("x-robots-tag", ""))
        or headers.get("location")
    ):
        raise SpanError("source_refused")
    if (
        headers.get("content-range")
        or headers.get("content-length", str(size)) != str(size)
        or headers.get("content-encoding", "").lower() not in {"", "identity"}
    ):
        raise SpanError("receipt_invalid")
    if not HTML_TYPE.fullmatch(headers.get("content-type", "").strip()):
        raise SpanError("unsupported_content_type")
    try:
        body = read_artifact(cache, f"{body_sha}.body", size)
    except (ValueError, OSError):
        raise SpanError("body_unavailable") from None
    if len(body) != size or digest(body) != body_sha:
        raise SpanError("body_integrity")
    return body


def excluded(tag, attrs, classes):
    return (
        tag in EXCLUDED_TAGS
        or bool({"hidden", "inert", "style"} & attrs.keys())
        or (attrs.get("aria-hidden") or "").strip().lower() == "true"
        or bool(EXCLUDED_ROLES.intersection((attrs.get("role") or "").lower().split()))
        or bool(EXCLUDED_CLASSES.intersection(classes))
        or any(name.startswith(EXCLUDED_CLASS_PREFIXES) for name in classes)
        or (attrs.get("typeof") or "").lower().startswith("mw:extension/ref")
        or (tag == "a" and (attrs.get("href") or "").startswith(("#cite_note", "#cite_ref")))
    )


@dataclass(frozen=True)
class Frame:
    tag: str
    stage: str
    blocked: bool
    prose: bool
    capture: bool
    joins: bool
    foreign: bool


OUTSIDE = Frame("", "", False, False, False, False, False)
ARTICLE_STAGES = {
    "html",
    "head",
    "title",
    "body",
    "main",
    "body_content",
    "content_text",
    "article",
}
STAGE_IDS = {"content": "main", "bodyContent": "body_content", "mw-content-text": "content_text"}


class ArticleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.seen = set()
        self.canonical = []
        self.title = []
        self.title_size = 0
        self.in_article = False
        self.in_body = False
        self.tags = 0
        self.parts = []
        self.blocks = []

    def stage(self, tag, attrs, classes, parent):
        node_id = attrs.get("id")
        if tag == "html" and not self.stack and attrs.get("lang") == "ro":
            return "html"
        if parent.stage == "html" and tag == "head":
            return "head"
        if parent.stage == "head" and tag == "title":
            return "title"
        if (
            parent.stage == "html"
            and tag == "body"
            and {"mediawiki", "action-view", "ns-0"} <= classes
        ):
            return "body"
        if self.in_body and tag == "main" and node_id == "content" and "mw-body" in classes:
            if all(frame.tag == "div" for frame in self.stack[2:]):
                return "main"
        if parent.stage == "main" and tag == "div" and node_id == "bodyContent":
            return "body_content"
        if parent.stage == "body_content" and tag == "div" and node_id == "mw-content-text":
            return "content_text"
        if (
            parent.stage == "content_text"
            and tag == "div"
            and "mw-parser-output" in classes
            and attrs.get("lang") == "ro"
        ):
            return "article"
        return ""

    def flush(self):
        if not self.parts:
            return
        text = normalize("".join(self.parts))
        self.parts.clear()
        if text:
            if len(self.blocks) >= MAX_BLOCKS:
                raise SpanError("html_limit")
            self.blocks.append(text)

    def start(self, tag, pairs, self_closing=False):
        self.tags += 1
        if self.tags > MAX_TAGS or len(self.stack) >= MAX_DEPTH:
            raise SpanError("html_limit")
        parent = self.stack[-1] if self.stack else OUTSIDE
        attrs = dict(pairs)
        classes = set((attrs.get("class") or "").split())
        folded_classes = {name.lower() for name in classes}
        stage = self.stage(tag, attrs, classes, parent)
        foreign = parent.foreign or tag in {"math", "svg"}
        if (
            len(attrs) != len(pairs)
            or (not self.stack and stage != "html")
            or tag in {"base", "plaintext"}
            or (self_closing and not foreign and tag not in VOID)
            or (attrs.get("id") in STAGE_IDS and stage != STAGE_IDS[attrs["id"]])
        ):
            raise SpanError("html_layout")
        blocked = parent.blocked or excluded(tag, attrs, folded_classes)
        if stage:
            if stage in self.seen or blocked:
                raise SpanError("html_layout")
            self.seen.add(stage)
        if tag == "link":
            rel = (attrs.get("rel") or "").lower().split()
            if "canonical" in rel:
                if parent.stage != "head" or blocked:
                    raise SpanError("html_canonical")
                self.canonical.append(attrs.get("href"))
            if "stylesheet" in rel and (
                parent.stage != "head" or not (attrs.get("href") or "").startswith("/w/load.php?")
            ):
                raise SpanError("html_layout")
        if tag == "style":
            types = set((attrs.get("typeof") or "").split())
            if (
                not self.in_body
                or "mw:Extension/templatestyles" not in types
                or types - {"mw:Extension/templatestyles", "mw:Transclusion"}
            ):
                raise SpanError("html_layout")
        if tag == "meta" and parent.stage == "head":
            self.check_meta(attrs)
        if stage == "body":
            self.in_body = True
        if stage == "article":
            self.in_article = True
        if self.in_article and stage != "article" and "mw-parser-output" in classes:
            blocked = True
        joins = parent.capture and not blocked and tag in INLINE
        prose = stage == "article" or (
            parent.prose and not blocked and (tag in TEXT_BLOCKS | CONTAINERS or joins)
        )
        capture = prose and (tag in TEXT_BLOCKS or joins)
        if self.in_article and not joins:
            self.flush()
        if tag not in VOID and not self_closing:
            self.stack.append(Frame(tag, stage, blocked, prose, capture, joins, foreign))

    @staticmethod
    def check_meta(attrs):
        equiv = (attrs.get("http-equiv") or "").strip().lower()
        name = (attrs.get("name") or "").strip().lower()
        content = (attrs.get("content") or "").strip()
        if (
            "charset" in attrs
            and (attrs["charset"] or "").lower() != "utf-8"
            or equiv == "content-type"
            and not HTML_TYPE.fullmatch(content)
        ):
            raise SpanError("unsupported_content_type")
        if (
            equiv in {"refresh", "content-signal"}
            or name == "content-signal"
            or (name == "robots" and NO_AI.search(content))
        ):
            raise SpanError("source_refused")

    def handle_starttag(self, tag, attrs):
        self.start(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self.start(tag, attrs, self_closing=True)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1].tag != tag:
            raise SpanError("html_layout")
        frame = self.stack.pop()
        if self.in_article and not frame.joins:
            self.flush()
        if frame.stage == "article":
            self.in_article = False
        if frame.stage == "body":
            self.in_body = False

    def handle_data(self, data):
        if not self.stack and data.strip():
            raise SpanError("html_layout")
        if self.stack and self.stack[-1].stage == "title":
            self.title_size += len(data)
            if self.title_size > MAX_TITLE:
                raise SpanError("html_limit")
            self.title.append(data)
        if self.stack and self.stack[-1].capture:
            self.parts.append(data)

    def unknown_decl(self, data):
        raise SpanError("html_layout")

    def article_blocks(self, url):
        if self.stack or self.seen != ARTICLE_STAGES:
            raise SpanError("html_layout")
        if self.canonical != [url]:
            raise SpanError("html_canonical")
        if REFUSED_TITLE.match("".join(self.title).lstrip()):
            raise SpanError("source_refused")
        return self.blocks


def refused_title_at(text, start):
    content = RE2_SPACE.match(text, start).end()
    if any(pat.match(text, content) for pat in (CRAWLER_TITLE, ENGLISH_TERMS, ROMANIAN_TERMS)):
        return True
    policy = POLICY_PREFIX.match(text, content)
    if policy and ENGLISH_TERMS.match(text, RE2_SPACE.match(text, policy.end()).end()):
        return True
    # RE2 permits a whitespace-only local prefix but excludes LF within it.
    last_line_break = text.rfind("\n", start, content)
    prefix_start = last_line_break + 1 if last_line_break >= 0 else start
    local = LOCAL_TERMS_PREFIX.match(text, prefix_start)
    return bool(local and ROMANIAN_TERMS.match(text, RE2_SPACE.match(text, local.end()).end()))


def raw_title_refused(text):
    end = -1
    for opening in RAW_TITLE_OPEN.finditer(text):
        # A run of apparent title openings before one '>' shares the same
        # content offset. Scan that offset once to keep malformed input bounded.
        if opening.end() <= end:
            continue
        end = text.find(">", opening.end())
        if end < 0:
            return False
        if refused_title_at(text, end + 1):
            return True
    return False


def extract_blocks(body, url):
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise SpanError("html_utf8") from None
    if raw_title_refused(text):
        raise SpanError("source_refused")
    if "\x00" in text:
        raise SpanError("html_layout")
    parser = ArticleHTML()
    try:
        parser.feed(text)
        parser.close()
    except (AssertionError, RecursionError):
        raise SpanError("html_layout") from None
    return parser.article_blocks(url)


def match(blocks, quote):
    for index, block in enumerate(blocks):
        start = block.find(quote)
        if start >= 0:
            return {
                "block": index,
                "start": start,
                "end": start + len(quote),
                "block_sha256": digest(block.encode("utf-8")),
            }
    raise SpanError("span_not_found")


def check_batch(cache, raw):
    rows = read_batch(raw)
    results = []
    sources = {}
    for row in rows:
        source = (row["url"], row["receipt_sha256"], row["body_sha256"])
        quote = row["quote"]
        result = {key: row[key] for key in ("link", "url", "receipt_sha256", "body_sha256")}
        result["quote_sha256"] = digest(quote.encode("utf-8"))
        results.append(result)
        sources.setdefault(source, []).append((result, normalize(quote)))
    for source, links in sources.items():
        try:
            blocks = extract_blocks(verified_body(cache, *source), source[0])
        except SpanError as error:
            for result, _ in links:
                result.update(status="fail", code=str(error))
            continue
        for result, quote in links:
            try:
                result.update(status="pass", match=match(blocks, quote))
            except SpanError as error:
                result.update(status="fail", code=str(error))
    status = "pass" if all(result["status"] == "pass" for result in results) else "fail"
    return {"schema": SCHEMA, "batch_sha256": digest(raw), "status": status, "links": results}


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--cache", required=True, type=Path)
    args.add_argument("--batch", required=True, type=Path)
    options = args.parse_args()
    try:
        raw = read_artifact(options.batch.parent, options.batch.name, MAX_BATCH)
    except (ValueError, OSError):
        print("link spans: batch_unavailable", file=sys.stderr)
        return 2
    try:
        report = check_batch(options.cache, raw)
    except SpanError as error:
        print(f"link spans: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, ensure_ascii=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
