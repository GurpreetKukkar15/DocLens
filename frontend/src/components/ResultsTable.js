import { FileText } from "lucide-react";

function ResultsTable({ results }) {
  const relevant = results.filter(
    r => r.answer !== "No relevant content found" && 
         r.answer !== "Not found in this document."
  );

  const irrelevant = results.filter(
    r => r.answer === "No relevant content found" || 
         r.answer === "Not found in this document."
  );

  return (
    <div className="results-container">
      <h2>Document Answers</h2>
      <p className="results-meta">
        {relevant.length} of {results.length} documents contained relevant information
      </p>

      <div className="table-wrapper">
        <table className="results-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Answer</th>
              <th>Citation</th>
            </tr>
          </thead>
          <tbody>
            {relevant.map((r, i) => (
              <tr key={i}>
                <td>
                  <div className="doc-name">
                    <FileText size={14} />
                    <span>{r.filename}</span>
                  </div>
                </td>
                <td>{r.answer}</td>
                <td>
                  <span className="citation-badge">{r.citation}</span>
                </td>
              </tr>
            ))}
            {irrelevant.map((r, i) => (
              <tr key={`irr-${i}`} className="irrelevant-row">
                <td>
                  <div className="doc-name">
                    <FileText size={14} />
                    <span>{r.filename}</span>
                  </div>
                </td>
                <td className="not-found">Not found in this document</td>
                <td>—</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ResultsTable;