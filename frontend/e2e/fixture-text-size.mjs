// Keep the zoom fixture under the document's real CSP, including enforced mode.
export async function applyDoubledText(page) {
  await page.evaluate(() => {
    const metas = document.head.querySelectorAll('meta[property="csp-nonce"], meta[name="csp-nonce"]');
    if (metas.length !== 1) throw new Error("Missing or ambiguous rendered CSP nonce bootstrap");
    const meta = metas[0];
    const nonce = meta.content;
    const nonces = new Set(Array.from(document.querySelectorAll("[nonce]"), (element) => element.nonce));
    if (!nonce || meta.getAttribute("property") !== "csp-nonce" || meta.nonce !== nonce || nonces.size !== 1 || !nonces.has(nonce)) {
      throw new Error("Missing or conflicting rendered CSP nonce");
    }
    const root = document.documentElement;
    const before = Number.parseFloat(getComputedStyle(root).fontSize);
    if (!Number.isFinite(before) || before <= 0) throw new Error("Invalid initial root font size");
    const style = document.createElement("style");
    style.nonce = nonce;
    style.textContent = "html { font-size: 200% !important; }";
    document.head.append(style);
    const after = Number.parseFloat(getComputedStyle(root).fontSize);
    if (!style.sheet || after !== before * 2) throw new Error("The 200% text-size fixture did not double the computed root font size");
  });
}
