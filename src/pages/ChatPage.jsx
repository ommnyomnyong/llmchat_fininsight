import React, { useState, useEffect } from "react";
import ChatWindow from "../components/ChatWindow";
import Sidebar from "../components/Sidebar";

export default function ChatPage() {
  // --- Sidebar 관련 상태 ---
  const [collapsed, setCollapsed] = useState(false);
  const [account, setAccount] = useState({
    name: "",
    googleEmail: "",
    profileUrl: "",
  });

  // URL에서 로그인 사용자 정보 읽어서 account 상태로 반영
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const name = params.get("name") || "";
    const googleEmail = params.get("email") || "";
    const profileUrl = params.get("picture") || "";

    if (name || googleEmail) {
      setAccount({ name, googleEmail, profileUrl });
      console.log("✅ 로그인 사용자 정보:", { name, googleEmail, profileUrl });
    }
  }, []);

  const [projects, setProjects] = useState([{ id: 1, name: "테스트 프로젝트" }]);
  const [chats, setChats] = useState([{ id: 1, name: "첫 번째 채팅" }]);
  const [selectedProjectId, setSelectedProjectId] = useState(1);
  const [selectedChatId, setSelectedChatId] = useState(1);
  const [messages, setMessages] = useState([]);

  const handleSend = (text, model, deepResearch) => {
    if (!text?.trim()) return;

    const newMsg = {
      id: Date.now(),
      role: "user",
      text,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newMsg]);

    fetch("http://localhost:3002/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, model, deepResearch }),
    })
      .then((res) => res.json())
      .then((data) => {
        const botMsg = {
          id: Date.now() + 1,
          role: "assistant",
          text: data.reply || "서버 응답이 없습니다.",
          createdAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, botMsg]);
      })
      .catch((err) => {
        console.error(err);
        const errMsg = {
          id: Date.now() + 2,
          role: "assistant",
          text: "⚠️ 서버 오류가 발생했습니다.",
          createdAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errMsg]);
      });
  };

  return (
    <div style={{ display: "flex", height: "100vh", background: "#f8fafc" }}>
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
        account={account}
        onSaveAccount={(patch) => setAccount({ ...account, ...patch })}
        projects={projects}
        chats={chats}
        selectedProjectId={selectedProjectId}
        selectedChatId={selectedChatId}
        onSelectProject={(id) => setSelectedProjectId(id)}
        onSelectChat={(id) => setSelectedChatId(id)}
        onCreateProject={() => {
          const name = prompt("새 프로젝트 이름을 입력하세요");
          if (!name) return;
          const newProj = { id: Date.now(), name };
          setProjects((prev) => [...prev, newProj]);
        }}
        onRenameProject={(id, patch) => {
          setProjects((prev) =>
            prev.map((p) => (p.id === id ? { ...p, ...patch } : p))
          );
        }}
        onDeleteProject={(id) =>
          setProjects((prev) => prev.filter((p) => p.id !== id))
        }
        onCreateChat={() => {
          const name = prompt("새 채팅 이름을 입력하세요");
          if (!name) return;
          const newChat = { id: Date.now(), name };
          setChats((prev) => [...prev, newChat]);
        }}
        onRenameChat={(id, patch) => {
          setChats((prev) =>
            prev.map((c) => (c.id === id ? { ...c, ...patch } : c))
          );
        }}
        onDeleteChat={(id) =>
          setChats((prev) => prev.filter((c) => c.id !== id))
        }
      />

      {/* 메인 채팅 창 */}
      <ChatWindow messages={messages} onSend={handleSend} />
    </div>
  );
}