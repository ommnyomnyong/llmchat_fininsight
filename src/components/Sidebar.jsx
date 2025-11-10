import React, { useEffect, useRef, useState } from "react";
import {
  FiFolder,
  FiMessageCircle,
  FiMoreVertical,
  FiPlus,
} from "react-icons/fi";
import { BsChevronLeft, BsChevronRight } from "react-icons/bs";
import AccountModal from "./AccountModal";
import ProjectModal from "./ProjectModal";

function DotMenu({ onRename, onDelete, onClose }) {
  const ref = useRef(null);
  useEffect(() => {
    const h = (e) => {
      if (ref.current && !ref.current.contains(e.target)) onClose?.();
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [onClose]);
  return (
    <div
      ref={ref}
      style={{
        position: "absolute",
        top: "30px",
        right: 0,
        background: "#fff",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        boxShadow: "0 6px 24px rgba(0,0,0,.08)",
        minWidth: 140,
        overflow: "hidden",
        zIndex: 20,
      }}
    >
      <div
        onClick={() => {
          onRename?.();
          onClose?.();
        }}
        style={rowStyle}
      >
        이름 변경
      </div>
      <div
        onClick={() => {
          onDelete?.();
          onClose?.();
        }}
        style={{ ...rowStyle, color: "#e11d48" }}
      >
        삭제
      </div>
    </div>
  );
}
const rowStyle = {
  padding: "10px 12px",
  fontSize: 14,
  cursor: "pointer",
  color: "#334155",
  borderBottom: "1px solid #f1f5f9",
};

export default function Sidebar({
  collapsed,
  onToggleCollapse,

  account,
  onSaveAccount,

  projects,
  chats,

  selectedProjectId,
  selectedChatId,

  onSelectProject,
  onSelectChat,

  onCreateProject,
  onRenameProject,
  onDeleteProject,

  onCreateChat,
  onRenameChat,
  onDeleteChat,
}) {
  const [accOpen, setAccOpen] = useState(false);
  const [projModalOpen, setProjModalOpen] = useState(false);
  const [openMenuKey, setOpenMenuKey] = useState(null); // 'p-{id}' | 'c-{id}'

  return (
    <aside
      style={{
        width: collapsed ? 60 : 280,
        background: "#f6f9ff",
        borderRight: "1px solid #e2e8f0",
        transition: "width .22s ease",
        boxSizing: "border-box",
        padding: collapsed ? "14px 6px" : "18px 14px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* 접기/펼치기 */}
      <button
        onClick={onToggleCollapse}
        title={collapsed ? "펼치기" : "접기"}
        style={{
          position: "absolute",
          top: 10,
          right: 10,
          width: 28,
          height: 28,
          borderRadius: "50%",
          border: "1px solid #94a3b8",
          background: "#e2e8f0",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#334155",
          cursor: "pointer",
        }}
      >
        {collapsed ? <BsChevronRight /> : <BsChevronLeft />}
      </button>

      {!collapsed && (
        <>
          {/* 계정 */}
          <section style={{ marginTop: 36, marginBottom: 18 }}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: 10 }}>
              계정
            </div>
            <button
              onClick={() => setAccOpen(true)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 10px",
                borderRadius: 10,
                background: "#fff",
                border: "1px solid #cbd5e1",
                cursor: "pointer",
              }}
            >
              <Avatar name={account?.name} url={account?.profileUrl} />
              <div style={{ textAlign: "left" }}>
                <div style={{ fontWeight: 700 }}>{account?.name || "내 계정 보기"}</div>
                <div style={{ fontSize: 12, color: "#64748b" }}>
                  {account.googleEmail || "구글 계정 미연결"}
                </div>
              </div>
            </button>
          </section>

          {/* 프로젝트 */}
          <section>
            <HeaderWithPlus
              title="프로젝트"
              onPlus={() => setProjModalOpen(true)}
            />
            {projects.length === 0 ? (
              <Empty text="아직 생성된 프로젝트가 없습니다" />
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {projects.map((p) => (
                  <ItemRow
                    key={p.id}
                    active={selectedProjectId === p.id}
                    icon={<FiFolder color="#eab308" />}
                    label={p.name}
                    onClick={() => onSelectProject?.(p.id)}
                    menu={
                      openMenuKey === `p-${p.id}` && (
                        <DotMenu
                          onRename={() => {
                            const name = prompt("새 이름");
                            if (name?.trim())
                              onRenameProject?.(p.id, { name: name.trim() });
                          }}
                          onDelete={() => onDeleteProject?.(p.id)}
                          onClose={() => setOpenMenuKey(null)}
                        />
                      )
                    }
                    onOpenMenu={() =>
                      setOpenMenuKey((k) =>
                        k === `p-${p.id}` ? null : `p-${p.id}`
                      )
                    }
                  />
                ))}
              </div>
            )}
          </section>

          {/* 구분선 */}
          <hr
            style={{
              border: 0,
              height: 1,
              background: "#dbe3ef",
              margin: "16px 0",
            }}
          />

          {/* 채팅 */}
          <section>
            <HeaderWithPlus title="채팅" onPlus={() => onCreateChat?.()} />
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {chats.map((c) => (
                <ItemRow
                  key={c.id}
                  active={selectedChatId === c.id}
                  icon={<FiMessageCircle color="#64748b" />}
                  label={c.name}
                  onClick={() => onSelectChat?.(c.id)}
                  menu={
                    openMenuKey === `c-${c.id}` && (
                      <DotMenu
                        onRename={() => {
                          const name = prompt("새 이름");
                          if (name?.trim())
                            onRenameChat?.(c.id, { name: name.trim() });
                        }}
                        onDelete={() => onDeleteChat?.(c.id)}
                        onClose={() => setOpenMenuKey(null)}
                      />
                    )
                  }
                  onOpenMenu={() =>
                    setOpenMenuKey((k) =>
                      k === `c-${c.id}` ? null : `c-${c.id}`
                    )
                  }
                />
              ))}
            </div>
          </section>

          {/* 모달 */}
          {accOpen && (
            <AccountModal
              initial={account}
              onClose={() => setAccOpen(false)}
              onSave={(patch) => {
                onSaveAccount?.(patch);
                setAccOpen(false);
              }}
            />
          )}
          {projModalOpen && (
            <ProjectModal
              onClose={() => setProjModalOpen(false)}
              onCreate={(data) => {
                onCreateProject?.(data);
                setProjModalOpen(false);
              }}
            />
          )}
        </>
      )}
    </aside>
  );
}

/** 공통 작은 컴포넌트들 */
function Avatar({ name, url, size = 34 }) {
  if (url)
    return (
      <img
        src={url}
        alt="profile"
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          objectFit: "cover",
        }}
      />
    );
  const initial = (name || "?").substring(0, 1).toUpperCase();
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: "#c7d2fe",
        color: "#1e293b",
        fontWeight: 800,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {initial}
    </div>
  );
}

function HeaderWithPlus({ title, onPlus }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 10,
      }}
    >
      <div style={{ fontWeight: 700, color: "#0f172a" }}>{title}</div>
      <button
        onClick={onPlus}
        title={`${title} 추가`}
        style={{
          border: "none",
          background: "transparent",
          color: "#2563eb",
          cursor: "pointer",
        }}
      >
        <FiPlus size={18} />
      </button>
    </div>
  );
}

function Empty({ text }) {
  return (
    <div
      style={{
        color: "#94a3b8",
        fontSize: 14,
        fontStyle: "italic",
        margin: "2px 2px 12px",
      }}
    >
      {text}
    </div>
  );
}

function ItemRow({ icon, label, active, onClick, onOpenMenu, menu }) {
  const ref = useRef(null);
  // 외부 클릭 닫기
  useEffect(() => {
    const h = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        if (menu && typeof menu.props?.onClose === "function") {
          menu.props.onClose();
        }
      }
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [menu]);

  return (
    <div
      ref={ref}
      style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "10px 12px",
        borderRadius: 10,
        border: "1px solid #e2e8f0",
        background: active ? "#e7f0ff" : "#fff",
        cursor: "pointer",
      }}
      onClick={onClick}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {icon}
        <div style={{ fontWeight: 600 }}>{label}</div>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onOpenMenu?.();
        }}
        title="메뉴"
        style={{ border: "none", background: "transparent", cursor: "pointer" }}
      >
        <FiMoreVertical />
      </button>
      {menu}
    </div>
  );
}