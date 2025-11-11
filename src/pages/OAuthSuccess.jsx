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

    if (token && email) {
      // ✅ 토큰 및 이메일을 localStorage에 저장
      localStorage.setItem("token", token);
      localStorage.setItem("email", email);
      if (name) localStorage.setItem("name", name); // ✅ 저장

      console.log("✅ OAuth 로그인 성공:", name, email);

      // ✅ 로그인 완료 후 /chat으로 이동
      navigate("/chat");
    } else {
      // ❌ 파라미터 누락 시 로그인 페이지로 복귀
      console.error("❌ OAuth 파라미터 누락");
      navigate("/");
    }
  }, [navigate, searchParams]);

  return <div>로그인 처리 중입니다...</div>;
}
