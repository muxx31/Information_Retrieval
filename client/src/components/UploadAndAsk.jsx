import React, { useState } from "react";
import api from "../api";
import ChatHistory from "./ChatHistory";

export default function UploadAndAsk() {
  const [file, setFile] = useState(null);
  const [uploadMsg, setUploadMsg] = useState("");
  const [uploading, setUploading] = useState(false);

  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [history, setHistory] = useState([]);
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [error, setError] = useState("");

  // Upload handler
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadMsg("Please select a PDF file.");
      return;
    }
    setUploadMsg("");
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadMsg(res.data.message);
    } catch (err) {
      setUploadMsg(err.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  // Ask handler
  const handleAsk = async (e) => {
    e.preventDefault();
    setError("");
    setAnswer("");
    if (!query.trim()) {
      setError("Please enter a question.");
      return;
    }
    setLoadingAnswer(true);

    try {
      const res = await api.post("/ask", { query });
      setAnswer(res.data.answer);
      setHistory([{ q: query, a: res.data.answer }, ...history]);
      setQuery("");
    } catch (err) {
      setError(err.response?.data?.error || "Failed to get answer.");
    } finally {
      setLoadingAnswer(false);
    }
  };

  return (
    <div className="container">
      <h2 style={{ textAlign: "center", marginBottom: "2rem" }}>
        Upload PDF & Ask Questions
      </h2>

      {/* Upload Card */}
      <div style={cardStyle}>
        <h3>Upload PDF</h3>
        <form onSubmit={handleUpload}>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files[0])}
            style={{ marginBottom: "1rem" }}
          />
          <br />
          <button
            type="submit"
            disabled={uploading}
            className="btn btn-blue"
            style={{ minWidth: "120px" }}
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </form>
        {uploadMsg && <p style={{ marginTop: "1rem" }}>{uploadMsg}</p>}
      </div>

      {/* Ask Card */}
      <div style={cardStyle}>
        <h3>Ask a Question</h3>
        <form onSubmit={handleAsk}>
          <textarea
            rows={4}
            className="text-input"
            placeholder="Ask something about your uploaded PDF..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="submit"
            disabled={loadingAnswer}
            className="btn btn-green"
            style={{ marginTop: "1rem", minWidth: "120px" }}
          >
            {loadingAnswer ? "Processing..." : "Ask"}
          </button>
        </form>

        {error && (
          <p style={{ color: "red", marginTop: "0.8rem", fontWeight: "600" }}>
            {error}
          </p>
        )}

        {answer && !loadingAnswer && (
          <div className="answer-box" style={{ marginTop: "1rem" }}>
            <strong>Answer:</strong> {answer}
          </div>
        )}

        <ChatHistory history={history} />
      </div>
    </div>
  );
}

const cardStyle = {
  backgroundColor: "#f9f9f9",
  padding: "1.5rem",
  borderRadius: "10px",
  boxShadow: "0 6px 15px rgba(0,0,0,0.1)",
  marginBottom: "2rem",
};
