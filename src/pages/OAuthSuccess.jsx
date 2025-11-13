// ✅ OAuthSuccess.jsx
import React, { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

export default function OAuthSuccess() {
  // ✅ 구글 OAuth 리디렉션 후 전달된 URL 파라미터 읽기
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    // ✅ URL에서 token, email 추출
    const token = searchParams.get("token");
    const email = searchParams.get("email");
    const name = searchParams.get("name"); // ✅ name 추가

    // 기존 인증 체크/리디렉션 주석 처리
    // if (token && email) {
    //   localStorage.setItem("token", token);
    //   localStorage.setItem("email", email);
    //   if (name) localStorage.setItem("name", name);
    //   console.log("✅ OAuth 로그인 성공:", name, email);
    //   navigate("/chat");
    // } else {
    //   console.error("❌ OAuth 파라미터 누락");
    //   navigate("/");
    // }
    
    // 인증 결과 관계없이 항상 pass해서 채팅 화면으로 이동
    navigate("/chat");
  }, [navigate, searchParams]);

  return <div>로그인 처리 중입니다...</div>;
}
