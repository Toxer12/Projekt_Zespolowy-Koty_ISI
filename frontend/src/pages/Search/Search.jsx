import { useState, useRef, useEffect } from "react";
import { appApi } from "../../api";
import "./Search.css";

function ScoreBar({ score }) {
  const pct = Math.round(score * 100);
  const cls  = pct >= 70 ? "high" : pct >= 40 ? "mid" : "low";
  return (
    <div className="score-wrap">
      <div className="score-bar">
        <div className={`score-fill score-fill--${cls}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="score-label">{pct}%</span>
    </div>
  );
}

function ResultItem({ result, index }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = result.text.length > 200;

  return (
    <div className="result-item" style={{ "--i": index }}>
      <div className="result-header">
        <div className="result-file">
          <span className="result-file-icon">
            {result.file_name?.endsWith('.pdf') ? '📄' : '📝'}
          </span>
          <span className="result-file-name">{result.file_name}</span>
          <span className="result-chunk">fragment #{result.chunk_index + 1}</span>
        </div>
        <ScoreBar score={result.score} />
      </div>
      <p className={`result-text ${expanded ? "expanded" : ""}`}>
        {result.text}
      </p>
      {isLong && (
        <button className="result-expand" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Zwiń ▲" : "Rozwiń ▼"}
        </button>
      )}
    </div>
  );
}

export default function Search() {
  const [query, setQuery]     = useState("");
  const [scope, setScope]     = useState("mine");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const inputRef              = useRef(null);
  const pollingRef            = useRef(null); // Keeps track of our background checking interval

  useEffect(() => { inputRef.current?.focus(); }, []);

  // Clear background timers instantly if the user leaves this view
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setResults(null);

    // Cancel old timers if a user clicks search repeatedly
    if (pollingRef.current) clearInterval(pollingRef.current);

    try {
      // 1. Ask Django to kick off the Celery task
      const res = await appApi.post("/documents/search/", {
        query: query.trim(),
        scope,
        n_results: 8,
      });

      const { task_id, status } = res.data;

      // 2. If it was successfully pushed to Celery, start polling
      if (status === "PENDING") {
        pollingRef.current = setInterval(async () => {
          try {
            const statusRes = await appApi.get(`/documents/search/status/${task_id}/`);
            const taskData = statusRes.data;

            if (taskData.status === "SUCCESS") {
              clearInterval(pollingRef.current);
              setResults(taskData); // Populates results layout cleanly
              setLoading(false);
            } else if (taskData.status === "FAILURE") {
              clearInterval(pollingRef.current);
              setError(taskData.error || "Wyszukiwanie nie powiodło się.");
              setLoading(false);
            }
          } catch (pollErr) {
            clearInterval(pollingRef.current);
            setError(pollErr.response?.data?.error || "Błąd sprawdzania statusu wyszukiwania.");
            setLoading(false);
          }
        }, 1200); // Check every 1.2 seconds
    } else {
  setError("Nieoczekiwana odpowiedź serwera.");
  setLoading(false);
}
    } catch (err) {
      setError(err.response?.data?.error || "Błąd wyszukiwania.");
      setLoading(false);
    }
  };

  // Only consider results valid to render if the background task successfully finished
  const displayResults = results?.status === "SUCCESS" && Array.isArray(results?.results) && results.results.length >= 0;

  return (
    <div className="page search-page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Wyszukiwanie</p>
          <h1 className="page-title">Wyszukiwanie semantyczne</h1>
        </div>
      </div>

      <div className="search-box">
        <div className="search-scope-tabs">
          {[["mine", "Moje projekty"], ["public", "Publiczne projekty"]].map(([val, label]) => (
            <button
              key={val}
              className={`scope-tab ${scope === val ? "active" : ""}`}
              onClick={() => { setScope(val); setResults(null); }}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="search-row">
          <div className="search-input-wrap">
            <span className="search-icon">⌕</span>
            <input
              ref={inputRef}
              className="search-input-field"
              type="text"
              placeholder={scope === "mine"
                ? "Zadaj pytanie o swoje dokumenty…"
                : "Szukaj w publicznych projektach…"}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            {query && (
              <button className="search-clear" onClick={() => { setQuery(""); setResults(null); }}>×</button>
            )}
          </div>
          <button className="search-btn" onClick={handleSearch} disabled={loading || !query.trim()}>
            {loading ? <span className="search-spinner" /> : "Szukaj"}
          </button>
        </div>
      </div>

      {error && <p className="search-error">{error}</p>}

      {/* Render result fields safely only when displayResults evaluations match true */}
      {displayResults && (
        <div className="results-section">
          <div className="results-meta">
            {results.total > 0
              ? <span>Znaleziono <strong>{results.total}</strong> {results.total === 1 ? "wynik" : "wyników"} dla <em>"{results.query}"</em></span>
              : <span>Brak wyników dla <em>"{results.query}"</em> — spróbuj innego zapytania.</span>
            }
          </div>
          <div className="results-list">
            {results.results.map((r, i) => (
              <ResultItem key={`${r.document_id}-${r.chunk_index}-${i}`} result={r} index={i} />
            ))}
          </div>
        </div>
      )}

      {!displayResults && !loading && (
        <div className="search-empty">
          <p className="search-empty-icon">⌕</p>
          <p className="search-empty-text">Wpisz zapytanie aby przeszukać dokumenty semantycznie.</p>
          <p className="search-empty-hint">Wyszukiwanie rozumie znaczenie — nie tylko słowa kluczowe.</p>
        </div>
      )}
    </div>
  );
}