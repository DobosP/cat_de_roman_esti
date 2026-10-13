// The wrapper forwards its effective limit as GOMAXPROCS. Compose does not
// forward GATE_PARALLEL_MAX, so read that cap from the committed gate file.
export function guiBrowserWorkers(environment, gateEnvironment) {
  const caps = gateEnvironment.split("\n").filter((line) => line.startsWith("GATE_PARALLEL_MAX="));
  if (caps.length !== 1 || !/^GATE_PARALLEL_MAX=[1-4]$/.test(caps[0])
    || !["1", "2", "3", "4"].includes(environment.GOMAXPROCS)) {
    throw new Error("GUI browser workers require the committed cap and wrapper parallel limit");
  }
  const cap = Number(caps[0].split("=")[1]), effective = Number(environment.GOMAXPROCS);
  if (effective > cap) throw new Error("GUI browser workers exceed the committed gate cap");
  return effective;
}
