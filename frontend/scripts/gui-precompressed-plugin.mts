import path from "node:path";
import assert from "node:assert/strict";
import type { Plugin } from "vite";
import { emitPrecompressedAssets } from "./gui-precompressed-assets.mjs";

export function guiPrecompressedPlugin(): Plugin {
  let output = "", written = false, failed = false;
  return {
    name: "cat-final-manifest-precompressed-assets",
    apply: "build",
    configResolved(config) {
      assert.equal(config.build.outDir, "dist");
      assert.equal(config.build.manifest, true);
      assert.equal(config.build.write, true);
      output = path.resolve(config.root, config.build.outDir);
    },
    buildStart() { written = false; failed = false; },
    buildEnd(error) { failed = !!error; },
    writeBundle() { written = true; },
    // closeBundle follows finalized on-disk HTML/manifest/minified assets.
    closeBundle: { order: "post", sequential: true, handler() {
      if (written && !failed) emitPrecompressedAssets(output);
    } },
  };
}
