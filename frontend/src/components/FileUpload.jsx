import { useRef } from "react";
import "./FileUpload.css";

function FileUpload({ file, onFileChange, onSubmit, onReset, loading, disabled }) {
  const inputRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) onFileChange(dropped);
  };

  const handleDragOver = (e) => e.preventDefault();

  return (
    <div className="upload-card">
      <div
        className="dropzone"
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".exe"
          hidden
          onChange={(e) => onFileChange(e.target.files[0])}
        />
        {file ? (
          <div className="file-info">
            <span className="file-icon">&#128196;</span>
            <span className="file-name">{file.name}</span>
            <span className="file-size">
              ({(file.size / 1024).toFixed(1)} KB)
            </span>
          </div>
        ) : (
          <div className="dropzone-placeholder">
            <span className="upload-icon">&#8682;</span>
            <p>
              Drag &amp; drop a <strong>.exe</strong> file here, or click to
              browse
            </p>
          </div>
        )}
      </div>

      <div className="upload-actions">
        <button
          className="btn btn-primary"
          onClick={onSubmit}
          disabled={disabled}
        >
          {loading ? "Analysing…" : "Analyse File"}
        </button>
        {file && (
          <button className="btn btn-ghost" onClick={onReset} disabled={loading}>
            Clear
          </button>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
