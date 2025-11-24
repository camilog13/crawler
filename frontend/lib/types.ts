export type Severity = "critical" | "major" | "minor";

export interface Project {
  id: number;
  name: string;
  domain: string;
  created_at: string;
}

export interface Crawl {
  id: number;
  project_id: number;
  status: "running" | "finished" | "failed";
  site_health: number | null;
  started_at: string;
  finished_at: string | null;
}

export interface CrawlSummary {
  crawl: Crawl;
  total_urls: number;
  total_issues: number;
  issues_by_severity: Record<string, number>;
  issues_by_category: Record<string, number>;
  site_health: number;
}

export interface IssueTypeGroup {
  code: string;
  name: string;
  severity: Severity;
  category: string;
  count: number;
}

export interface Url {
  id: number;
  crawl_id: number;
  url: string;
  status_code: number | null;
  title: string | null;
  title_length: number | null;
  meta_description: string | null;
  meta_description_length: number | null;
  word_count: number | null;
  performance_score_mobile: number | null;
  lcp: number | null;
  cls: number | null;
  tbt: number | null;
}

export interface IssueDetailsPayload {
  url: string;
  issue_code: string;
  issue_name: string;
  severity: Severity;
  category: string;
  hint?: string;
  [key: string]: any;
}

export interface Issue {
  id: number;
  crawl_id: number;
  url_id: number;
  issue_type_id: number;
  implemented: boolean;
  status: "pending" | "in_progress" | "done";
  comment: string | null;
  created_at: string;
  updated_at: string;
  details: string;
}
