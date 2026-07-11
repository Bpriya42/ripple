import type { RippleEdge } from "../api/client";

export type ConsequenceCategory = "markets" | "costs" | "policy" | "supply";

export const consequenceCategories: Record<string, ConsequenceCategory> = {
  "commodity.oil_price": "markets",
  "outcome.importer_inflation": "costs",
  "outcome.transport_cost": "costs",
  "outcome.energy_security": "policy",
  "outcome.supply_shortage": "supply",
};

export const locationFixtures: Record<
  string,
  {
    label: string;
    latitude: number;
    longitude: number;
    highlightedCountries: string[];
  }
> = {
  "Strait of Hormuz": {
    label: "Strait of Hormuz",
    latitude: 26.56,
    longitude: 56.25,
    highlightedCountries: ["Iran", "Oman"],
  },
  "Bab el-Mandeb Strait": {
    label: "Bab el-Mandeb Strait",
    latitude: 12.58,
    longitude: 43.33,
    highlightedCountries: ["Yemen", "Djibouti"],
  },
};

export const regionalEffectFixtures = [
  {
    label: "East Asia importers",
    latitude: 31,
    longitude: 121,
    category: "markets" as ConsequenceCategory,
  },
  {
    label: "European importers",
    latitude: 50,
    longitude: 10,
    category: "costs" as ConsequenceCategory,
  },
  {
    label: "South Asia importers",
    latitude: 20,
    longitude: 77,
    category: "costs" as ConsequenceCategory,
  },
];

export function categoryFor(edge: RippleEdge): ConsequenceCategory {
  return consequenceCategories[edge.to_node] ?? "supply";
}

export function humanize(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
