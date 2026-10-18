import { afterEach, beforeEach, expect, test } from "vitest";
import { page } from "vitest/browser";
import { render, type ComponentChildren, type ComponentType } from "preact";
import { ErrorBoundary, LocationProvider } from "preact-iso";
import { GameIntro } from "../../src/components/GameIntro";
import { GameShell } from "../../src/components/GameShell";
import { RouteErrorBoundary } from "../../src/components/RouteErrorBoundary";
import { ScreenURL } from "../../src/screenLocation";
import { lazyScreen } from "../../src/lazyScreen";
import cases from "./case-ids.json";
import "@roedu/ui/styles.css";

let host: HTMLDivElement;
const extraHosts: HTMLDivElement[] = [];
beforeEach(() => {
  host = document.createElement("div"); host.className = "roedu-root screen-pad";
  document.body.append(host);
});
afterEach(() => {
  for (const node of [host, ...extraHosts.splice(0)]) { render(null, node); node.remove(); }
});
function frame(children: ComponentChildren) {
  return <LocationProvider><ScreenURL.Provider value="/intrusul">{children}</ScreenURL.Provider></LocationProvider>;
}
const intro = (options: { starting?: boolean; onStart?: () => void; onDaily?: () => void } = {}) => frame(
  <GameIntro icon="🧩" title="Test de joc" accent="#8b5cf6" description="Alege o acțiune."
    startLabel="Joacă liber" dailyLabel="Joacă zilnic" onStart={options.onStart ?? (() => {})}
    onDaily={options.onDaily} starting={options.starting} />,
);

test(cases[0], async () => {
  render(intro(), host);
  await expect.poll(() => document.activeElement === page.getByRole("button", { name: "Joacă liber", exact: true }).element()).toBe(true);
  render(null, host);
  const other = document.createElement("button"); other.textContent = "Alt control";
  document.body.append(other);
  try {
    other.focus(); expect(document.activeElement).toBe(other);
    render(intro(), host);
    await expect.poll(() => document.activeElement === page.getByRole("button", { name: "Joacă liber", exact: true }).element()).toBe(true);
  } finally { other.remove(); }
});

test(cases[1], async () => {
  let starts = 0, dailies = 0;
  const options = { onStart: () => { starts++; }, onDaily: () => { dailies++; } };
  render(intro(options), host);
  const primary = page.getByRole("button", { name: "Joacă liber", exact: true });
  const daily = page.getByRole("button", { name: "Joacă zilnic", exact: true });
  const primaryElement = primary.element() as HTMLButtonElement;
  const dailyElement = daily.element() as HTMLButtonElement;
  render(intro({ ...options, starting: true }), host);
  expect(host.querySelector<HTMLElement>(".game-intro")?.inert).toBe(true);
  expect(host.querySelector(".game-intro")?.getAttribute("aria-busy")).toBe("true");
  expect(primaryElement.disabled).toBe(true); expect(dailyElement.disabled).toBe(true);
  primaryElement.click(); dailyElement.click(); expect([starts, dailies]).toEqual([0, 0]);
  render(intro(options), host);
  expect(host.querySelector<HTMLElement>(".game-intro")?.inert).toBe(false);
  await expect.poll(() => (primary.element() as HTMLButtonElement).disabled).toBe(false); await primary.click();
  expect([starts, dailies]).toEqual([1, 0]);
  await daily.click(); expect([starts, dailies]).toEqual([1, 1]);
});

test(cases[2], async () => {
  let exits = 0;
  const onExit = () => { exits++; };
  render(<GameShell busy onExit={onExit} title="Joc" />, host);
  const locked = page.getByRole("button", { name: "Se pregătește jocul", exact: true });
  expect((locked.element() as HTMLButtonElement).disabled).toBe(true);
  (locked.element() as HTMLButtonElement).click(); expect(exits).toBe(0);
  render(<GameShell onExit={onExit} title="Joc" />, host);
  const exit = page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true });
  expect((exit.element() as HTMLButtonElement).disabled).toBe(false); await exit.click(); expect(exits).toBe(1);
});

test(cases[3], async () => {
  render(<GameShell onExit={() => {}} title="Joc" />, host);
  const header = host.querySelector<HTMLElement>(".game-shell-header")!;
  const measured = () => host.style.getPropertyValue("--game-shell-header-height");
  await expect.poll(measured).toBe(`${header.offsetHeight}px`);
  const oldHeight = header.offsetHeight;
  header.style.setProperty("min-height", `${oldHeight + 100}px`);
  await expect.poll(() => header.offsetHeight).toBeGreaterThan(oldHeight);
  await expect.poll(measured).toBe(`${header.offsetHeight}px`);
  render(null, host); expect(measured()).toBe("");
});

test(cases[4], async () => {
  let loads = 0;
  let resolve!: (module: { default: ComponentType<{ label: string }> }) => void;
  const module = new Promise<{ default: ComponentType<{ label: string }> }>((done) => { resolve = done; });
  const Lazy = lazyScreen(() => { loads++; return module; });
  const second = document.createElement("div"); document.body.append(second); extraHosts.push(second);
  render(<ErrorBoundary><Lazy label="Primul ecran" /></ErrorBoundary>, host);
  render(<ErrorBoundary><Lazy label="Al doilea ecran" /></ErrorBoundary>, second);
  expect(loads).toBe(1);
  resolve({ default: ({ label }) => <h2>{label}</h2> });
  await expect.poll(() => page.getByRole("heading", { name: "Primul ecran", exact: true }).element().checkVisibility()).toBe(true);
  await expect.poll(() => page.getByRole("heading", { name: "Al doilea ecran", exact: true }).element().checkVisibility()).toBe(true);
  expect(loads).toBe(1);
});

test(cases[5], async () => {
  let loads = 0;
  let reject!: (error: Error) => void;
  const module = new Promise<{ default: ComponentType<Record<string, never>> }>((_resolve, fail) => { reject = fail; });
  const Lazy = lazyScreen(() => { loads++; return module; });
  render(<RouteErrorBoundary pathname="/intrusul"><ErrorBoundary><Lazy /></ErrorBoundary></RouteErrorBoundary>, host);
  expect(loads).toBe(1);
  reject(new Error("Held chunk unavailable"));
  const failure = page.getByRole("heading", { name: "Nu am putut încărca jocul.", exact: true });
  await expect.poll(() => failure.element().checkVisibility()).toBe(true);
  expect(document.activeElement).toBe(failure.element());
  expect(page.getByRole("link", { name: "Înapoi la jocuri", exact: true }).element().checkVisibility()).toBe(true);
  render(<RouteErrorBoundary pathname="/perechi"><h2>Ecran disponibil</h2></RouteErrorBoundary>, host);
  await expect.poll(() => page.getByRole("heading", { name: "Ecran disponibil", exact: true }).element().checkVisibility()).toBe(true);
  expect(host.querySelector('[role="alert"]')).toBeNull(); expect(loads).toBe(1);
});
