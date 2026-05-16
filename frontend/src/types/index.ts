export interface Member {
  id: number;
  name: string;
  filename: string;

  developer_summary: string;
  skills: string[];
  domain_focus: string[];
  compatibility_insights: Record<string, string>;

  is_senior: boolean;
  priority: number;
  must_assign: boolean;
  pinned_project_id: number | null;
  forbidden_project_ids: number[];
}

export interface Project {
  id: number;
  title: string;
  filename: string;

  mission_statement: string;
  technical_intent: string;
  required_skills: string[];
  compatibility_insights: Record<string, string>;

  priority: number;
}

export interface Allocation {
  candidate_id: number;
  project_id: number;
  fit_score: number;
  reasons: string[];
}

export interface IngestionError {
  id: number;
  filename: string;
  file_type: string;
  error_message: string;
  occurred_at: string;
}

export interface TraceLog {
  id: string;
  timestamp: string;
  node: string;
  message: string;
  latency?: number;
  meta?: any;
}

export interface Bottleneck {
  project_id: number;
  project_title: string;
  health_score: number;
  critical_skills: string[];
  explanation: string;
  is_at_risk: boolean;
}

export interface WhatIfRequest {
  candidate_id: number;
  source_project_id?: number;
  target_project_id: number;
}

export interface WhatIfResponse {
  impact_on_source?: string;
  impact_on_target?: string;
  net_verdict?: 'positive' | 'neutral' | 'negative';
  reasoning?: string;

  insight: string;
  source_score_impact: number;
  target_score_impact: number;
}
