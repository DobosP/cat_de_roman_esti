// Design tokens shared between CSS (via :root vars) and TS (canvas / inline styles).
// The category color map is the single source of truth for node/edge/badge coloring;
// the force-graph canvas reads it directly (it can't see CSS variables).

export interface CategoryStyle {
  /** Human, Romanian-flavoured menu label. */
  label: string;
  /** Bright accent (node fill / glow). */
  color: string;
  /** Softer companion for gradients / halos. */
  glow: string;
  /** One-line description used on the menu cards. */
  blurb: string;
}

export const CATEGORY_STYLES: Record<string, CategoryStyle> = {
  istorie: {
    label: "Istorie",
    color: "#f4a259",
    glow: "#ffcaa0",
    blurb: "Domnitori, batalii si momente care au scris tara.",
  },
  literatura: {
    label: "Literatura",
    color: "#8ec5ff",
    glow: "#bfe0ff",
    blurb: "Poeti, opere si curente — de la Eminescu la modernism.",
  },
  geografie: {
    label: "Geografie",
    color: "#5fd99b",
    glow: "#a7f0c8",
    blurb: "Munti, rauri si regiuni de la Carpati la Marea Neagra.",
  },
  personalitati: {
    label: "Personalitati",
    color: "#f178b6",
    glow: "#ffb0d8",
    blurb: "Oameni care au dus numele Romaniei in lume.",
  },
  arta_cultura: {
    label: "Arta & Cultura",
    color: "#c08bff",
    glow: "#dcc0ff",
    blurb: "Pictura, muzica, film si traditii vii.",
  },
  stiinta: {
    label: "Stiinta",
    color: "#56d4dd",
    glow: "#a3eef2",
    blurb: "Inventatori si descoperiri cu semnatura romaneasca.",
  },
  societate: {
    label: "Societate",
    color: "#ffd166",
    glow: "#ffe6a8",
    blurb: "Institutii, miscari si felul in care traim impreuna.",
  },
  limba: {
    label: "Limba",
    color: "#7bdff2",
    glow: "#b8eef9",
    blurb: "Cuvinte, expresii si povestea limbii romane.",
  },
  mixed: {
    label: "Mixt",
    color: "#b8b8d1",
    glow: "#e0e0f0",
    blurb: "Salturi care trec granitele dintre categorii.",
  },
};

const FALLBACK: CategoryStyle = {
  label: "Necunoscut",
  color: "#9aa3b2",
  glow: "#c9d0db",
  blurb: "Categorie fara stil definit.",
};

export function categoryStyle(category: string): CategoryStyle {
  return CATEGORY_STYLES[category] ?? FALLBACK;
}

export function categoryColor(category: string): string {
  return categoryStyle(category).color;
}

export function categoryLabel(category: string): string {
  return categoryStyle(category).label;
}

/** Canvas palette the force-graph reads (CSS vars are invisible to <canvas>). */
export const CANVAS = {
  background: "#0a0b14",
  edge: "rgba(150, 162, 196, 0.22)",
  edgeTrail: "#ffd166",
  edgeFlash: "#ffffff",
  textLight: "#eef1f8",
  textDim: "rgba(238, 241, 248, 0.55)",
  current: "#ffffff",
  target: "#ff5d8f",
} as const;
