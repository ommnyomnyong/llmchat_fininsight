import React, { useEffect, useRef, useState } from "react";

export default function ProjectModal({ onClose, onCreate }) {
  const ref = useRef(null);
  const [form, setForm] = useState({ name: "", description: "", purpose: "" });

  useEffect(() => {
    const h = (e) => {
      if (ref.current && !ref.current.contains(e.target)) onClose?.();
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [onClose]);

  return (
    <div style={backdrop}>
      <div ref={ref} style={modal}>
        <h3 style={{ margin: 0 }}>프로젝트 생성</h3>
        <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
          <L label="프로젝트명">
            <input
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              style={input}
              placeholder="예) 금융 뉴스 분석"
            />
          </L>
          <L label="프로젝트 설명">
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm((f) => ({ ...f, description: e.target.value }))
              }
              style={{ ...input, minHeight: 80 }}
            />
          </L>
          <L label="프로젝트 목적">
            <textarea
              value={form.purpose}
              onChange={(e) => setForm((f) => ({ ...f, purpose: e.target.value }))}
              style={{ ...input, minHeight: 80 }}
            />
          </L>
        </div>
        <div style={{ marginTop: 14, display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={btnGhost}>
            취소
          </button>
          <button
            onClick={() => {
              if (!form.name.trim()) return;
              onCreate?.(form);
            }}
            style={btnPrimary}
          >
            생성
          </button>
        </div>
      </div>
    </div>
  );
}

function L({ label, children }) {
  return (
    <label style={{ display: "grid", gap: 6 }}>
      <span style={{ fontSize: 13, color: "#475569" }}>{label}</span>
      {children}
    </label>
  );
}

const backdrop = {
  position: "fixed",
  inset: 0,
  background: "rgba(15,23,42,.35)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 50,
};
const modal = {
  width: 520,
  maxWidth: "92vw",
  background: "#fff",
  borderRadius: 12,
  padding: 18,
  boxShadow: "0 24px 80px rgba(0,0,0,.25)",
};
const input = {
  border: "1px solid #cbd5e1",
  borderRadius: 8,
  padding: "10px 12px",
  outline: "none",
};
const btnPrimary = {
  background: "#2563eb",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  padding: "8px 12px",
  cursor: "pointer",
};
const btnGhost = {
  background: "#f1f5f9",
  color: "#111827",
  border: "1px solid #e5e7eb",
  borderRadius: 8,
  padding: "8px 12px",
  cursor: "pointer",
};