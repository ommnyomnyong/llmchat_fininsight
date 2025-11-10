// src/pages/OAuthSuccess.jsx
import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function OAuthSuccess() {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (token) {
      // 로그인 성공 시 토큰 저장
      localStorage.setItem("jwt_token", token);
      // 채팅 페이지로 이동
      navigate("/chat");
    } else {
      alert("로그인 토큰이 없습니다. 다시 로그인 해주세요.");
      navigate("/");
    }
  }, [navigate]);

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        fontSize: "1.2rem",
        color: "#334155",
      }}
    >
      로그인 처리 중입니다...
    </div>
  );
}
