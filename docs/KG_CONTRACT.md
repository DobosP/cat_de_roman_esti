# Romanian Knowledge Graph (KG) — Canonical Contract v1

> This is the authoritative contract `cat_de_roman_esti` conforms to. It is pasted
> verbatim from the platform owner. The producer side (romania_scraper) owns the
> build; this repo is a **consumer** and conforms exactly to the served record shapes.

ROMANIAN KNOWLEDGE GRAPH (KG) — CANONICAL CONTRACT v1

PURPOSE: data layer for a "semantic network hop" game (cat_de_roman_esti).
Player gets a START concept + TARGET concept and navigates the graph by hopping
along semantic edges; fewer hops scores higher. Categories scope the playable subgraph.
Two game modes: easy / hard. All four difficulty levers below MUST be encoded as data.

STORAGE: kg.db (SQLite, WAL) in the romania_scraper data_dir, alongside connections.db /
curriculum.db / index.db. Content-addressed ids, idempotent upserts. SQL schema (exact):

    CREATE TABLE nodes (
      id TEXT PRIMARY KEY,            -- blake2b(node_type|canonical_name, digest_size=16) hex
      node_type TEXT NOT NULL,        -- concept|person|place|work|event|org|competency
      label_ro TEXT NOT NULL,         -- display label (Romanian, diacritics preserved)
      canonical_name TEXT NOT NULL,   -- normalized: NFKD + casefold + collapse whitespace
      category TEXT NOT NULL,         -- one of the game categories (taxonomy below)
      description TEXT,               -- short gloss <=200 chars, may be empty string
      salience REAL NOT NULL,         -- 0..1 fame/obscurity (1=famous). Drives obscurity lever
      difficulty_tier TEXT NOT NULL,  -- easy|medium|hard derived from salience bands
      degree INTEGER NOT NULL DEFAULT 0, -- edge count (centrality proxy, feeds salience)
      source TEXT,                    -- producing registry/source name(s), csv
      source_url TEXT,
      access_type TEXT NOT NULL,      -- public_document|public_domain|open_license|tdm_exception
      legal_basis TEXT,
      first_seen TEXT, last_seen TEXT -- ISO-8601
    );
    CREATE TABLE edges (
      id TEXT PRIMARY KEY,            -- blake2b(src_id|relation|dst_id, 16) hex
      src_id TEXT NOT NULL, dst_id TEXT NOT NULL,
      relation TEXT NOT NULL,         -- related_to|is_a|part_of|created_by|located_in|influenced|contemporary_of|same_category
      label_ro TEXT,                  -- human edge label for the map ("a scris", "se afla in")
      strength REAL NOT NULL,         -- 0..1 semantic relatedness/confidence
      is_distractor INTEGER NOT NULL DEFAULT 0, -- 1 = weak/decoy edge (hard-mode density lever)
      bidirectional INTEGER NOT NULL DEFAULT 1,
      supporting_chunk_ids TEXT,      -- json array provenance, may be "[]"
      extraction_method TEXT,         -- relationship|cooccurrence|curriculum|taxonomy
      access_type TEXT NOT NULL, legal_basis TEXT
    );
    CREATE TABLE puzzles (
      id TEXT PRIMARY KEY,            -- blake2b(start_id|target_id|difficulty, 16) hex
      start_id TEXT NOT NULL, target_id TEXT NOT NULL,
      category TEXT NOT NULL,         -- start category, or "mixed"
      difficulty TEXT NOT NULL,       -- easy|hard (the two game modes)
      optimal_hops INTEGER NOT NULL,  -- shortest-path length on the NON-distractor subgraph
      par INTEGER NOT NULL,           -- score threshold (== optimal_hops)
      solution_path TEXT NOT NULL,    -- json array of node ids (one shortest path)
      hint_neighbors TEXT,            -- json: easy-mode suggested next-hop node ids along solution
      start_salience REAL, target_salience REAL, created_at TEXT
    );
    CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT); -- build_version, generated_at, counts json
    + indexes: nodes(category), nodes(difficulty_tier), edges(src_id), edges(dst_id),
      puzzles(difficulty,category).

DIFFICULTY MODEL — encodes ALL FOUR levers the product owner selected:
  1) HOP DISTANCE: puzzles.optimal_hops. easy => optimal_hops in [2,3]; hard => [4,7].
     Computed by BFS over the non-distractor edge subgraph.
  2) CONCEPT OBSCURITY: nodes.salience (0..1) = normalized blend of degree-centrality +
     corpus mention frequency (chunk count) + structured-source prior. Bands ->
     difficulty_tier: >=0.66 easy, 0.33..0.66 medium, <0.33 hard. Easy puzzles pick
     high-salience start/target; hard puzzles pick lower-salience nodes.
  3) EDGE VISIBILITY / HINTS: edges.label_ro + puzzles.hint_neighbors. Easy mode reveals
     edge labels and suggested next hop; hard mode the client hides both.
  4) DISTRACTOR DENSITY: edges.is_distractor + edges.strength. Hard mode keeps distractor
     edges (decoys); easy mode filters them out. distractor = strength < 0.35 OR cross-
     category low-PMI co-occurrence.

CATEGORY TAXONOMY (game categories; each node has exactly one primary category):
  istorie, literatura, geografie, personalitati, arta_cultura, stiinta, societate, limba.
  Mapping: curriculum subject_code -> {ro,limba_si_literatura=>literatura/limba; ist=>istorie;
  geo=>geografie; bio/fiz/chim/mat=>stiinta; ...}. connections entity type -> {person=>
  personalitati; place/country=>geografie; organization=>societate; project/contract=>societate}.
  corpus Domain/document_type -> {history=>istorie; media=>societate; education=>limba; ...}.

DATAAPI PRODUCTS (romania_scraper/dataapi/kg_product.py), follow the EXISTING DataProduct
pattern (license gate via GatePolicy.permits(access_type), cursor pagination, Page return,
ProductSpec). Register in dataapi/products.py _PRODUCT_CLASSES. Three products, kind="graph":
  kg_nodes: record_fields=[id,node_type,label_ro,category,description,salience,difficulty_tier,
            degree,source,source_url,access_type,legal_basis]; filters=[node_type,category,difficulty_tier]
  kg_edges: record_fields=[id,src_id,dst_id,relation,label_ro,strength,is_distractor,bidirectional,
            extraction_method,access_type,legal_basis]; filters=[relation,src_id,dst_id,is_distractor]
  kg_puzzles: record_fields=[id,start_id,target_id,category,difficulty,optimal_hops,par,
            solution_path,hint_neighbors,start_salience,target_salience]; filters=[difficulty,category]

AUTH: in dataapi/auth.py default dev keys add key "cat-de-roman-dev" ->
  Scope(app="cat-de-roman-esti", products={"kg_nodes","kg_edges","kg_puzzles"}, internal=False).
  Existing social-app-dev / ro-teacher-dev keys must NOT gain kg access (scope isolation).
  admin-dev wildcard already covers kg.

CLI: "romania-scraper kg build [--limit N] [--puzzles-per-bucket N] [--commit]" builds kg.db
  from curriculum.db + connections.db + index.db corpus chunks. Default = dry-run (print counts);
  --commit writes. Idempotent. Must degrade gracefully if a source store is absent (build from
  whatever exists) and must NOT add heavy hard deps — spaCy NER only if already importable, else
  rule-based fallback (dictionary match of known entity/competency names + capitalized multiword).

EXTRACTION (romania_scraper/kg/): (1) structured seed from connections.db entities->nodes and
  relationships->edges (strength from confidence), curriculum.db competencies->nodes (category from
  subject) with same_category/part_of edges; (2) corpus concept layer: mine salient terms from
  index.db chunk text (dictionary match + capitalized multiword/heading terms), co-occurrence edges
  (related_to, strength = normalized co-occurrence/PMI within chunk/section); (3) salience = blend
  degree + mention-freq + source prior, normalized 0..1; (4) flag distractors; (5) puzzles via BFS
  shortest paths on non-distractor subgraph, sampled per (category, difficulty band), store
  solution_path + hint_neighbors. All access_type carried from source records, gate fail-closed.

CONSUMER (cat_de_roman_esti): thin stub. Vendor roedu_client.py (stdlib urllib) from
  /home/dobo/work/roedu/client/roedu_client.py. Game engine loads nodes/edges/puzzle from the
  served products, validates each hop is along a real edge, scores hops vs par, toggles
  distractor/hint visibility by mode. Terminal-playable CLI. Tests use a fake server / fixture
  (no live server needed). .env.example: ROEDU_API_URL=http://localhost:8077, ROEDU_API_KEY=cat-de-roman-dev.
