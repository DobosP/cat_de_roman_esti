import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync, realpathSync } from "node:fs";
import path from "node:path";
import type { Plugin } from "vite";

// A production-build annotation of four proven allocations in one immutable
// SDK payload. This does not replace the SDK or declare general call purity.
export const SDK_ALLOCATION_BINDING = Object.freeze({
  uiVersion: "0.3.0",
  uiSha256: "45bc37efd15df1d9671d17e5d5f96518128a19da9af4bdfc3d437906ab8d049d",
  reactVersion: "19.2.7",
  reactProductionSha256: "66fa8fc8149e02f61dd5f26e3d0ea7bd03bac64a52d15601019f50a61260a115",
});
export const SDK_UNUSED_ALLOCATIONS = Object.freeze([
  { binding: "F", component: "Card", marker: "roedu-card" },
  { binding: "G", component: "Stack", marker: "roedu-stack" },
  { binding: "Z", component: "Container", marker: "roedu-container" },
  { binding: "D", component: "Input", marker: "roedu-field" },
]);
export const allocationHash = (bytes: string | Uint8Array): string =>
  createHash("sha256").update(bytes).digest("hex");
export function assertSdkAllocationBinding(observed: { uiVersion: string; uiSha256: string;
  reactVersion: string; reactProductionSha256: string }): void {
  assert.deepEqual(observed, SDK_ALLOCATION_BINDING, "SDK allocation production binding differs");
}
export function annotateUnusedSdkAllocations(source: string): string {
  assert.equal(allocationHash(source), SDK_ALLOCATION_BINDING.uiSha256, "SDK allocation payload differs");
  let code = source;
  for (const { binding } of SDK_UNUSED_ALLOCATIONS) {
    const before = `, ${binding} = m(function(`;
    assert.equal(code.split(before).length - 1, 1, `Expected exactly one ${binding} allocation`);
    code = code.replace(before, `, ${binding} = /* @__PURE__ */ m(function(`);
  }
  assert.equal(code.split("const q = m(function(").length - 1, 1, "Used Button allocation changed");
  return code;
}
export function boundSdkAllocationInputs(frontend: string) {
  const packageRoot = realpathSync(frontend);
  const lock = JSON.parse(readFileSync(path.join(packageRoot, "package-lock.json"), "utf8"));
  const packages = ["@roedu/ui", "react"].map((name) => {
    const directory = path.join(packageRoot, "node_modules", name);
    assert.equal(realpathSync(directory), directory, "SDK allocation package aliases are refused");
    const manifestPath = path.join(directory, "package.json");
    const manifestBytes = readFileSync(manifestPath);
    const manifest = JSON.parse(manifestBytes.toString("utf8"));
    assert.equal(manifest.name, name);
    assert.equal(manifest.version, lock.packages[`node_modules/${name}`].version, "Installed SDK allocation package differs from owning lock");
    return { name, version: manifest.version as string, directory, manifestPath,
      manifestSha256: allocationHash(manifestBytes) };
  });
  const ui = packages[0]!, react = packages[1]!;
  const uiPath = path.join(ui.directory, "dist/index.js");
  const reactProductionPath = path.join(react.directory, "cjs/react.production.js");
  assert.equal(realpathSync(uiPath), uiPath);
  assert.equal(realpathSync(reactProductionPath), reactProductionPath);
  const uiSource = readFileSync(uiPath, "utf8");
  const reactProductionSource = readFileSync(reactProductionPath, "utf8");
  assertSdkAllocationBinding({ uiVersion: ui.version, uiSha256: allocationHash(uiSource),
    reactVersion: react.version, reactProductionSha256: allocationHash(reactProductionSource) });
  return { packages, uiPath, uiSource, reactProductionPath, reactProductionSource };
}
export function guiSdkAllocationPlugin(): Plugin {
  let inputs: ReturnType<typeof boundSdkAllocationInputs> | undefined;
  let transformed = 0;
  return {
    name: "cat-ui-0.3.0-unused-production-allocations",
    apply: "build",
    enforce: "pre",
    configResolved(config) {
      if (config.isProduction) inputs = boundSdkAllocationInputs(config.root);
    },
    transform(code, id) {
      if (!inputs || id !== inputs.uiPath) return null;
      assert.equal(transformed++, 0, "SDK allocation payload transformed more than once");
      assert.equal(code, inputs.uiSource, "SDK allocation pre-transform payload changed");
      // Production React's bound forwardRef only returns { $$typeof, render };
      // the four function-expression arguments allocate without being invoked.
      return { code: annotateUnusedSdkAllocations(code), map: null };
    },
    generateBundle() {
      if (inputs) assert.equal(transformed, 1, "Bound SDK allocation payload was not transformed");
    },
  };
}
