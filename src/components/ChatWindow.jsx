import React, { useMemo, useRef, useState, useEffect } from "react";
import ChatInput from "./ChatInput.jsx";
import { FaBrain } from "react-icons/fa";
import { SiOpenai, SiGooglegemini, SiX } from "react-icons/si";

const models = [
  { id: "gpt", name: "ChatGPT", icon: <SiOpenai size={16} /> },
  { id: "gemini", name: "Gemini", icon: <SiGooglegemini size={16} /> },
  { id: "grok", name: "Grok", icon: <SiX size={16} /> },
];

function fmtTime(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const hh = d.getHours();
  const mm = `${d.getMinutes()}`.padStart(2, "0");
  const ap = hh >= 12 ? "오후" : "오전";
  const h12 = hh % 12 || 12;
  return `${ap} ${h12}:${mm}`;
}

function fmtYMD(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`;
}

export default function ChatWindow({ messages = [], onSend }) {
  console.log("💬 ChatWindow props:", { onSend });

  const [model, setModel] = useState("gpt");
  const [aiOpen, setAiOpen] = useState(false);
  const [deepResearch, setDeepResearch] = useState(false);

  const messagesEndRef = useRef(null);

  const selected = useMemo(
    () => models.find((m) => m.id === model) || models[0],
    [model]
  );

  // 날짜별 그룹화
  const grouped = useMemo(() => {
    const g = {};
    for (const m of messages) {
      const key = fmtYMD(m.createdAt);
      g[key] = g[key] || [];
      g[key].push(m);
    }
    return Object.keys(g).map((k) => ({ date: k, items: g[k] }));
  }, [messages]);

  // 메시지 변경 시 맨 아래로 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ChatInput에서 (text, file)을 받아 상위로 전달
  const handleSend = (text, file) => {
    if (!text?.trim() && !file) return;
    onSend?.(text, model, deepResearch, file);
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
          position: "relative",
        }}
      >
        {/* AI 변경 */}
        <div style={{ position: "relative" }}>
          <button
            onClick={() => setAiOpen((v) => !v)}
            title="AI 변경"
            style={aiBtn}
          >
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
      <div
        style={{
          background: "#f8fafc",
          overflowY: "auto",
          padding: "16px 20px",
        }}
      >
        {grouped.length === 0 ? (
          <div
            style={{
              color: "#94a3b8",
              textAlign: "center",
              marginTop: 80,
            }}
          >
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
                  <Bubble
                    key={m.id}
                    me={m.role === "user"}
                    time={fmtTime(m.createdAt)}
                    file={m.file}
                    text={m.text}
                  />
                ))}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력창 */}
      <ChatInput onSend={handleSend} />
    </div>
  );
}

console.log("📌 ChatWindow 전달된 messages:", messages);
/** 말풍선 */
function Bubble({ me, time, text, file }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: me ? "flex-end" : "flex-start",
      }}
    >
      <div
        style={{
          maxWidth: "64%",
          background: me ? "#dbeafe" : "#fff",
          color: "#0f172a",
          border: "1px solid #e5e7eb",
          borderRadius: 14,
          padding: "10px 12px 6px",
          position: "relative",
          boxShadow: "0 2px 8px rgba(0,0,0,.05)",
        }}
      >
        {/* 업로드한 파일 표시 */}
        {file && (
          <div
            style={{
              marginBottom: 6,
              fontSize: 12,
              color: "#64748b",
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            <span>📎</span>
            <span>
              {file.name}{" "}
              <span style={{ fontSize: 11 }}>
                ({Math.round(file.size / 1024)} KB)
              </span>
            </span>
          </div>
        )}

        {/* 텍스트 */}
        <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {text}
        </div>

        {/* 시간 */}
        <div
          style={{
            fontSize: 11,
            color: "#64748b",
            marginTop: 6,
            textAlign: me ? "right" : "left",
          }}
        >
          {time}
        </div>
      </div>
    </div>
  );
}

/** 상단 UI 스타일 */
const aiBtn = {
  border: "1px solid #cbd5e1",
  background: "#f8fafc",
  borderRadius: 8,
  padding: "7px 10px",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: 6,
};

const aiMenu = {
  position: "absolute",
  top: 38,
  right: 0,
  background: "#fff",
  border: "1px solid #e2e8f0",
  borderRadius: 10,
  boxShadow: "0 12px 30px rgba(0,0,0,.1)",
  padding: "6px 0",
  minWidth: 140,
  zIndex: 30,
};

const aiRow = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 12px",
  cursor: "pointer",
  color: "#334155",
};

const dateLine = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  width: "100%",
};

const dateLineBar = {
  flex: 1,
  height: 1,
  background: "#e2e8f0",
};

const dateChip = {
  border: "1px solid #e2e8f0",
  borderRadius: 999,
  fontSize: 12,
  color: "#64748b",
  background: "#fff",
  padding: "4px 10px",
  justifySelf: "center",
};
