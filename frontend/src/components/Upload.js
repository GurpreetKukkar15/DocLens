import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload as UploadIcon, CheckCircle, AlertCircle } from "lucide-react";
import axios from "axios";

const API = (process.env.REACT_APP_API_URL || "http://localhost:8000") + "/api";

function Upload() {
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [error, setError] = useState("");

  const onDrop = useCallback(async (acceptedFiles) => {
    setUploading(true);
    setError("");

    for (const file of acceptedFiles) {
      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await axios.post(`${API}/upload`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 300000
        });

        setUploadedFiles(prev => [...prev, {
          name: file.name,
          pages: response.data.pages,
          chunks: response.data.chunks,
          status: "success"
        }]);

      } catch (err) {
        setUploadedFiles(prev => [...prev, {
          name: file.name,
          status: "error",
          error: err.response?.data?.detail || "Upload failed"
        }]);
      }
    }
    setUploading(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: true
  });

  return (
    <div className="upload-container">
      <h2>Upload Documents</h2>

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? "active" : ""}`}
      >
        <input {...getInputProps()} />
        <UploadIcon size={32} />
        {isDragActive
          ? <p>Drop PDFs here...</p>
          : <p>Drag & drop PDFs here, or click to select</p>
        }
        {uploading && <p className="uploading-text">Uploading...</p>}
      </div>

      {error && (
        <div className="error-message">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div className="uploaded-list">
          {uploadedFiles.map((f, i) => (
            <div key={i} className={`upload-item ${f.status}`}>
              {f.status === "success"
                ? <CheckCircle size={16} />
                : <AlertCircle size={16} />
              }
              <span>{f.name}</span>
              {f.status === "success" &&
                <span className="meta">{f.pages} pages · {f.chunks} chunks</span>
              }
              {f.status === "error" &&
                <span className="meta">{f.error}</span>
              }
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Upload;
