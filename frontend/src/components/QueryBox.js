import { Search } from "lucide-react";
import axios from "axios";

const API = (process.env.REACT_APP_API_URL || "http://localhost:8000") + "/api";

function QueryBox({ query, setQuery, setResults, setThemes, setLoading, loading }) {
  
  const handleQuery = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setResults(null);
    setThemes("");

    try {
      const response = await axios.post(`${API}/query`, { query });
      setResults(response.data.doc_answers);
      setThemes(response.data.themes);
    } catch (err) {
      alert(err.response?.data?.detail || "Query failed");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleQuery();
  };

  return (
    <div className="querybox-container">
      <h2>Ask a Question</h2>
      <div className="query-input-row">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="e.g. What are the penalties for regulatory violations?"
          className="query-input"
          disabled={loading}
        />
        <button
          onClick={handleQuery}
          disabled={loading}
          className="query-button"
        >
          <Search size={18} />
          {loading ? "Searching..." : "Search"}
        </button>
      </div>
    </div>
  );
}

export default QueryBox;
