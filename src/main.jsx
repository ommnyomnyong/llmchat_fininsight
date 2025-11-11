// frontend/src/main.jsx
import React, { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />  {/* ✅ BrowserRouter는 App.jsx에서만 사용 */}
  </StrictMode>
);
