import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

export const api = createClient<paths>({ baseUrl: "/api" });

export type FeedItem = components["schemas"]["FeedItemResponse"];
export type StoryDetail = components["schemas"]["StoryDetailResponse"];
export type Ripple = components["schemas"]["StoryRippleResponse"];
export type RippleEdge = components["schemas"]["StoryRippleEdgeResponse"];
export type RippleNode = components["schemas"]["RippleNodeResponse"];
export type Evidence = components["schemas"]["EvidenceResponse"];

function errorMessage(error: unknown, fallback: string) {
  if (typeof error === "object" && error && "detail" in error) {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

export async function getFeed(cursor?: string, domain = "energy") {
  const { data, error, response } = await api.GET("/feed", {
    params: { query: { domain, limit: 3, cursor } },
  });
  if (!data)
    throw new Error(
      errorMessage(error, `Feed request failed (${response.status})`),
    );
  return data;
}

export async function getStory(storyId: string) {
  const { data, error, response } = await api.GET("/story/{story_id}", {
    params: { path: { story_id: storyId } },
  });
  if (!data)
    throw new Error(
      errorMessage(error, `Story request failed (${response.status})`),
    );
  return data;
}

export async function getStoryRipples(storyId: string, depth = 2) {
  const { data, error, response } = await api.GET("/story/{story_id}/ripples", {
    params: { path: { story_id: storyId }, query: { depth } },
  });
  if (!data)
    throw new Error(
      errorMessage(error, `Ripple request failed (${response.status})`),
    );
  return data;
}
