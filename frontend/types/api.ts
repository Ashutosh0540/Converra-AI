export type Role = "ADMIN" | "MANAGER" | "AGENT" | "VIEWER";
export type AgentType = "FAQ" | "LEAD" | "SCHEDULING" | "SUMMARY" | "ESCALATION";
export type ConversationStatus = "ACTIVE" | "ESCALATED" | "CLOSED";
export type EscalationStatus = "PENDING" | "ASSIGNED" | "ACCEPTED" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";
export type EscalationPriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type DocumentStatus = "PROCESSING" | "READY" | "FAILED";
export type WorkflowStage = "ROUTING" | "CLASSIFYING" | "RETRIEVING" | "GENERATING" | "COMPLETE" | "ERROR" | string;

export interface User {
  id: string;
  organization_id: string;
  full_name: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at?: string;
}

export interface Organization {
  id: string;
  name: string;
  industry: string;
  subscription_plan: string;
  created_at?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface KnowledgeDocument {
  id: string;
  organization_id: string;
  uploader_id: string;
  filename: string;
  content_type: string;
  file_size: number;
  source: string;
  status: DocumentStatus;
  upload_time: string;
  chunk_count: number;
  error_message?: string | null;
}

export interface Citation {
  document_id: string;
  document: string;
  page: number;
  chunk_number: number;
  source: string;
}

export interface AIResponse {
  conversation_id: string;
  agent: AgentType;
  status: ConversationStatus;
  workflow_stage: WorkflowStage;
  message: string;
  confidence: number;
  citations: Citation[];
  retrieved_sources: Citation[];
  guardrail_result: Record<string, unknown>;
  escalation_decision: Record<string, unknown>;
  structured_data: Record<string, unknown>;
  escalation_state: Record<string, unknown>;
}

export interface Conversation {
  id: string;
  organization_id: string;
  user_id: string;
  status: ConversationStatus;
  workflow_stage: WorkflowStage;
  active_agent?: AgentType | null;
  started_at: string;
  ended_at?: string | null;
  memory: Array<{ role: string; content: string; timestamp?: string }>;
  retrieved_documents: Array<Record<string, unknown>>;
  escalation_state: Record<string, unknown>;
  human_mode: boolean;
  human_assignee_id?: string | null;
}

export interface EscalationQueueItem {
  id: string;
  conversation_id: string;
  organization_id: string;
  customer: string;
  customer_id: string;
  assigned_agent?: string | null;
  assigned_agent_id?: string | null;
  escalation_reason: string;
  confidence_score: number;
  timestamp: string;
  priority: EscalationPriority;
  status: EscalationStatus;
  source_channel: string;
  source_agent?: string | null;
  human_mode: boolean;
}

export interface EscalationQueueResponse {
  items: EscalationQueueItem[];
}

export interface EscalationDetailResponse {
  escalation: EscalationQueueItem;
  audit_trail: Array<{
    id: string;
    escalation_id: string;
    actor_user_id?: string | null;
    action: string;
    notes?: string | null;
    before_state: Record<string, unknown>;
    after_state: Record<string, unknown>;
    created_at: string;
  }>;
  assist_bundle: {
    summary: string;
    suggested_reply: string;
    knowledge_articles: Array<Record<string, unknown>>;
    previous_history: Array<Record<string, unknown>>;
    suggested_next_actions: string[];
  };
}

export interface VoiceSessionStart {
  session_id: string;
  conversation_id: string;
  websocket_url: string;
  status: ConversationStatus;
  active_agent?: AgentType | null;
  workflow_stage: WorkflowStage;
}

export interface VoiceTranscript {
  id: string;
  session_id: string;
  role: string;
  content: string;
  partial: boolean;
  agent?: string | null;
  created_at: string;
}

export interface VoiceSessionEnd {
  session_id: string;
  conversation_id: string;
  status: ConversationStatus;
  ended_at: string;
}

export interface VoiceSessionListItem {
  id: string;
  conversation_id: string;
  active_agent?: AgentType | null;
  workflow_stage: WorkflowStage;
  status: ConversationStatus;
  is_active: boolean;
  connection_count: number;
  last_seen_at?: string | null;
  created_at: string;
}

export interface DashboardMetric {
  label: string;
  value: string;
  trend: string;
}

export interface KnowledgeSearchResult {
  text: string;
  score: number;
  metadata: Record<string, unknown>;
  citation: Citation;
}

export interface KnowledgeSearchResponse {
  query: string;
  results: KnowledgeSearchResult[];
}

export interface EscalationActionResponse {
  escalation_id: string;
  status: EscalationStatus;
  assigned_agent_id?: string | null;
  human_mode: boolean;
  message: string;
}
