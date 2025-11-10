import React, { useEffect, useRef, useState } from "react";

export default function AccountModal({ initial, onClose, onSave }) {
  const [form, setForm] = useState(initial);
  const wrapRef = useRef(null);

  // ✅ 초기값이 바뀌면 form도 업데이트
  useEffect(() => {
    setForm(initial);
  }, [initial]);

  useEffect(() => {
    const h = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) onClose?.();
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [onClose]);

  const onChange = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div style={backdrop}>
      <div ref={wrapRef} style={modal}>
        <h3 style={{ margin: 0 }}>내 계정</h3>
        <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
          <L label="이름">
            <input value={form.name || ""} onChange={(e) => onChange("name", e.target.value)} style={input} />
          </L>
          <L label="구글 아이디">
            <input value={form.googleEmail || ""} onChange={(e) => onChange("googleEmail", e.target.value)} style={input} />
          </L>
          <L label="프로필 이미지 URL">
            <input value={form.profileUrl || ""} onChange={(e) => onChange("profileUrl", e.target.value)} style={input} />
          </L>
          <L label="기본 지침">
            <textarea value={form.defaultGuideline || ""} onChange={(e) => onChange("defaultGuideline", e.target.value)} style={{ ...input, minHeight: 90 }} />
          </L>
        </div>
        <div style={{ marginTop: 14, display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={btnGhost}>닫기</button>
          <button onClick={() => onSave?.(form)} style={btnPrimary}>저장</button>
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

// 스타일 생략 (기존 코드 그대로)


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