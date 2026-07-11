import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import {
  getStory,
  getStoryRipples,
  type RippleEdge,
  type RippleNode,
} from "../api/client";
import {
  categoryFor,
  humanize,
  type ConsequenceCategory,
} from "../data/presentation";
import { GlobeScene } from "./GlobeScene";

function useReducedMotion() {
  const [reduced, setReduced] = useState(
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return reduced;
}

function pathForBranch(branch: string[], edges: RippleEdge[]) {
  const branchEdges = branch
    .map((id) => edges.find((edge) => edge.edge_id === id))
    .filter((edge): edge is RippleEdge => Boolean(edge));
  const first = branchEdges[0];
  if (!first || first.hop === 1) return branch;
  const ancestors: RippleEdge[] = [];
  let from = first.from_node;
  for (let hop = first.hop - 1; hop >= 1; hop -= 1) {
    const parent = edges.find(
      (edge) => edge.hop === hop && edge.to_node === from,
    );
    if (!parent) break;
    ancestors.unshift(parent);
    from = parent.from_node;
  }
  return [...ancestors.map((edge) => edge.edge_id), ...branch];
}

export function claimText(edge: RippleEdge) {
  if (!edge.condition_met)
    return `Conditional pathway. If ${edge.required_condition}, ${edge.mechanism}`;
  if (edge.claim_state === "observed_effect")
    return `Observed effect. ${edge.mechanism}`;
  return `Established mechanism. ${edge.mechanism}`;
}

function EvidencePanel({
  edge,
  nodes,
}: {
  edge: RippleEdge;
  nodes: Map<string, RippleNode>;
}) {
  const disruption = edge.high_impact && edge.condition_met;
  return (
    <aside className="evidence-panel" aria-live="polite">
      <div className="evidence-heading">
        <p className="eyebrow">SELECTED CLAIM</p>
        <span className={disruption ? "severity-disruption" : "claim-badge"}>
          {disruption ? "DISRUPTION" : humanize(edge.claim_state)}
        </span>
      </div>
      <h2>
        {nodes.get(edge.from_node)?.label ?? edge.from_node}{" "}
        <span aria-hidden="true">→</span>{" "}
        {nodes.get(edge.to_node)?.label ?? edge.to_node}
      </h2>
      <p className="mechanism">{claimText(edge)}</p>
      {!edge.condition_met && (
        <p className="condition">
          <strong>Unmet condition:</strong> {edge.required_condition}
        </p>
      )}
      <dl className="claim-facts">
        <div>
          <dt>Certainty</dt>
          <dd>{humanize(edge.certainty)}</dd>
        </div>
        <div>
          <dt>Lag</dt>
          <dd>{humanize(edge.lag)}</dd>
        </div>
        <div>
          <dt>Strength</dt>
          <dd>{humanize(edge.strength)}</dd>
        </div>
        <div>
          <dt>Provenance</dt>
          <dd>{humanize(edge.provenance)}</dd>
        </div>
      </dl>
      <div className="evidence-list">
        <p className="micro-label">
          EVIDENCE · {edge.evidence.length} SOURCE
          {edge.evidence.length === 1 ? "" : "S"}
        </p>
        {edge.evidence.map((item) => (
          <a
            key={item.evidence_id}
            href={item.url}
            target="_blank"
            rel="noreferrer"
          >
            <span>{item.publisher}</span>
            <strong>{item.title}</strong>
            <small>
              {humanize(item.directness)} ·{" "}
              {item.supports ? "supports mechanism" : "contradicts"}
            </small>
          </a>
        ))}
      </div>
    </aside>
  );
}

type Filters = { certainty: string; horizon: string; category: string };

function matchesFilters(edge: RippleEdge, filters: Filters) {
  if (filters.certainty !== "all" && edge.certainty !== filters.certainty)
    return false;
  if (filters.horizon !== "all" && edge.lag !== filters.horizon) return false;
  if (filters.category !== "all" && categoryFor(edge) !== filters.category)
    return false;
  return true;
}

export function StoryPage() {
  const { storyId = "" } = useParams();
  const reducedMotion = useReducedMotion();
  const [revealDone, setRevealDone] = useState(reducedMotion);
  const [activeEdgeId, setActiveEdgeId] = useState<string>();
  const [activeBranch, setActiveBranch] = useState<number | null>(null);
  const [filters, setFilters] = useState<Filters>({
    certainty: "all",
    horizon: "all",
    category: "all",
  });
  const story = useQuery({
    queryKey: ["story", storyId],
    queryFn: () => getStory(storyId),
    enabled: Boolean(storyId),
  });
  const ripple = useQuery({
    queryKey: ["ripples", storyId],
    queryFn: () => getStoryRipples(storyId),
    enabled: Boolean(storyId),
  });

  useEffect(() => {
    if (reducedMotion) setRevealDone(true);
    if (revealDone || reducedMotion) return;
    const timer = window.setTimeout(() => setRevealDone(true), 6000);
    return () => window.clearTimeout(timer);
  }, [reducedMotion, revealDone]);

  const edges = ripple.data?.edges ?? [];
  const filteredEdges = edges.filter((edge) => matchesFilters(edge, filters));
  const nodeMap = useMemo(
    () =>
      new Map((ripple.data?.nodes ?? []).map((node) => [node.node_id, node])),
    [ripple.data?.nodes],
  );
  const pathIds =
    activeBranch === null
      ? (ripple.data?.main_path ?? [])
      : pathForBranch(ripple.data?.branches[activeBranch] ?? [], edges);
  const visiblePath = pathIds
    .map((id) => filteredEdges.find((edge) => edge.edge_id === id))
    .filter((edge): edge is RippleEdge => Boolean(edge));
  const activeEdge =
    filteredEdges.find((edge) => edge.edge_id === activeEdgeId) ??
    visiblePath[0] ??
    filteredEdges[0];
  const visibleCategories = Array.from(new Set(filteredEdges.map(categoryFor)));

  if (story.isPending || ripple.isPending)
    return (
      <main className="story-loading">
        <p className="eyebrow">ASSEMBLING SOURCED PATHWAY</p>
        <div className="pulse-ring" />
      </main>
    );
  if (story.isError || ripple.isError)
    return (
      <main className="state-page" role="alert">
        <p className="eyebrow">API ERROR</p>
        <h1>The story pathway could not be loaded.</h1>
        <p>{story.error?.message ?? ripple.error?.message}</p>
        <Link to="/">Return to feed</Link>
      </main>
    );
  if (!story.data || !ripple.data) return null;

  if (edges.length === 0) {
    return (
      <main className="state-page">
        <p className="eyebrow">NO PUBLISHABLE RIPPLE</p>
        <h1>{story.data.headline}</h1>
        <p>
          No sourced causal claim passed the deterministic publication policy
          for this event.
        </p>
        <Link to="/">Return to feed</Link>
      </main>
    );
  }

  return (
    <main className="story-page">
      {!revealDone && (
        <section className="reveal-overlay" aria-label="Causal pathway reveal">
          <p className="eyebrow">
            TRACE 01 · {story.data.fixture ? "FIXTURE" : "LIVE"}
          </p>
          <h1>{story.data.headline}</h1>
          <p className="reveal-origin">
            {story.data.origin_location} <span>→</span> sourced mechanisms{" "}
            <span>→</span> conditional outcomes
          </p>
          <div className="reveal-progress">
            <i />
          </div>
          <button onClick={() => setRevealDone(true)}>Skip reveal</button>
        </section>
      )}

      <section className="story-hero">
        <Link to="/" className="back-link">
          ← Feed
        </Link>
        <p className="eyebrow">
          {story.data.domain} · {story.data.event_status.replaceAll("_", " ")} ·{" "}
          {story.data.fixture ? "FIXTURE" : "VERIFIED"}
        </p>
        <h1>{story.data.headline}</h1>
        <p>
          {story.data.sources.length} representative source
          {story.data.sources.length === 1 ? "" : "s"} · mapped to{" "}
          {story.data.mapped_nodes.map(humanize).join(", ")}
        </p>
      </section>

      <section className="explorer-layout">
        <div className="map-column">
          <GlobeScene
            originLocation={story.data.origin_location}
            reducedMotion={reducedMotion}
            activeCategory={activeEdge ? categoryFor(activeEdge) : "supply"}
            visibleCategories={visibleCategories}
          />
          <div className="filters" aria-label="Ripple filters">
            <label>
              Certainty
              <select
                aria-label="Certainty"
                value={filters.certainty}
                onChange={(event) =>
                  setFilters({ ...filters, certainty: event.target.value })
                }
              >
                <option value="all">All</option>
                <option value="established">Established</option>
                <option value="emerging">Emerging</option>
                <option value="speculative">Speculative</option>
              </select>
            </label>
            <label>
              Time horizon
              <select
                aria-label="Time horizon"
                value={filters.horizon}
                onChange={(event) =>
                  setFilters({ ...filters, horizon: event.target.value })
                }
              >
                <option value="all">All</option>
                <option value="immediate">Immediate</option>
                <option value="medium">Medium</option>
                <option value="long">Long</option>
              </select>
            </label>
            <label>
              Consequence
              <select
                aria-label="Consequence"
                value={filters.category}
                onChange={(event) =>
                  setFilters({ ...filters, category: event.target.value })
                }
              >
                <option value="all">All</option>
                {(
                  [
                    "markets",
                    "costs",
                    "policy",
                    "supply",
                  ] as ConsequenceCategory[]
                ).map((category) => (
                  <option key={category}>{category}</option>
                ))}
              </select>
            </label>
          </div>
          <p className="filter-result" role="status">
            Showing {filteredEdges.length} of {edges.length} sourced claims.
          </p>
        </div>

        <section className="causal-column" aria-label="Causal pathway explorer">
          <div className="rail-heading">
            <div>
              <p className="eyebrow">ACTIVE CAUSAL RAIL</p>
              <h2>
                {activeBranch === null
                  ? "Primary pathway"
                  : `Branch ${activeBranch + 1}`}
              </h2>
            </div>
            <span>{visiblePath.length} HOPS</span>
          </div>
          <ol className="causal-rail">
            {visiblePath.map((edge, index) => (
              <li key={edge.edge_id}>
                <button
                  className={
                    activeEdge?.edge_id === edge.edge_id ? "active" : ""
                  }
                  onClick={() => setActiveEdgeId(edge.edge_id)}
                >
                  <span className="hop-index">0{index + 1}</span>
                  <span>
                    <strong>
                      {nodeMap.get(edge.to_node)?.label ??
                        humanize(edge.to_node)}
                    </strong>
                    <small>
                      {humanize(edge.claim_state)} · {humanize(edge.lag)}
                    </small>
                  </span>
                  <span aria-hidden="true">→</span>
                </button>
              </li>
            ))}
          </ol>
          {visiblePath.length === 0 && (
            <p className="no-filter-results">
              No claims match these filters. The graph has not been altered.
            </p>
          )}
          {ripple.data.branches.length > 0 && (
            <div className="branch-list">
              <p className="micro-label">ALTERNATE BRANCHES</p>
              {ripple.data.branches.map((branch, index) => {
                const edge = edges.find((item) => item.edge_id === branch[0]);
                return (
                  <button
                    key={branch.join("-")}
                    aria-pressed={activeBranch === index}
                    onClick={() => {
                      setActiveBranch(index);
                      setActiveEdgeId(branch[0]);
                    }}
                  >
                    Explore branch:{" "}
                    {edge
                      ? (nodeMap.get(edge.to_node)?.label ??
                        humanize(edge.to_node))
                      : index + 1}
                  </button>
                );
              })}
              <button
                aria-pressed={activeBranch === null}
                onClick={() => {
                  setActiveBranch(null);
                  setActiveEdgeId(undefined);
                }}
              >
                Return to primary pathway
              </button>
            </div>
          )}
        </section>

        {activeEdge && <EvidencePanel edge={activeEdge} nodes={nodeMap} />}
      </section>

      <section className="text-chain" aria-labelledby="text-chain-title">
        <div>
          <p className="eyebrow">KEYBOARD & TEXT EQUIVALENT</p>
          <h2 id="text-chain-title">Sourced claim chain</h2>
        </div>
        <ol>
          {filteredEdges.map((edge) => (
            <li key={edge.edge_id}>
              <button onClick={() => setActiveEdgeId(edge.edge_id)}>
                <strong>
                  {nodeMap.get(edge.from_node)?.label} →{" "}
                  {nodeMap.get(edge.to_node)?.label}
                </strong>
                <span>{claimText(edge)}</span>
                <small>
                  Evidence:{" "}
                  {edge.evidence
                    .map((item) => `${item.publisher}, ${item.title}`)
                    .join("; ")}
                </small>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
