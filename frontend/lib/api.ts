import {
  DocumentDetail,
  DocumentSummary,
  HealthResponse,
  IndexResponse,
  QueryResponse,
  UploadResponse,
} from "@/types";


const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";


async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail ?? detail;
    } catch {
      // Fall back to the HTTP status text when the backend does not return JSON.
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}


export const api = {
  health: () => request<HealthResponse>("/health"),
  listDocuments: () => request<DocumentSummary[]>("/documents"),
  getDocument: (documentId: string) => request<DocumentDetail>(`/documents/${documentId}`),
  upload: async (files: File[]) => {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }
    return request<UploadResponse>("/upload", {
      method: "POST",
      body: formData,
    });
  },
  buildIndex: (documentIds?: string[]) =>
    request<IndexResponse>("/index", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids: documentIds?.length ? documentIds : null }),
    }),
  query: (payload: {
    question: string;
    top_k?: number;
    selected_document_ids?: string[];
    include_debug?: boolean;
  }) =>
    request<QueryResponse>("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  deleteDocument: (documentId: string) =>
    request<{ message: string; deleted_document_id: string }>(`/documents/${documentId}`, {
      method: "DELETE",
    }),
};
