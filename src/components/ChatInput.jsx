import React, { useState, useRef } from 'react';

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleSend = () => {
    // 텍스트도 없고 파일도 없으면 전송 안 함
    console.log("📌 ChatWindow handleSend 전달값:", { text, file });
    if (!text.trim() && !file) return;
    onSend?.(text, file);
    setText('');
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '10px 12px',
        borderTop: '1px solid #e2e8f0',
        gap: 8,
      }}
    >
      {/* 파일 아이콘 버튼 */}
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          border: '1px solid #e2e8f0',
          background: '#f8fafc',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 16,
        }}
        title="파일 첨부"
      >
        📎
      </button>

      {/* 숨겨진 파일 input */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={(e) => {
          const f = e.target.files?.[0];
          setFile(f || null);
        }}
      />

      {/* 선택된 파일명 표시 */}
      {file && (
        <div
          style={{
            fontSize: 12,
            color: '#64748b',
            maxWidth: 200,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {file.name}
        </div>
      )}

      {/* 텍스트 입력 */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="메시지를 입력하세요..."
        disabled={disabled}
        style={{
          flex: 1,
          resize: 'none',
          borderRadius: 10,
          border: '1px solid #e2e8f0',
          padding: '8px 10px',
          minHeight: 38,
          maxHeight: 120,
          fontSize: 14,
        }}
      />

      {/* 전송 버튼 */}
      <button
        type="button"
        onClick={handleSend}
        disabled={disabled}
        style={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          border: 'none',
          background: '#2563eb',
          color: 'white',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 18,
        }}
        title="전송"
      >
        ➤
      </button>
    </div>
  );
}
