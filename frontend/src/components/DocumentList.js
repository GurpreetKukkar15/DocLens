import { useState, useEffect } from "react";
import { FileText, RefreshCw } from "lucide-react";
import axios from "axios";

const API = (process.env.REACT_APP_API_URL || "http://localhost:8000") + "/api";

function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/documents`);
      setDocuments(response.data.documents);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="doclist-container">
      <div className="doclist-header">
        <h2>Uploaded Documents ({documents.length})</h2>
        <button onClick={fetchDocuments} className="refresh-button">
          <RefreshCw size={14} />
        </button>
      </div>

      {loading && <p className="loading-text">Loading...</p>}

      {documents.length === 0 && !loading ? (
        <p className="no-docs">No documents uploaded yet</p>
      ) : (
        <ul className="doc-list">
          {documents.map((doc, i) => (
            <li key={i} className="doc-item">
              <FileText size={14} />
              <span>{doc}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default DocumentList;
