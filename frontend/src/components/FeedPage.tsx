import { useInfiniteQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { getFeed } from "../api/client";

function StoryCard({
  story,
}: {
  story: Awaited<ReturnType<typeof getFeed>>["items"][number];
}) {
  const published = new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(story.published_at));

  return (
    <article className="story-card">
      <div className="story-meta">
        <span className="domain-chip">{story.domain}</span>
        <time dateTime={story.published_at}>{published}</time>
        <span>{story.origin_location}</span>
        {story.fixture && <span className="fixture-label">FIXTURE</span>}
      </div>
      <h2>
        <Link to={`/story/${story.story_id}`}>{story.headline}</Link>
      </h2>
      <div className="story-lower">
        <div>
          <p className="micro-label">REPRESENTATIVE SOURCES</p>
          <ul className="source-row" aria-label="Representative sources">
            {story.sources.slice(0, 3).map((source) => (
              <li key={source.url}>
                <a href={source.url} target="_blank" rel="noreferrer">
                  {source.outlet}
                </a>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="micro-label">WHY IT SURFACED</p>
          <p>{story.prominence_reasons.join(" · ")}</p>
        </div>
      </div>
      <Link className="story-action" to={`/story/${story.story_id}`}>
        Trace causal pathway <span aria-hidden="true">→</span>
      </Link>
    </article>
  );
}

export function FeedPage() {
  const [params, setParams] = useSearchParams();
  const domain = params.get("domain") ?? "energy";
  const feed = useInfiniteQuery({
    queryKey: ["feed", domain],
    queryFn: ({ pageParam }) => getFeed(pageParam, domain),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (page) => page.next_cursor ?? undefined,
  });
  const stories = feed.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <main className="feed-page">
      <section className="feed-intro">
        <div>
          <p className="eyebrow">GLOBAL ENERGY · CURATED FIXTURES</p>
          <h1>
            What happened.
            <br />
            <em>What it could set in motion.</em>
          </h1>
        </div>
        <p className="intro-copy">
          Every pathway separates a known mechanism from an event-specific
          outcome. Unmet conditions remain visible.
        </p>
      </section>

      <nav className="feed-controls" aria-label="Feed domain">
        <button
          aria-pressed={domain === "energy"}
          onClick={() => setParams({ domain: "energy" })}
        >
          Energy feed
        </button>
        <button
          aria-pressed={domain !== "energy"}
          onClick={() => setParams({ domain: "not-a-fixture" })}
        >
          Empty-state preview
        </button>
        {feed.isFetching && !feed.isPending && (
          <span role="status">Refreshing fixture feed…</span>
        )}
      </nav>

      {feed.isPending && (
        <section className="feed-skeleton" aria-label="Loading feed">
          <i />
          <i />
          <i />
        </section>
      )}
      {feed.isError && (
        <section className="state-card" role="alert">
          <p className="eyebrow">API unavailable</p>
          <h2>The feed could not be reached.</h2>
          <p>{feed.error.message}</p>
          <button onClick={() => void feed.refetch()}>Try again</button>
        </section>
      )}
      {!feed.isPending && !feed.isError && stories.length === 0 && (
        <section className="state-card empty-state">
          <p className="eyebrow">NO STORIES IN THIS VIEW</p>
          <h2>Start from an established mechanism.</h2>
          <p>
            The empty feed does not need invented headlines. Explore concepts
            grounded in the curated graph instead.
          </p>
          <div className="concept-links">
            <button onClick={() => setParams({ domain: "energy" })}>
              Oil price pathways
            </button>
            <button onClick={() => setParams({ domain: "energy" })}>
              Shipping disruption
            </button>
          </div>
        </section>
      )}
      <section className="story-list" aria-label="Story feed">
        {stories.map((story) => (
          <StoryCard key={story.story_id} story={story} />
        ))}
      </section>
      {feed.hasNextPage && (
        <button
          className="load-more"
          disabled={feed.isFetchingNextPage}
          onClick={() => void feed.fetchNextPage()}
        >
          {feed.isFetchingNextPage ? "Loading…" : "Load older stories"}
        </button>
      )}
    </main>
  );
}
