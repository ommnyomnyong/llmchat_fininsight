import React, { useState } from 'react';

export default function ChatInput({ onSend }) {
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    if (!inputValue.trim()) return;
    onSend(inputValue);
    setInputValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', gap: '8px' }}>
      <textarea
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="메시지를 입력하세요..."
        style={{
          flex: 1,
          borderRadius: 8,
          border: '1px solid #ccc',
          padding: '10px',
          resize: 'none',
          minHeight: '45px'
        }}
      />
      <button
        onClick={handleSend}
        style={{
          background: '#4a90e2',
          color: 'white',
          border: 'none',
          borderRadius: 8,
          padding: '0 16px',
          fontWeight: 700,
          cursor: 'pointer'
        }}
      >
        전송
      </button>
    </div>
  );
}
