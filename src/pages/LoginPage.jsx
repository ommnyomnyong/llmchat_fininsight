import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
// import Login from "react-login-page";

function GoogleLoginButton() {
  return (
    <button
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        width: '100%', padding: '13px 0', borderRadius: 8,
        border: 'none', fontWeight: 700, fontSize: '1.1em',
        background: '#f6fbff', color: '#245',
        marginBottom: 18, marginTop: 20, position: "relative", cursor: "pointer",
        boxShadow: '0 2px 12px #a8def866', transition: "0.16s"
      }}
      onClick={() => window.location.href = "http://localhost:8000/auth/google/login"}
    >
      <img src="https://www.gstatic.com/marketing-cms/assets/images/d5/dc/cfe9ce8b4425b410b49b7f2dd3f3/g.webp=s96-fcrop64=1,00000000ffffffff-rw"
           alt="Google" style={{width: 26, marginRight: 12, display: 'inline-block'}}/>
      구글로 로그인
    </button>
  );
}


export default function LoginPage() {
  const navigate = useNavigate();

  // ✅ 자동 로그인 유지
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      console.log("✅ 이미 로그인된 사용자입니다. /chat으로 이동합니다.");
      navigate("/chat");
    }
  }, [navigate]);


// function App() {
  return (
    <div style={{
      minHeight: "100vh", width:"100vw", background: "linear-gradient(140deg,#e9f7ff 60%, #f6f7fe 100%)",
      display: "flex", alignItems: "center", justifyContent: "center",
      position: "relative", overflow: "hidden"
    }}>
      {/* 밝은 톤 원형 데코 */}
      <div style={{
        position: "absolute", left: -80, top: -90, width: 220, height: 220,
        borderRadius: "50%", background: "radial-gradient(circle at 70% 30%, #60bfff77 80%,transparent 100%)",
        filter: "blur(8px)", zIndex: 0
      }} />
      <div style={{
        position: "absolute", right: -60, bottom: -80, width: 140, height: 140,
        borderRadius: "50%", background: "radial-gradient(circle at 20% 80%, #ffc08266 75%,transparent 100%)",
        filter: "blur(14px)", zIndex: 0
      }} />
      <div style={{
        width: 370, zIndex: 1, borderRadius: 18,
        background: "rgba(255,255,255,0.8)",  // 더 밝고 투명!
        boxShadow: "0 8px 50px #aee8ff99",
        padding: "49px 32px 36px 32px",
        backdropFilter: "blur(10px)"
      }}>
        {/* 두 배 크기 회사 로고 */}
        <img
          src="https://fins.ai/assets/images/header_img/fin_logo_scroll.png"
          alt="company logo"
          style={{ width: 168, margin: "0 auto 18px auto", display: 'block', filter:"drop-shadow(0 1px 10px #15a1fa44)" }}
        />
        <h2 style={{
          textAlign: "center", fontWeight: 800, color: "#284e93",
          letterSpacing: "-1.2px", marginBottom: 8, fontSize: "1.28em"
        }}>로그인</h2>

        <GoogleLoginButton />
        {/* 구분선 */}
        <div style={{
          textAlign: "center", color: "#afd2e8", fontWeight: 500,
          margin: "19px 0 20px 0", letterSpacing: "0.7px"
        }}>Welcome LLM Chat</div>
        {/* <Login
          onLogin={(e,pw)=>console.log(e,pw)}
          buttonText="이메일로 로그인"
          inputNames={{ username: "이메일", password: "비밀번호" }}
          usernameType="email"
          usernameInputProps={{
            placeholder: "이메일",
            style: {
              borderRadius: 8, padding: "9px 13px", background:"#f6fbff", color:"#245",
              border: "1.4px solid #b8e4fd", marginTop:4, fontWeight:600
            }
          }}
          passwordInputProps={{
            placeholder: "비밀번호",
            style: {
              borderRadius: 8, padding: "9px 13px", background:"#f6fbff", color:"#245",
              border: "1.4px solid #b8e4fd", marginTop:8, fontWeight:600
            }
          }}
          buttonProps={{
            style: {
              background: "linear-gradient(90deg,#7dd2fb 22%,#4ca2fd 78%)", color: "#fff",
              borderRadius:"10px", padding: "11px 0", marginTop: "10px",
              fontWeight:700, fontSize: "1.1em", boxShadow:"0 2px 14px #88e9fa86"
            }
          }}
        /> */}
        {/* 회원가입 안내 완전 제거 */}
      </div>
    </div>
  );
}
// export default App;
