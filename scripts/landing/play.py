#!/usr/bin/env python3
"""Replay every new alias and selectable pack board on a local, pinned Cat build."""
import argparse
from functools import lru_cache
from http.client import HTTPConnection, HTTPException
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlencode, urlsplit

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kgdiff import committed_delta
from support import PLANNER, build_identity, build_receipt, clean_source, git, read_json, registered_artifact, require

BUNDLE = "go-backend/internal/content/bundled.json"
GAMES = ("conexiuni", "contexto", "lant", "alchimie")
ID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")


class LocalHTTP:
    def __init__(self, url):
        parsed = urlsplit(url)
        require(parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port
                and parsed.netloc == f"127.0.0.1:{parsed.port}" and parsed.path in ("", "/")
                and not parsed.query and not parsed.fragment, "Expected http://127.0.0.1:PORT")
        self.port = parsed.port

    def request(self, method, path, data=None, status=200):
        # http.client connects directly. It uses neither proxy variables nor redirects.
        connection = HTTPConnection("127.0.0.1", self.port, timeout=30)
        try:
            connection.request(method, path, json.dumps(data) if data is not None else None,
                               {"Content-Type": "application/json"})
            response = connection.getresponse()
            require(response.status == status, f"{method} {path.split('?')[0]} returned HTTP {response.status}, expected {status}")
            require(response.headers.get_content_type() == "application/json", "Expected a Cat JSON response")
            raw = response.read(1_048_577)
            require(len(raw) <= 1_048_576, "Oversized local API response")
            return read_json(raw)
        finally:
            connection.close()

    def create(self, game, query):
        path = f"/api/wordgames/{game}/games"
        state = self.request("POST", f"{path}?{urlencode(query)}")
        game_id = state.get("game_id")
        require(isinstance(game_id, str) and ID.fullmatch(game_id), "Invalid public game id")
        return f"{path}/{game_id}", state


def tile_ids(rows):
    return [row["id"] for row in rows]


def query_for(board, seed):
    return {"category": board["category"], "difficulty": board["difficulty"], "seed": seed}


def has_shelf(state, board):
    return (state.get("board_category"), state.get("difficulty")) == (board["category"], board["difficulty"])


def find_contexto(http):
    @lru_cache(maxsize=10000)
    def reveal(seed, difficulty, category):
        query = {"seed": seed, "difficulty": difficulty}
        if category:
            query["category"] = category
        path, initial = http.create("contexto", query)
        if category:
            require(has_shelf(initial, query), "Cald seed search returned the wrong shelf")
        return http.request("POST", path + "/giveup")["target"]["id"]
    return reveal


def check_guess(state, owner, won):
    require(state["ok"] is True and state.get("needs_confirmation", False) is False
            and state["attempts"] == 1 and state["guess"]["id"] == owner and state["won"] is won
            and len(state["guesses"]) == 1 and state["guesses"][0] == state["guess"],
            f"Cald guess did not directly use the single expected slot for {owner}")


def check_contexto_win(http, query, text, owner, label):
    path, initial = http.create("contexto", query)
    require(has_shelf(initial, query) and initial["won"] is False
            and initial.get("target") is None and initial["attempts"] == 0,
            "Invalid initial Cald game")
    won = http.request("POST", path + "/guess", {"text": text})
    check_guess(won, owner, True)
    got = http.request("GET", path)
    require(has_shelf(got, query) and got["won"] is True
            and got["target"]["id"] == owner and got["attempts"] == 1,
            "Cald win did not survive reload")
    http.request("POST", path + "/guess", {"text": label}, status=400)


def check_alias(http, reveal, row, target_boards, max_seeds):
    owner, label, form = row["id"], row["label"], row["form"]
    repeat_seed = next((seed for seed in range(max_seeds) if reveal(seed, "normal", "") != owner), None)
    require(repeat_seed is not None, f"No nonwinning Cald target found for alias owner {owner}")
    for words in ((label, form), (form, label)):
        path, _ = http.create("contexto", {"seed": repeat_seed, "difficulty": "normal"})
        first = http.request("POST", path + "/guess", {"text": words[0]})
        second = http.request("POST", path + "/guess", {"text": words[1]})
        check_guess(first, owner, False)
        check_guess(second, owner, False)
        require(first["guess"] == second["guess"], "Cald repeat changed the existing guess")
        got = http.request("GET", path)
        require(got["attempts"] == 1 and got["guesses"] == first["guesses"], "Cald single slot did not survive reload")
    target_seeds = {}
    for board in target_boards:
        seed = next((seed for seed in range(max_seeds)
                     if reveal(seed, board["difficulty"], board["category"]) == owner), None)
        require(seed is not None, f"No Cald winning seed for {board['id']}")
        check_contexto_win(http, query_for(board, seed), form, owner, label)
        target_seeds[board["id"]] = seed
    return {"alias": form, "label": label, "id": owner, "repeat_seed": repeat_seed, "wins": target_seeds}


def conexiuni(http, board, max_seeds):
    payload = board["payload"]
    groups = payload["groups"]
    require(len(groups) == 4 and all(len(group) == 4 for group in groups.values()), "Invalid Conexiuni groups")
    expected = payload["order"]
    for seed in range(max_seeds):
        path, state = http.create("conexiuni", query_for(board, seed))
        if tile_ids(state["tiles"]) == expected:
            break
    else:
        raise ValueError(f"No public Conexiuni seed within {max_seeds}")
    require(has_shelf(state, board) and state["won"] is False and state["solved_count"] == 0
            and "solution" not in state, "Unexpected initial Conexiuni game")
    for index, (key, ids) in enumerate(sorted(groups.items()), 1):
        state = http.request("POST", path + "/guess", {"ids": ids})
        require(state["correct"] is True and state["solved_count"] == index
                and state["category"] == {"key": key, "label": payload["group_labels"][key]}
                and state["won"] is (index == 4), f"Conexiuni rejected or mislabelled group {key}")
    got = http.request("GET", path)
    solution = {row["key"]: (row["label"], tile_ids(row["tiles"])) for row in got["solution"]}
    require(got["won"] is True and got["solved_count"] == 4 and got["mistakes"] == 0
            and solution == {key: (payload["group_labels"][key], ids) for key, ids in groups.items()},
            "Conexiuni final solution or reload differs")
    return seed


def planned_board(http, board, planner, max_seeds, captions):
    game, board_id = board["game"], board["id"]
    environment = {key: os.environ[key] for key in ("PATH", "SystemRoot", "LANG", "LC_ALL") if key in os.environ}
    environment.update(CAT_ACCOUNTS_ENABLED="0", CAT_SUBMISSIONS_DIR="")
    process = subprocess.run([str(planner), game, board_id], env=environment, check=True,
                             capture_output=True, timeout=180)
    plan = read_json(process.stdout)
    require(plan["pack_id"] == board_id, "Offline plan has wrong pack ID")
    seed = int(plan["query"]["seed"])
    query = query_for(board, seed)
    require(0 <= seed < max_seeds and plan["query"] == {key: str(value) for key, value in query.items()},
            "Offline seed and shelf differ from requested board")
    path, initial = http.create(game, query)
    payload = board["payload"]
    require(has_shelf(initial, board) and initial["won"] is False
            and plan["initial"] == {key: value for key, value in initial.items() if key != "game_id"},
            "Public initial game differs from the exact board plan")
    if game == "lant":
        played = [(payload["start"], None)]
        require((initial["start"]["id"], initial["target"]["id"], initial["optimal"])
                == (payload["start"], payload["target"], payload["optimal"]), "Lanț board identity differs")
    else:
        require(tile_ids(initial["inventory"]) == payload["seeds"] and initial["target_depth"] == payload["target_depth"],
                "Alchimie board seeds or depth differ")
    action = "move" if game == "lant" else "combine"
    steps = plan["steps"]
    require(steps, "Offline board plan is empty")
    for index, step in enumerate(steps, 1):
        require(step["action"] == action, "Unexpected offline gameplay action")
        state = http.request("POST", f"{path}/{action}", step["payload"])
        require(state["moves"] == index and state["won"] is (index == len(steps)),
                f"{game} action {index} did not produce the expected progress")
        if game == "lant":
            previous, current = played[-1][0], state["current"]["id"]
            expected = captions.get(f"{previous}\0{current}")
            require(state["ok"] is True and expected and state["relation"] == expected
                    and (state["path"][-1]["id"], state["path"][-1]["relation"]) == (current, expected),
                    f"Lanț caption differs from the candidate for {previous} → {current}")
            played.append((current, expected))
    got = http.request("GET", path)
    require(got["won"] is True and got["moves"] == len(steps) and got["target"]["id"] == payload["target"],
            f"{game} win did not reach the candidate target after reload")
    if game == "lant":
        require([(row["id"], row.get("relation")) for row in got["path"]] == played,
                "Lanț caption path differs after reload")
    return seed


def scope(delta, bundled, touched=()):
    all_pack = {row["id"]: row for row in bundled["pack_items"]}
    pack = {key: row for key, row in all_pack.items()
            if row["pilot_eligible"] and row["status"] == "approved" and row["game"] in GAMES}
    wanted = {}
    for game, change in delta["boards"].items():
        ids = {row["id"] for row in change["added"]}
        ids.update(row["id"] for row in change.get("changed", []) if row["id"] in pack)
        if change.get("eligibility"):
            ids.update(change["eligibility"]["added"])
        wanted.update((board_id, game) for board_id in ids)
    for board_id in touched:
        wanted.setdefault(board_id, all_pack.get(board_id, {}).get("game", "unknown"))
    boards, blocked = [], []
    for board_id, game in sorted(wanted.items(), key=lambda item: (item[1], item[0])):
        board = pack.get(board_id)
        if board is None or board["game"] != game:
            blocked.append((game, board_id))
        else:
            boards.append(board)
    return boards, blocked, pack


def play(http, delta, bundled, planner, max_seeds, touched=()):
    reveal = find_contexto(http)
    boards, blocked, pack = scope(delta, bundled, touched)
    aliases = delta["aliases"]["added"]
    failures = 0
    for game, board_id in blocked:
        print(json.dumps({"game": game, "id": board_id, "error": "Board is unknown, unsupported or unselectable"}))
        failures += 1
    for row in aliases:
        try:
            targets = [board for board in pack.values() if board["game"] == "contexto"
                       and board["payload"]["target"] == row["id"]]
            print(json.dumps(check_alias(http, reveal, row, targets, max_seeds), ensure_ascii=False))
        except (OSError, ValueError, KeyError, TypeError, HTTPException) as exc:
            print(json.dumps({**row, "error": str(exc)}, ensure_ascii=False))
            failures += 1
    for board in boards:
        game, board_id, payload = board["game"], board["id"], board["payload"]
        result = {"game": game, "id": board_id}
        try:
            shelf = [other for other in pack.values()
                     if other["id"] != board_id
                     and all(other[key] == board[key] for key in ("game", "category", "difficulty"))]
            if game == "conexiuni":
                require(not any(other["payload"]["order"] == payload["order"] for other in shelf),
                        "Conexiuni order is ambiguous on the public shelf")
                seed = conexiuni(http, board, max_seeds)
            elif game == "contexto":
                target = payload["target"]
                require(not any(other["payload"]["target"] == target for other in shelf),
                        "Cald target is ambiguous on the public shelf")
                seed = next((seed for seed in range(max_seeds)
                             if reveal(seed, board["difficulty"], board["category"]) == target), None)
                require(seed is not None, "No public Cald winning seed found")
                label = bundled["labels"][target]
                check_contexto_win(http, query_for(board, seed), label, target, label)
            else:
                seed = planned_board(http, board, planner, max_seeds, bundled["lant_captions"])
            print(json.dumps({**result, "seed": seed, "won": True}))
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, HTTPException) as exc:
            print(json.dumps({**result, "error": str(exc)}))
            failures += 1
    print(json.dumps({"aliases": len(aliases), "boards": len(boards) + len(blocked), "failures": failures}))
    return int(bool(failures))


def verify_server(http, identity, manifest):
    require(http.request("GET", "/api/gui-build") == identity,
            "Local server build identity differs from the pinned candidate")
    actual_manifest = http.request("GET", "/api/manifest")
    require(json.dumps(actual_manifest, sort_keys=True) == json.dumps(manifest, sort_keys=True),
            "Local server content identity differs")
    require(http.request("GET", "/api/me")["accounts_enabled"] is False, "Use a disposable anonymous local server")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--build-dir", type=Path, required=True, help="owning pinned build mirror root")
    parser.add_argument("--touched-board", action="append", default=[],
                        help="also verify this affected selectable board ID; may repeat")
    parser.add_argument("--max-seeds", type=int, default=10000)
    args = parser.parse_args()
    try:
        require(1 <= args.max_seeds <= 10000, "Seed limit must be 1–10000")
        repo = args.repo.resolve()
        delta = committed_delta(repo, args.baseline, args.sha, include_neighbors=False)
        clean_source(repo, args.sha)
        raw, receipt, artifacts, _ = build_receipt(repo, args.sha)
        _, identity = build_identity(args.build_dir.resolve(), raw, receipt, artifacts)
        bundled = read_json(git(repo, "show", f"{args.sha}:{BUNDLE}"))
        http = LocalHTTP(args.base_url)
        verify_server(http, identity, bundled["manifest"])
        boards, _, _ = scope(delta, bundled, args.touched_board)
        planner = None
        if any(board["game"] in ("lant", "alchimie") for board in boards):
            registered_artifact(repo, artifacts, PLANNER)
            planner = repo / PLANNER
        print(json.dumps({"sha": args.sha, "baseline": args.baseline, "content_hash": bundled["manifest"]["content_hash"]}))
        return play(http, delta, bundled, planner, args.max_seeds, args.touched_board)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, HTTPException) as exc:
        print(f"HTTP playthrough failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
