import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const source = readFileSync(new URL("../src/sound.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
}).outputText;
const moduleUrl = `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`;

for (const reducedMotion of [false, true]) {
  test(`denied storage at module import keeps sound usable (reduced motion: ${reducedMotion})`, async (t) => {
    const descriptors = ["localStorage", "window"].map((key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)]);
    t.after(() => {
      for (const [key, descriptor] of descriptors) {
        if (descriptor) Object.defineProperty(globalThis, key, descriptor);
        else delete globalThis[key];
      }
    });
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      get() { throw new DOMException("Storage denied", "SecurityError"); },
    });
    const events = [];
    globalThis.window = Object.assign(new EventTarget(), {
      matchMedia: () => ({ matches: reducedMotion }),
    });
    globalThis.window.addEventListener("cat-sound-muted-change", (event) => events.push(event));

    // This import runs the same preference initializer that executes before React.
    const sound = await import(`${moduleUrl}#denied-${reducedMotion}`);
    assert.equal(sound.isMuted(), reducedMotion);
    assert.equal(sound.toggleMuted(), !reducedMotion);
    assert.equal(sound.isMuted(), !reducedMotion);
    assert.equal(events.length, 1);
    assert.equal(events[0].detail, !reducedMotion);
    assert.doesNotThrow(() => sound.playSfx("select"));
  });
}
