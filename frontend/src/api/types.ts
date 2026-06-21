// TS types that BYTE-MATCH the server contract (see web app CONTRACT + JSON SHAPES).
// The server computes everything; the client never trusts or recomputes game logic.

/** One concept/person/place/work in a category subgraph. */
export interface GraphNode {
  id: string;
  label: string;
  category: string;
  node_type: string;
  /** 0..1 — drives node radius / glow intensity. */
  salience: number;
  difficulty_tier: string;
  description: string;
}

/** A semantic relation connecting two nodes. */
export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  /** Human label — present in easy mode, "" in hard mode (decoys look real). */
  label: string;
  bidirectional: boolean;
}

/** The puzzle the player is solving (endpoints + scoring reference). */
export interface PuzzleView {
  id: string;
  category: string;
  difficulty: string;
  start_id: string;
  target_id: string;
  par: number;
  optimal_hops: number;
}

export type Mode = "easy" | "hard";

/** Server-authoritative game session state — the single source of truth for the UI. */
export interface GameState {
  game_id: string;
  mode: Mode;
  category: string;
  puzzle: PuzzleView;
  nodes: GraphNode[];
  edges: GraphEdge[];
  current_id: string;
  target_id: string;
  start_id: string;
  hops: number;
  won: boolean;
  score: number;
  /** Node ids hopped, in order, starting at start — the explicit hop trail. */
  path: string[];
  /** Node ids reachable from current in this mode. */
  neighbors: string[];
  /** easy: suggested next node id from current; hard: null. */
  hint: string | null;
  /** Set when a hop was rejected; state otherwise unchanged. */
  last_error: string | null;
}

// ----------------------------------------------------------------- catalog/health

export interface HealthResponse {
  ok: boolean;
  source: "offline" | "live";
  server_url: string | null;
  categories: number;
}

/** One row of the menu catalog: how many puzzles a category has per difficulty. */
export interface CatalogCategory {
  category: string;
  label: string;
  easy: number;
  hard: number;
}

export interface CatalogResponse {
  source: "offline" | "live";
  categories: CatalogCategory[];
}

// ----------------------------------------------------------------- request bodies

export interface CreateGameBody {
  category: string;
  difficulty: Mode;
  /**
   * Optional puzzle id to avoid when more than one candidate exists. The server
   * picks the first candidate whose id != exclude (else falls back to the first).
   * Used by the Win screen's "Urmatoarea" so Next advances to a different puzzle.
   */
  exclude?: string;
}

export interface HopBody {
  to: string;
}
