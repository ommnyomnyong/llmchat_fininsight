// src/components/ChatInput.jsx
import React, { useState } from "react";

export default function ChatInput({ onSend, loading }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text);
    setText("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        gap: 8,
        padding: "10px 14px",
        background: "#fff",
        borderTop: "1px solid #e5e7eb",
      }}
    >
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
        placeholder="메시지를 입력하세요..."
        style={{
          flex: 1,
          border: "1px solid #cbd5e1",
          borderRadius: 8,
          padding: "10px 12px",
        }}
      />
      <button
        type="submit"
        disabled={loading}
        style={{
          background: loading ? "#93c5fd" : "#2563eb",
          color: "#fff",
          border: "none",
          borderRadius: 8,
          padding: "10px 14px",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "..." : "전송"}
      </button>
    </form>
  );
}
