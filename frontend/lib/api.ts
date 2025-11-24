const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

import {
  Project,
  Crawl,
  CrawlSummary,
  IssueTypeGroup,
  Issue
} from "./types";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status} ${res.statusText} en ${path}`);
  }
  return res.json();
}

// Projects
export async function getProjects(): Promise<Project[]> {
  return api<Project[]>("/projects");
}

export async function getProject(projectId: string | number): Promise<Project> {
  return api<Project>(`/projects/${projectId}`);
}

// Crawls
export async function getCrawls(projectId: string | number): Promise<Crawl[]> {
  return api<Crawl[]>(`/projects/${projectId}/crawls`);
}

export async function getLatestCrawlSummary(projectId: string | number): Promise<CrawlSummary> {
  return api<CrawlSummary>(`/projects/${projectId}/crawls/latest/summary`);
}

// Issues
export async function getIssuesByType(crawlId: number): Promise<IssueTypeGroup[]> {
  return api<IssueTypeGroup[]>(`/crawls/${crawlId}/issues/by-type`);
}

export async function getIssuesForType(
  crawlId: number,
  issueCode: string
): Promise<Issue[]> {
  return api<Issue[]>(`/crawls/${crawlId}/issues/${issueCode}`);
}

export async function updateIssue(
  issueId: number,
  payload: Partial<Pick<Issue, "implemented" | "status" | "comment">>
): Promise<Issue> {
  return api<Issue>(`/issues/${issueId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}
