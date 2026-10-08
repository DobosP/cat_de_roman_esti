import * as fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import assert from "node:assert/strict";

const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
function manifest(frontend, name) {
  const directory = path.join(frontend, "node_modules", name), file = path.join(directory, "package.json");
  assert.equal(fs.realpathSync(directory), directory, "Installed compiler package alias/symlink refused");
  const bytes = fs.readFileSync(file), data = JSON.parse(bytes);
  const lock = JSON.parse(fs.readFileSync(path.join(frontend, "package-lock.json")));
  assert.equal(data.name, name);
  assert.equal(data.version, lock.packages[`node_modules/${name}`].version, "Installed package differs from actual owning lock");
  return { directory, data, record: { name: data.name, version: data.version, path: file, sha256: sha(bytes) }, lock };
}
export function nativeCompiler(frontend) {
  const pkg = manifest(frontend, "typescript");
  const selected = JSON.parse(fs.readFileSync(path.join(frontend, "../versions.lock.json"))).tools.find(({ tool }) => tool === "typescript");
  assert.equal(pkg.data.version, selected.version, "Authoritative compiler differs from selected core floor");
  const declared = typeof pkg.data.bin === "string" ? pkg.data.bin : pkg.data.bin?.tsc;
  assert.ok(typeof declared === "string" && !path.isAbsolute(declared), "Package-declared relative native compiler required");
  const executable = path.resolve(pkg.directory, declared), actual = fs.realpathSync(executable);
  assert.ok(actual.startsWith(pkg.directory + path.sep) && executable === actual, "Native compiler executable escaped its verified package");
  assert.ok(fs.statSync(actual).isFile());
  return { executable: actual, package: pkg.record, executable_sha256: sha(fs.readFileSync(actual)) };
}
export function parserBinding(frontend, api) {
  const pkg = manifest(frontend, "@typescript/typescript6");
  const selected = JSON.parse(fs.readFileSync(path.join(frontend, "../versions.lock.json"))).tools.find(({ tool }) => tool === "@typescript/typescript6");
  assert.equal(pkg.data.version, selected.version);
  // This is the approved published wrapper's own dependency, not a consumer-created alias.
  assert.equal(pkg.data.dependencies?.["@typescript/old"], "npm:typescript@^6");
  const require = createRequire(path.join(pkg.directory, "package.json"));
  const implementation = require.resolve("@typescript/old");
  assert.ok(implementation.startsWith(path.join(frontend, "node_modules") + path.sep));
  const implementationPackage = require.resolve("@typescript/old/package.json");
  const bytes = fs.readFileSync(implementationPackage), data = JSON.parse(bytes);
  const relative = path.relative(frontend, path.dirname(implementationPackage)).split(path.sep).join("/");
  assert.equal(data.name, "typescript");
  assert.equal(data.version, pkg.lock.packages[relative].version, "Parser implementation differs from actual resolved lock");
  assert.equal(api.version, data.version, "Observed parser API version differs from its implementation");
  return { package: pkg.record, implementation: { name: data.name, version: data.version, path: implementation,
    manifest_sha256: sha(bytes), entry_sha256: sha(fs.readFileSync(implementation)) }, role: "AST/transpilation only; native7 is authoritative for typechecking" };
}
