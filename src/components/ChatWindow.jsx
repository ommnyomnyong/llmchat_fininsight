import React, { useState, useEffect, useMemo, useRef } from "react";
import { FaBrain, FaPaperPlane } from "react-icons/fa";
import { SiOpenai, SiGooglegemini } from "react-icons/si";

// 사용할 모델 목록
const models = [
  { id: "gpt", name: "GPT", icon: <SiOpenai size={14} /> },
  { id: "gemini", name: "Gemini", icon: <SiGooglegemini size={14} /> },
];

function fmtTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
}

function fmtYMD(iso) {
  const d = new Date(iso);
  return `${d.getFullYear()}-${(d.getMonth() + 1)
    .toString()
    .padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")}`;
}

export default function ChatWindow({ messages = [], onSend }) {
  const [model, setModel] = useState("gpt");
  const [aiOpen, setAiOpen] = useState(false);
  const [deepResearch, setDeepResearch] = useState(false);
  const [text, setText] = useState("");
  const inputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const selected = useMemo(() => models.find((m) => m.id === model), [model]);

  const grouped = useMemo(() => {
    const g = {};
    for (const m of messages) {
      const key = fmtYMD(m.createdAt);
      g[key] = g[key] || [];
      g[key].push(m);
    }
    return Object.keys(g).map((k) => ({ date: k, items: g[k] }));
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const t = text.trim();
    if (!t) return;
    if (!onSend) {
      console.error("❌ onSend 함수가 전달되지 않았습니다!");
      return;
    }
    setText("");
    onSend(t, model, deepResearch);
  };

  return (
    <div
      style={{
        flex: 1,
        display: "grid",
        gridTemplateRows: "auto 1fr auto",
        height: "100%",
      }}
    >
      {/* 상단바 */}
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          gap: 8,
          padding: "10px 14px",
          background: "#fff",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        {/* AI 변경 */}
        <div style={{ position: "relative" }}>
          <button onClick={() => setAiOpen((v) => !v)} title="AI 변경" style={aiBtn}>
            {selected.icon}
          </button>
          {aiOpen && (
            <div style={aiMenu}>
              {models.map((m) => (
                <div
                  key={m.id}
                  onClick={() => {
                    setModel(m.id);
                    setAiOpen(false);
                  }}
                  style={aiRow}
                >
                  {m.icon}
                  <span>{m.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 심층 리서치 토글 */}
        <button
          onClick={() => setDeepResearch((v) => !v)}
          title="심층 리서치"
          style={{
            ...aiBtn,
            background: deepResearch ? "#1d4ed8" : "#f8fafc",
            color: deepResearch ? "#fff" : "#111827",
          }}
        >
          <FaBrain size={16} />
        </button>
      </div>

      {/* 대화 영역 */}
      <div style={{ background: "#f8fafc", overflowY: "auto", padding: "16px 20px" }}>
        {grouped.length === 0 ? (
          <div style={{ color: "#94a3b8", textAlign: "center", marginTop: 80 }}>
            대화 내용을 여기에 표시합니다.
          </div>
        ) : (
          grouped.map((g) => (
            <div key={g.date} style={{ marginBottom: 24 }}>
              <div style={dateLine}>
                <div style={dateLineBar} />
                <span style={dateChip}>{g.date}</span>
                <div style={dateLineBar} />
              </div>
              <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
                {g.items.map((m) => (
                  <Bubble key={m.id} me={m.role === "user"} time={fmtTime(m.createdAt)}>
                    {m.text}
                  </Bubble>
                ))}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력창 */}
      <div
        style={{
          background: "#fff",
          borderTop: "1px solid #e5e7eb",
          padding: "10px 14px",
          display: "grid",
          gridTemplateColumns: "1fr auto",
          gap: 8,
        }}
      >
        <input
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="메시지를 입력하세요..."
          style={{
            width: "100%",
            border: "1px solid #cbd5e1",
            borderRadius: 10,
            padding: "12px 14px",
            outline: "none",
            background: "#f8fafc",
          }}
        />
        <button onClick={handleSend} title="전송" style={sendBtn}>
          <FaPaperPlane size={16} />
        </button>
      </div>
    </div>
  );
}

/** 말풍선 컴포넌트 */
function Bubble({ children, me, time }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: me ? "flex-end" : "flex-start",
        gap: 6,
      }}
    >
      <div
        style={{
          background: me ? "#2563eb" : "#e2e8f0",
          color: me ? "#fff" : "#111827",
          padding: "10px 14px",
          borderRadius: 14,
          maxWidth: "70%",
          whiteSpace: "pre-wrap",
        }}
      >
        {children}
      </div>
      <div style={{ fontSize: 11, color: "#9ca3af", alignSelf: "flex-end" }}>{time}</div>
    </div>
  );
}

/** 스타일 정의 */
const aiBtn = {
  border: "1px solid #cbd5e1",
  borderRadius: 10,
  background: "#f8fafc",
  padding: 8,
  cursor: "pointer",
};

const aiMenu = {
  position: "absolute",
  top: "110%",
  right: 0,
  background: "#fff",
  border: "1px solid #e5e7eb",
  borderRadius: 10,
  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
  overflow: "hidden",
  zIndex: 20,
};

const aiRow = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 12px",
  cursor: "pointer",
};

const sendBtn = {
  border: "none",
  borderRadius: 10,
  background: "#2563eb",
  color: "#fff",
  padding: "0 14px",
  cursor: "pointer",
};

const dateLine = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  color: "#94a3b8",
  fontSize: 12,
  justifyContent: "center",
};

const dateLineBar = {
  height: 1,
  background: "#e2e8f0",
  flex: 1,
};

const dateChip = {
  background: "#f1f5f9",
  padding: "2px 8px",
  borderRadius: 10,
};
