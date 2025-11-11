import React from 'react';

export default function ChatMessages({ messages }) {
  const formatDate = (dateStr) =>
    new Date(dateStr).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' });
  const formatTime = (dateStr) =>
    new Date(dateStr).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });

  let lastDate = null;

  return (
    <div>
      {messages.map((msg, idx) => {
        const currentDate = formatDate(msg.createdAt);
        const showDateDivider = currentDate !== lastDate;
        lastDate = currentDate;

        return (
          <React.Fragment key={msg.id}>
            {showDateDivider && (
              <div style={{
                textAlign: 'center',
                color: '#888',
                fontSize: '0.85em',
                margin: '20px 0 10px',
                position: 'relative'
              }}>
                <span style={{
                  background: '#f6f8fb',
                  padding: '4px 10px',
                  borderRadius: '10px',
                  border: '1px solid #ddd'
                }}>
                  {currentDate}
                </span>
              </div>
            )}

            <div
              style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: 6,
              }}
            >
              <div
                style={{
                  background: msg.role === 'user' ? '#cbe7ff' : '#fff',
                  border: msg.role === 'user' ? 'none' : '1px solid #ddd',
                  borderRadius: 12,
                  padding: '8px 12px',
                  maxWidth: '70%',
                  wordBreak: 'break-word',
                }}
              >
                <div>{msg.text}</div>
                <div style={{
                  textAlign: 'right',
                  fontSize: '0.7em',
                  color: '#888',
                  marginTop: 4
                }}>
                  {formatTime(msg.createdAt)}
                </div>
              </div>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}
