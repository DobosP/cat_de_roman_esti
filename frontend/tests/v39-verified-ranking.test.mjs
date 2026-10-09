import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const authApi = read("../src/api/auth.ts");

void test("ranking API types the requester marker as boolean", () => {
  assert.match(authApi, /is_me: boolean/);
});
