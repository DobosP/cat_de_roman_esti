/** Keep the existing appearance unless the browser reports at most 2 GiB. */
export function homeCardBlurEnabled(memory: unknown): boolean {
  return !(typeof memory === "number" && Number.isFinite(memory) && memory > 0 && memory <= 2);
}
