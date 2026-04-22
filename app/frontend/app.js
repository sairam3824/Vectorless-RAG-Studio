const uploadForm = document.getElementById("upload-form");
const uploadOutput = document.getElementById("upload-output");
const indexButton = document.getElementById("index-button");
const indexOutput = document.getElementById("index-output");
const queryForm = document.getElementById("query-form");
const queryResults = document.getElementById("query-results");
const answerEl = document.getElementById("answer");
const citationsEl = document.getElementById("citations");
const chunksEl = document.getElementById("chunks");

const safeJson = async (response) => {
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload;
};

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  uploadOutput.textContent = "Uploading documents...";

  const formData = new FormData();
  for (const file of document.getElementById("files").files) {
    formData.append("files", file);
  }

  try {
    const payload = await safeJson(
      await fetch("/ingest", {
        method: "POST",
        body: formData,
      }),
    );
    uploadOutput.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    uploadOutput.textContent = error.message;
  }
});

indexButton.addEventListener("click", async () => {
  indexOutput.textContent = "Building local retrieval artifacts...";
  try {
    const payload = await safeJson(
      await fetch("/index", {
        method: "POST",
      }),
    );
    indexOutput.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    indexOutput.textContent = error.message;
  }
});

queryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  queryResults.classList.remove("hidden");
  answerEl.textContent = "Running retrieval and generation...";
  citationsEl.innerHTML = "";
  chunksEl.innerHTML = "";

  const filenameFilter = document.getElementById("filename-filter").value.trim();
  const filetypeFilter = document.getElementById("filetype-filter").value.trim();
  const body = {
    question: document.getElementById("question").value.trim(),
    top_k: Number(document.getElementById("top-k").value),
    use_tfidf: document.getElementById("use-tfidf").checked,
    use_reranker: document.getElementById("use-reranker").checked,
    filters: {
      filename: filenameFilter || null,
      file_type: filetypeFilter || null,
    },
  };

  try {
    const payload = await safeJson(
      await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    );

    answerEl.textContent = payload.answer;
    citationsEl.innerHTML = payload.citations
      .map(
        (citation) =>
          `<li><strong>${citation.filename}</strong> <code>${citation.chunk_id}</code><br />${citation.snippet}</li>`,
      )
      .join("");

    chunksEl.innerHTML = payload.retrieved_chunks
      .map(
        (chunk) => `
          <article class="chunk">
            <div class="chunk-header">
              <span><strong>${chunk.filename}</strong> · ${chunk.file_type}</span>
              <span>score ${chunk.score.toFixed(4)}</span>
            </div>
            <div><code>${chunk.chunk_id}</code></div>
            <p>${chunk.text}</p>
          </article>
        `,
      )
      .join("");
  } catch (error) {
    answerEl.textContent = error.message;
  }
});
