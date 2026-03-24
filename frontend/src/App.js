import { useState } from "react";
import Upload from "./components/Upload";
import QueryBox from "./components/QueryBox";
import ResultsTable from "./components/ResultsTable";
import ThemePanel from "./components/ThemePanel";
import DocumentList from "./components/DocumentList";
import "./App.css";

function App() {
  const [results, setResults] = useState(null);
  const [themes, setThemes] = useState("");
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");

  return (
    <div className="app">
      <header className="header">
        <h1>DocLens</h1>
        <p>Multi-document research and theme identification</p>
      </header>

      <main className="main">
        <div className="left-panel">
          <Upload />
          <DocumentList />
        </div>

        <div className="right-panel">
          <QueryBox
            query={query}
            setQuery={setQuery}
            setResults={setResults}
            setThemes={setThemes}
            setLoading={setLoading}
            loading={loading}
          />
          {loading && (
            <div className="loading">
              Analyzing {results ? results.length : "all"} documents...
            </div>
          )}
          {results && <ResultsTable results={results} />}
          {themes && <ThemePanel themes={themes} />}
        </div>
      </main>
    </div>
  );
}

export default App;