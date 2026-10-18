import { readFileSync } from "node:fs";
import ts from "@typescript/typescript6";

// Compile an acyclic local TS graph into data URLs. A module gets one URL per graph,
// preserving its identity; test assertions still enter through the public scores.ts facade.
export async function importTsGraph(entry) {
  const cache = new Map();
  const active = new Set();
  function compile(url) {
    const key = url.href;
    if (cache.has(key)) return cache.get(key);
    if (active.has(key)) throw new Error(`Cyclic test TS graph: ${key}`);
    active.add(key);
    const source = readFileSync(url, "utf8");
    const dependencies = new Map();
    for (const item of ts.preProcessFile(source, true, true).importedFiles) {
      const specifier = item.fileName;
      if (!specifier.startsWith(".")) throw new Error(`Non-local test TS import: ${specifier}`);
      const dependency = new URL(specifier.endsWith(".ts") ? specifier : `${specifier}.ts`, url);
      dependencies.set(specifier, compile(dependency));
    }
    const rewrite = (context) => (file) => {
      const visit = (node) => {
        if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier
          && ts.isStringLiteral(node.moduleSpecifier)) {
          const replacement = dependencies.get(node.moduleSpecifier.text);
          if (replacement) {
            const literal = ts.factory.createStringLiteral(replacement);
            return ts.isImportDeclaration(node)
              ? ts.factory.updateImportDeclaration(node, node.modifiers, node.importClause, literal, node.attributes)
              : ts.factory.updateExportDeclaration(node, node.modifiers, node.isTypeOnly, node.exportClause, literal, node.attributes);
          }
        }
        return ts.visitEachChild(node, visit, context);
      };
      return ts.visitNode(file, visit);
    };
    const compiled = ts.transpileModule(source, {
      compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
      transformers: { before: [rewrite] },
    }).outputText;
    const result = `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`;
    active.delete(key);
    cache.set(key, result);
    return result;
  }
  return import(compile(entry));
}
