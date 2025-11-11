import React, { useState } from "react";

export default function ModelSelector() {
  const [model, setModel] = useState("GPT-4");
  const models = ["GPT-4", "Gemini", "Grok"];

  return (
    <div style={{
      display: "flex", gap: 10, background: "#f4fbff",
      padding: 6, borderRadius: 12, boxShadow: "0 2px 8px #d6ebff"
    }}>
      {models.map((m) => (
        <button
          key={m}
          onClick={() => setModel(m)}
          style={{
            padding: "8px 12px",
            borderRadius: 10,
            border: "1px solid #d7e7ff",
            background: model === m ? "#4ca2fd" : "#ffffff",
            color: model === m ? "#fff" : "#245",
            fontWeight: 700,
            cursor: "pointer"
          }}
        >
          {m}
        </button>
      ))}
    </div>
  );
}
