import "./ResultCard.css";

function ResultCard({ prediction }) {
  const isRansomware = prediction === "Ransomware";

  return (
    <div className={`result-card ${isRansomware ? "danger" : "safe"}`}>
      <div className="result-icon">{isRansomware ? "⚠" : "✓"}</div>
      <h2 className="result-label">{prediction}</h2>
      <p className="result-desc">
        {isRansomware
          ? "This file has been classified as ransomware. Do NOT execute it."
          : "This file appears to be benign. No ransomware behaviour detected."}
      </p>
    </div>
  );
}

export default ResultCard;
