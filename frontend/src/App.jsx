import { useState } from "react";
import FileUpload from "./components/FileUpload";
import ResultCard from "./components/ResultCard";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (selectedFile) => {
    setFile(selectedFile);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async () => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".exe")) {
      setError("Only .exe files are accepted.");
      return;
    }

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || `Server error (${response.status})`);
      }

      const data = await response.json();
      setResult(data.prediction);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>
          <span className="icon">&#128737;</span> Ransomware Detector
        </h1>
        <p className="subtitle">
          Upload a Windows <code>.exe</code> file to classify it as{" "}
          <strong>Benign</strong> or <strong>Ransomware</strong>.
        </p>
      </header>

      <main className="app-main">
        <FileUpload
          file={file}
          onFileChange={handleFileChange}
          onSubmit={handleSubmit}
          onReset={handleReset}
          loading={loading}
          disabled={!file || loading}
        />

        {error && (
          <div className="error-banner">
            <span>&#9888;</span> {error}
          </div>
        )}

        {loading && (
          <div className="loading">
            <div className="spinner" />
            <span>Analysing file&hellip;</span>
          </div>
        )}

        {result && <ResultCard prediction={result} />}
      </main>

      <footer className="app-footer">
        Ransomware Detection &mdash; Final Year Project
      </footer>
    </div>
  );
}

export default App;
