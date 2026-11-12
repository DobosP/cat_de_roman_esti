import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";

const TEST_FILE = "go-backend/internal/contentops/readset_producer_test.go";
const TEST = "TestQuickPendingActualCompiledProducerReadset";
const PACKAGE = "github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops";
const MIN_BYTES = 32 * 1024 * 1024;
const MAX_BYTES = 256 * 1024 * 1024;
const NAME = "cat-content-rail";
const SCRATCH = "/tmp";
const scratchPrefix = (invocation) => `cat-pending-review-producer-${invocation}-`;
export const PRODUCER_DESCRIPTOR = "pending-review-producer.json";
export const PRODUCER_BUILD_CHECK = "cat-unit-build-pending-review-producer";
export const PRODUCER_BUILD_ASSERT = "Actual pending producer build requires verified managed assets and identity";
export const PRODUCER_RACE_ASSERT = "Actual pending producer test ran and passed once with the built executable size and SHA-256";

export function hasActualProducerTest(root) {
  const file = path.join(root, TEST_FILE);
  const info = fs.lstatSync(file, { throwIfNoEntry: false });
  if (!info) return false;
  if (!info.isFile() || fs.realpathSync(file) !== file) throw Error("Nonregular actual producer test registration");
  return true;
}

export const producerBuildArgs = (output) => ["build", "-mod=readonly", "-buildvcs=false", "-o", output, `./cmd/${NAME}`];
export const producerSizeValid = (size) => Number.isSafeInteger(size) && size > MIN_BYTES && size <= MAX_BYTES;
export function producerOutputValid(output, invocation) {
  if (typeof output !== "string") return false;
  const prefix = `${SCRATCH}/${scratchPrefix(invocation)}`;
  return output.startsWith(prefix) && /^[a-zA-Z0-9]{6}\/cat-content-rail$/.test(output.slice(prefix.length));
}

const sameFile = (before, after) => after.isFile() && ["dev", "ino", "size", "mode", "uid", "gid", "nlink", "mtimeNs", "ctimeNs"]
  .every((key) => before[key] === after[key]);

function fingerprint(file) {
  const before = fs.lstatSync(file, { bigint: true });
  if (!before.isFile() || before.nlink !== 1n || before.uid !== BigInt(process.geteuid()) || !(before.mode & 0o100n)
    || !producerSizeValid(Number(before.size)) || fs.realpathSync(file) !== file) throw Error("Actual producer executable is outside its regular-file, size or ownership bounds");
  const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
  try {
    if (!sameFile(before, fs.fstatSync(fd, { bigint: true })) || fs.realpathSync(`/proc/self/fd/${fd}`) !== file) {
      throw Error("Actual producer changed before hashing");
    }
    const hash = createHash("sha256"), buffer = Buffer.alloc(64 * 1024);
    const size = Number(before.size);
    let offset = 0;
    while (offset < size) {
      const count = fs.readSync(fd, buffer, 0, Math.min(buffer.length, size - offset), null);
      if (!count) throw Error("Actual producer was truncated while hashing");
      hash.update(buffer.subarray(0, count));
      offset += count;
    }
    const unchanged = () => sameFile(before, fs.lstatSync(file, { bigint: true })) && fs.realpathSync(file) === file;
    if (fs.readSync(fd, buffer, 0, 1, null) || !sameFile(before, fs.fstatSync(fd, { bigint: true })) || !unchanged()) {
      throw Error("Actual producer changed while hashing");
    }
    return { bytes: size, sha256: hash.digest("hex"), unchanged };
  } finally { fs.closeSync(fd); }
}

export function withActualProducer(hook, managed, runRace) {
  const { root, target, invocation, sha, tree_sha256, toolchain_digest, parallel } = hook.context;
  let scratch, producer;
  try {
    hook.check(PRODUCER_BUILD_CHECK, () => {
      hook.assert(PRODUCER_BUILD_ASSERT, managed);
      scratch = fs.mkdtempSync(path.join(SCRATCH, scratchPrefix(invocation)));
      const privateDirectory = fs.lstatSync(scratch);
      if (!privateDirectory.isDirectory() || privateDirectory.uid !== process.geteuid()
        || (privateDirectory.mode & 0o7777) !== 0o700 || fs.realpathSync(scratch) !== scratch) {
        throw Error("Private actual producer scratch required");
      }
      const output = path.join(scratch, NAME);
      hook.run("go", producerBuildArgs(output), path.join(root, "go-backend"), {
        GOENV: "off", GOTOOLCHAIN: "local", GOWORK: "off", GOPROXY: "off", GONOPROXY: "none",
        GOSUMDB: "off", GOVCS: "*:off", CGO_ENABLED: "1", GOFLAGS: `-p=${parallel}`,
        GIT_NO_LAZY_FETCH: "1", GIT_OPTIONAL_LOCKS: "0",
      });
      const { bytes, sha256, unchanged } = fingerprint(output);
      const file = `.gate/${target}/${PRODUCER_DESCRIPTOR}`;
      fs.writeFileSync(path.join(root, file), JSON.stringify({
        schema: 1, target, invocation, sha, tree_sha256, toolchain_digest, output, bytes, sha256,
      }, null, 2) + "\n", { flag: "wx", mode: 0o600 });
      hook.artifact(file);
      producer = { bytes, sha256, unchanged, environment: { PENDING_REVIEW_TOOL: output, PENDING_REVIEW_TOOL_SHA256: sha256 } };
    });
    runRace(producer);
  } finally {
    if (scratch) fs.rmSync(scratch, { recursive: true, force: true });
  }
}

export function actualProducerEvents(output, producer) {
  try {
    const events = String(output).split("\n").filter((line) => line.trim()).map((line) => JSON.parse(line));
    if (events.some((event) => !event || Array.isArray(event) || typeof event.Action !== "string"
      || (Object.hasOwn(event, "Output") && typeof event.Output !== "string")
      || (Object.hasOwn(event, "Test") && typeof event.Test !== "string"))) return false;
    const packageEvents = events.filter((event) => event.Package === PACKAGE);
    const testEvents = packageEvents.filter((event) => event.Test === TEST);
    const runs = testEvents.filter((event) => event.Action === "run"), passes = testEvents.filter((event) => event.Action === "pass");
    const fingerprints = testEvents.filter((event) => event.Action === "output" && typeof event.Output === "string"
      && event.Output.includes("actual unstripped producer"));
    const completion = packageEvents.filter((event) => event.Action === "pass" && event.Test === undefined);
    if (runs.length !== 1 || passes.length !== 1 || fingerprints.length !== 1 || completion.length !== 1
      || packageEvents.some((event) => event.Action === "fail"
        || (typeof event.Output === "string" && event.Output.includes("(cached)")))
      || testEvents.some((event) => !["run", "output", "pass"].includes(event.Action))) return false;
    const outputLine = fingerprints[0].Output;
    const location = /^\s*readset_producer_test\.go:\d+: /.exec(outputLine);
    const logged = location && outputLine.slice(location[0].length);
    const sequence = [runs[0], fingerprints[0], passes[0], completion[0]].map((event) => packageEvents.indexOf(event));
    return logged === `actual unstripped producer ${producer.bytes} bytes sha256=${producer.sha256}; source executable remained read-only\n`
      && sequence.every((index, position) => position === 0 || index > sequence[position - 1]);
  } catch {
    return false;
  }
}
