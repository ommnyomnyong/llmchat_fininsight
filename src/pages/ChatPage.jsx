import axios from 'axios';
import React, { useMemo, useState, useCallback, useEffect } from "react";
import Sidebar from "../components/Sidebar.jsx";
import ChatWindow from "../components/ChatWindow.jsx";

import { useNavigate } from "react-router-dom";

function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}
// 간단 유틸
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

//---------------------------- 로그인 검증 --------------------------- 추가
useEffect(() => {
  const token = localStorage.getItem("token");
  const email = localStorage.getItem("email");
  const name = localStorage.getItem("name");

  // 디버깅용 출력
  console.log('✅ 토큰:', token, '| 이메일:', email);

  if (token && email) {
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    setAccount((prev) => ({
      ...prev,
      name: name || prev.name,
      googleEmail: email,
    }));
    console.log("✅ 로그인된 사용자:", name, email);
  } else {
    navigate("/"); // 로그인 안된 경우 홈으로
  }
}, [navigate]);


//------------------------- 프로젝트 목록 불러오기 ------------------------------
  useEffect(() => {
    // 실제 로그인된 사용자 이메일로 교체 가능
    const email = account.googleEmail || "test@example.com";

    axios.get(`http://223.130.156.200:8000/project/list?email=${email}`)
      .then((res) => {
        console.log("📂 프로젝트 목록 응답:", res.data);
        setProjects(Array.isArray(res.data) ? res.data : res.data.projects || []);
      })
      .catch((err) => console.error("❌ 프로젝트 목록 불러오기 실패:", err));
  }, [account.googleEmail]);

  // 채팅 스레드 (백 연동 예정)
  const [chats, setChats] = useState([
    { id: "c-1", name: "현재 대화", projectId: null, createdAt: nowISO() },
  ]);

  // 현재 선택
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [selectedChatId, setSelectedChatId] = useState(chats[0].id);

  // 메시지(채팅ID별 맵)
  const [messages, setMessages] = useState({
    "c-1": [],
  });

  // 선택된 채팅의 메시지
  const currentMessages = useMemo(
    () => messages[selectedChatId] ?? [],
    [messages, selectedChatId]
  );

  // 채팅 선택 시 프로젝트 선택 해제
  const handleSelectChat = (chatId) => {
    setSelectedChatId(chatId);
    setSelectedProjectId(null); // ✅ 추가: 프로젝트 선택 해제
  };

  // 프로젝트 선택
  const handleSelectProject = async (pid) => {
    setSelectedProjectId(pid);
    setSelectedChatId(null); // ✅ 추가: 채팅 선택 해제
    console.log("📂 선택된 프로젝트 ID:", pid);

    try {
      const res = await axios.get(`http://223.130.156.200:8000/project/chat/history?project_id=${pid}`);
      const chatsFromDB = res.data.chats || [];

      console.log("💬 프로젝트별 채팅 불러오기:", chatsFromDB);

      // 백엔드의 chat 데이터 형식에 맞게 messages로 변환
      const formatted = chatsFromDB.map((c, idx) => ({
        id: c.id || `m-${idx}`,
        role: "user", // 또는 c.role
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
      const email = account.googleEmail || "test@example.com"; // 실제 로그인 이메일 연결 가능
      formData.append("email", email);
      formData.append("project_name", data.project_name);
      formData.append("description", data.description || "");
      formData.append("project_purpose", data.project_purpose || "");

      const res = await axios.post("http://223.130.156.200:8000/project/create", formData);
      console.log("📁 프로젝트 생성 결과:", res.data);
      
      // 목록 갱신
      const listRes = await axios.get(`http://223.130.156.200:8000/project/list?email=${email}`);
      setProjects(Array.isArray(listRes.data) ? listRes.data : listRes.data.projects || []);

      const projectId = res.data.project_id;
      // 프로젝트 생성 직후 자동 선택
      setSelectedProjectId(projectId);

      // 새 프로젝트의 채팅 ID 등록
      const chatId = `project-${projectId}`;
      setSelectedChatId(chatId);

      // UI → ChatWindow로 자동 이동 효과  
      navigate(`/chat?project=${projectId}`);

    } catch (err) {
      console.error("❌ 프로젝트 생성 실패:", err);
      alert("프로젝트 생성 중 오류가 발생했습니다.");
    }
  };
  
// ✅ 프로젝트 이름 변경 함수
const renameProject = async (projectId, patch) => {
  const newName = patch?.name;
  if (!newName) return;

  try {
    // ✅ UI 먼저 반영
    setProjects((prev) =>
      prev.map((p) =>
        p.id === projectId ? { ...p, project_name: newName } : p
      )
    );

    // ✅ 서버 요청
    await axios.put(
      `http://223.130.156.200:8000/project/rename/${projectId}`,
      { project_name: newName },
      { headers: { "Content-Type": "application/json" } }
    );

    console.log(`✏️ 프로젝트 이름 변경 완료: ${newName}`);
  } catch (err) {
    console.error("❌ 프로젝트 이름 변경 실패:", err);
  }
};
  
  // ✅ 프로젝트 삭제 함수 (ChatPage 쪽)
const deleteProject = async (projectId) => {
  if (!window.confirm("정말 삭제하시겠습니까?")) return;
  try {
    // ✅ UI 즉시 반영
    setProjects((prev) => prev.filter((p) => p.id !== projectId));

    await axios.delete(`http://223.130.156.200:8000/project/delete/${projectId}`);
    console.log(`🗑️ 프로젝트 ${projectId} 삭제 완료`);
  } catch (err) {
    console.error("❌ 프로젝트 삭제 실패:", err);
  }
};


  // 채팅 생성
  const createChat = (name = "새 채팅", projectId = selectedProjectId) => {
    const id = `c-${uuidv4()}`;
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
  
// :흰색_확인_표시: 새로운 함수: 채팅 제목 자동 생성 (첫 메시지 요약)
  const generateChatTitle = useCallback(async (chatId, userMessage) => {
    try {
      // 현재 채팅의 이름 확인
      const currentChat = chats.find(c => c.id === chatId);
      // "새 채팅" 또는 "현재 대화"인 경우에만 제목 변경
      if (!currentChat || (currentChat.name !== "새 채팅" && currentChat.name !== "현재 대화")) {
        return;
      }
      // 메시지가 너무 짧으면 그대로 사용
      if (userMessage.length <= 20) {
        renameChat(chatId, { name: userMessage });
        return;
      }
      // AI에게 요약 요청
      const formData = new FormData();
      formData.append("session_id", "title-generator");
      formData.append("prompt", `다음 메시지를 15자 이내로 간단히 요약해서 채팅방 제목으로 만들어줘. 답변은 오직 제목만 말해:\n\n${userMessage}`);
      const response = await fetch(`http://223.130.156.200:8000/chat/agent-call/gemini`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      let title = await response.text();
      // 텍스트 정리
      title = title.trim()
        .replace(/^["']|["']$/g, '') // 따옴표 제거
        .replace(/\\r\\n|\\n/g, ' ') // 줄바꿈 제거
        .replace(/\s+/g, ' ') // 연속 공백 제거
        .slice(0, 30); // 최대 30자
      if (title) {
        renameChat(chatId, { name: title });
        console.log(`:메모: 채팅 제목 자동 생성: ${title}`);
      }
    } catch (error) {
      console.error(":x: 채팅 제목 생성 실패:", error);
      // 실패 시 메시지 앞 20자를 제목으로 사용
      const fallbackTitle = userMessage.slice(0, 20) + (userMessage.length > 20 ? '...' : '');
      renameChat(chatId, { name: fallbackTitle });
    }
  }, [chats, renameChat]);

  // ✅ 메시지 전송 함수 (수정 완료 버전)
  const sendMessage = useCallback(async (text, model, deepResearch) => {
    console.log("=== sendMessage 호출됨 ===");
    console.log("text:", text);
    console.log("model:", model);
    console.log("deepResearch:", deepResearch);

    // 1) 현재 선택된 채팅이 없으면 새로 생성
    let chatId = selectedChatId;
    if (!chatId) {
      chatId = `c-${uuidv4()}`;
      setMessages(prev => ({ ...prev, [chatId]: [] }));
    }

    // 2) 사용자 메시지 생성 및 반영
    const userMsg = {
      id: `m-${uuidv4()}`,
      role: "user",
      text,
      createdAt: nowISO(),
    };

    setMessages(prev => ({
      ...prev,
      [chatId]: [...(prev[chatId] ?? []), userMsg],
    }));

    // AI 응답 "빈 메시지" 생성 (실시간으로 채워짐)
    const replyMsgId = `m-${uuidv4()}`;
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

      // 파일 업로드 기능을 나중에 붙일 수 있음
      // if (file) formData.append("file", file);

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

        // 필요하면 연속 공백 제거 (선택)
        // t = t.replace(/\s+/g, " ");

        return t.trim();
      }
      
      const cleaned = formatGeminiText(data);


      // 응답을 UI에 반영
      setMessages(prev => {
        const updated = [...(prev[chatId] ?? [])];
        const idx = updated.findIndex(m => m.id === replyMsgId);
        if (idx !== -1) updated[idx] = { ...updated[idx], text: cleaned };
        return { ...prev, [chatId]: updated };
      });

    } catch (error) {
      console.error("❌ 요청 중 오류 발생:", error);
      const errorMsg = {
        id: `m-${uuidv4()}`,
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

  // 계정 수정 저장
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
        setProjects={setProjects}
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
        selectedProjectId={selectedProjectId}
        // onFileUpload={uploadFile}
      />
    </div>
  );
}
