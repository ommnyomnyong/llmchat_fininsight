import axios from 'axios';
import React, { useMemo, useState, useCallback, useEffect } from "react";
import Sidebar from "../components/Sidebar.jsx";
import ChatWindow from "../components/ChatWindow.jsx";
import { useNavigate } from "react-router-dom";

// 대체 UUID 함수 추가
function simpleUUID() {
  return Math.random().toString(36).substr(2, 9);
}

const nowISO = () => new Date().toISOString();

export default function ChatPage() {
  // 사이드바 접힘
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 계정 (백 연동 예정)
  const [account, setAccount] = useState({
    id: "u-1",
    name: "사용자",
    googleEmail: "",
    profileUrl: "",
    defaultGuideline: "",
  });

  // 프로젝트 (백 연동 예정)
  const [projects, setProjects] = useState([]);
  const navigate = useNavigate();

  //------------------------------------------------------- 추가
  useEffect(() => {
    // const token = localStorage.getItem("token");
    // const email = localStorage.getItem("email");
    // const name = localStorage.getItem("name");
    //
    // if (token && email) {
    //   // ✅ axios에 인증 헤더 설정
    //   axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    //   // ✅ 사용자 정보 반영
    //   setAccount((prev) => ({
    //     ...prev,
    //     name: name || prev.name,
    //     googleEmail: email,
    //   }));
    //   console.log("✅ 로그인된 사용자:", name, email);
    // } else {
    //   navigate("/"); // 로그인 안된 경우 홈으로
    // }
    // 인증 완전 패스 (주석처리)
  }, [navigate]);
  //-------------------------------------------------------

  useEffect(() => {
    // 실제 로그인된 사용자 이메일로 교체 가능
    const email = account.googleEmail || "test@example.com";
    axios.get(`http://223.130.156.200:8000/project/list?email=${email}`)
      .then((res) => {
        if (!res.data.new_user) {
          setProjects(res.data.projects);
        } else {
          setProjects([]);
        }
      })
      .catch((err) => console.error("❌ 프로젝트 목록 불러오기 실패:", err));
  }, []);

  // 채팅 스레드
  const [chats, setChats] = useState([
    { id: "c-1", name: "현재 대화", projectId: null, createdAt: nowISO() },
  ]);
  // 현재 선택
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [selectedChatId, setSelectedChatId] = useState(chats[0].id);

  // 메시지(채팅ID별 맵)
  const [messages, setMessages] = useState({ "c-1": [] });

  // 선택된 채팅의 메시지
  const currentMessages = useMemo(
    () => messages[selectedChatId] ?? [],
    [messages, selectedChatId]
  );

  // 채팅 선택 시 프로젝트 선택 해제
  const handleSelectChat = (chatId) => {
    setSelectedChatId(chatId);
    setSelectedProjectId(null);
  };

  // 프로젝트 선택
  const handleSelectProject = async (pid) => {
    setSelectedProjectId(pid);
    setSelectedChatId(null);
    console.log("📂 선택된 프로젝트 ID:", pid);
    try {
      const res = await axios.get(`http://223.130.156.200:8000/chat/list?project_id=${pid}`);
      const chatsFromDB = res.data.chats || [];
      console.log("💬 프로젝트별 채팅 불러오기:", chatsFromDB);
      // 백엔드의 chat 데이터 형식에 맞게 messages로 변환
      const formatted = chatsFromDB.map((c, idx) => ({
        id: c.id || `m-${idx}`,
        role: "user",
        text: c.user_input + "\n\n" + c.bot_output,
        createdAt: new Date().toISOString(),
      }));
      // 프로젝트 전용 "가상 채팅 ID"로 messages 저장
      const chatId = `project-${pid}`;
      setMessages((prev) => ({ ...prev, [chatId]: formatted }));
      setSelectedChatId(chatId);
    } catch (err) {
      console.error("❌ 채팅 불러오기 실패:", err);
    }
  };

  // ✅ 프로젝트 생성
  const createProject = async (data) => {
    try {
      const formData = new FormData();
      const email = account.googleEmail || "test@example.com";
      formData.append("email", email);
      formData.append("project_name", data.name);
      formData.append("description", data.description || "");
      const res = await axios.post("http://223.130.156.200:8000/project/create", formData);
      console.log("📁 프로젝트 생성 결과:", res.data);
      // 생성 후 목록 갱신
      const listRes = await axios.get(`http://223.130.156.200:8000/project/list?email=${email}`);
      if (!listRes.data.new_user) {
        setProjects(listRes.data.projects);
      }
    } catch (err) {
      console.error("❌ 프로젝트 생성 실패:", err);
      alert("프로젝트 생성 중 오류가 발생했습니다.");
    }
  };
  const renameProject = (id, patch) =>
    setProjects((prev) => prev.map((p) => (p.id === id ? { ...p, ...patch } : p)));
  const deleteProject = async (id) => {
    await axios.delete(`http://223.130.156.200:8000/project/delete?project_id=${id}`);
    setProjects(prev => prev.filter(p => p.id !== id));
  };

  // 채팅 생성
  const createChat = (name = "새 채팅", projectId = selectedProjectId) => {
    // const id = `c-${crypto.randomUUID()}`;
    const id = `c-${simpleUUID()}`;
    const newChat = { id, name, projectId: projectId ?? null, createdAt: nowISO() };
    setChats((prev) => [newChat, ...prev]);
    setMessages((prev) => ({ ...prev, [id]: [] }));
    setSelectedChatId(id);
    return id;
  };
  const renameChat = (id, patch) =>
    setChats((prev) => prev.map((c) => (c.id === id ? { ...c, ...patch } : c)));
  const deleteChat = (id) => {
    setChats((prev) => prev.filter((c) => c.id !== id));
    setMessages((prev) => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
    if (selectedChatId === id) {
      const fallback = chats.find((c) => c.id !== id);
      setSelectedChatId(fallback ? fallback.id : null);
    }
  };

  // ✅ 메시지 전송 함수 (수정 완료 버전)
  const sendMessage = useCallback(async (text, model, deepResearch) => {
    console.log("=== sendMessage 호출됨 ===");
    console.log("text:", text);
    console.log("model:", model);
    console.log("deepResearch:", deepResearch);
    // 1) 현재 선택된 채팅이 없으면 새로 생성
    let chatId = selectedChatId;
    if (!chatId) {
      // chatId = `c-${crypto.randomUUID()}`;
      chatId = `c-${simpleUUID()}`;
      setMessages(prev => ({ ...prev, [chatId]: [] }));
    }
    // 2) 사용자 메시지 생성 및 반영
    const userMsg = {
      // id: `m-${crypto.randomUUID()}`,
      id: `m-${simpleUUID()}`,
      role: "user",
      text,
      createdAt: nowISO(),
    };
    setMessages(prev => ({
      ...prev,
      [chatId]: [...(prev[chatId] ?? []), userMsg],
    }));
    // AI 응답 "빈 메시지" 생성 (실시간으로 채워짐)
    // const replyMsgId = `m-${crypto.randomUUID()}`;
    const replyMsgId = `m-${simpleUUID()}`;
    setMessages(prev => ({
      ...prev,
      [chatId]: [
        ...(prev[chatId] ?? []),
        { id: replyMsgId, role: "assistant", text: "", createdAt: new Date().toISOString() },
      ],
    }));
    // 모델 이름 매핑 (백엔드 기준)
    let modelName;
    if (deepResearch) {
      modelName =
        model === "gemini"
          ? "gemini-research"
          : model === "gpt"
          ? "openai-research"
          : `${model}-research`;
    } else {
      modelName =
        model === "gpt"
          ? "openai"
          : model === "gemini"
          ? "gemini"
          : model === "grok"
          ? "grok"
          : model;
    }
    // 4) 백엔드 요청
    try {
      const formData = new FormData();
      formData.append("session_id", chatId);
      formData.append("prompt", text);
      if (selectedProjectId) formData.append("project_id", selectedProjectId);
      const response = await fetch(`http://223.130.156.200:8000/chat/agent-call/${modelName}`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.text();
      function formatGeminiText(text) {
        if (typeof text !== "string") return text;
        let t = text.trim();
        // 바깥 큰따옴표 제거
        if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
          t = t.slice(1, -1).trim();
        }
        // 이스케이프 문자 처리
        t = t
          .replace(/\\r\\n/g, "\n")
          .replace(/\\n/g, "\n")
          .replace(/\\t/g, " ")
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, "\\");
        return t.trim();
      }
      const cleaned = formatGeminiText(data);
      setMessages(prev => {
        const updated = [...(prev[chatId] ?? [])];
        const idx = updated.findIndex(m => m.id === replyMsgId);
        if (idx !== -1) updated[idx] = { ...updated[idx], text: cleaned };
        return { ...prev, [chatId]: updated };
      });
    } catch (error) {
      console.error("❌ 요청 중 오류 발생:", error);
      const errorMsg = {
        // id: `m-${crypto.randomUUID()}`,
        id: `m-${simpleUUID()}`,
        role: "assistant",
        text: `오류가 발생했습니다: ${error.message}`,
        createdAt: new Date().toISOString(),
      };
      setMessages(prev => ({
        ...prev,
        [chatId]: [...(prev[chatId] ?? []), errorMsg],
      }));
    }
  }, [selectedChatId, selectedProjectId]);

  const saveAccount = (patch) => setAccount((a) => ({ ...a, ...patch }));
  // ✅ 디버깅: sendMessage 함수 확인
  console.log("💡 ChatPage 렌더링 - sendMessage 타입:", typeof sendMessage);

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
        account={account}
        onSaveAccount={saveAccount}
        projects={projects || []}   // ✅ undefined 방지 -------------------- 수정
        chats={chats || []}         // ✅ undefined 방지
        selectedProjectId={selectedProjectId}
        selectedChatId={selectedChatId}
        onSelectProject={handleSelectProject}
        onSelectChat={handleSelectChat}
        onCreateProject={createProject}
        onRenameProject={renameProject}
        onDeleteProject={deleteProject}
        onCreateChat={() => createChat("새 채팅")}
        onRenameChat={renameChat}
        onDeleteChat={deleteChat}
      />
      <ChatWindow
        key={selectedChatId}
        messages={currentMessages}
        onSend={sendMessage}
      />
    </div>
  );
}
