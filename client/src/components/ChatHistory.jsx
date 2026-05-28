import React from "react";

export default function ChatHistory({ history }) {
  if (history.length === 0) return null;

  return (
    <div className="chat-history">
      <h3 className="chat-title">Chat History</h3>
      {history.map(({ q, a }, idx) => (
        <div key={idx} className="chat-entry">
          <p><b>Q:</b> {q}</p>
          <p><b>A:</b> {a}</p>
        </div>
      ))}
    </div>
  );
}
