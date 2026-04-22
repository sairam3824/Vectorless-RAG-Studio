export interface HealthResponse {
  status: string;
  documents: number;
  pages: number;
  sections: number;
  index_ready: boolean;
}

export interface DocumentSummary {
  id: string;
  filename: string;
  file_type: string;
  title: string;
  page_count: number;
  section_count: number;
  size_bytes: number;
  indexing_status: string;
  last_indexed_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface PageRecord {
  id: string;
  page_number: number;
  label: string;
  title: string | null;
  snippet: string;
  text: string;
  word_count: number;
  token_count: number;
}

export interface SectionRecord {
  id: string;
  title: string;
  normalized_title: string;
  heading_level: number;
  page_number: number;
  start_page: number;
  end_page: number;
  parent_section_id: string | null;
  heading_path: string;
  snippet: string;
  text: string;
  word_count: number;
  token_count: number;
}

export interface DocumentDetail extends DocumentSummary {
  pages: PageRecord[];
  sections: SectionRecord[];
}

export interface Citation {
  document_id: string;
  filename: string;
  page_number: number;
  section_title: string | null;
  heading_path: string | null;
  snippet: string;
  unit_type: string;
  unit_id: string;
}

export interface RetrievedPassage {
  unit_id: string;
  document_id: string;
  filename: string;
  document_title: string;
  file_type: string;
  unit_type: string;
  page_number: number;
  start_page: number;
  end_page: number;
  section_title: string | null;
  heading_level: number | null;
  heading_path: string | null;
  title: string;
  snippet: string;
  text: string;
  score: number;
  bm25_score: number;
  tfidf_score: number;
  keyword_score: number;
  title_score: number;
  exact_match_score: number;
  matched_terms: string[];
}

export interface QueryDebug {
  normalized_query: string;
  query_terms: string[];
  candidate_count: number;
  context_preview: string;
}

export interface QueryResponse {
  question: string;
  answer: string;
  answer_status: string;
  llm_used: boolean;
  citations: Citation[];
  retrieved_chunks: RetrievedPassage[];
  retrieval_summary: {
    candidate_count: number;
    returned_count: number;
    indexed_document_ids: string[];
    selected_document_ids: string[];
  };
  selected_document_ids: string[];
  debug: QueryDebug | null;
}

export interface ChatMessage {
  id: string;
  question: string;
  answer: string;
  citations: Citation[];
  retrievalSummary: QueryResponse["retrieval_summary"];
  answerStatus: string;
  createdAt: string;
}

export interface UploadResponse {
  documents: Array<{
    document_id: string;
    filename: string;
    file_type: string;
    page_count: number;
    section_count: number;
    indexing_status: string;
  }>;
  skipped: Array<{ filename: string; reason: string }>;
  total_uploaded: number;
}

export interface IndexResponse {
  message: string;
  indexed_document_ids: string[];
  document_count: number;
  page_count: number;
  section_count: number;
  retrieval_unit_count: number;
  tfidf_enabled: boolean;
  created_at: string;
}
