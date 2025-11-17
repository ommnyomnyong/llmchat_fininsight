import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

export default function ProjectPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);

  useEffect(() => {
    fetch(`/api/projects/${projectId}`)
      .then((res) => res.json())
      .then((data) => setProject(data))
      .catch((err) => console.error("Fetch error:", err));
  }, [projectId]);

  if (!project) return <div>Loading...</div>;

  return (
    <div className="project-page">
      <div className="header">
        <h2>{project.name}</h2>
        <button>⋮</button>
      </div>
      <div className="info">
        <div>설명: {project.description}</div>
        <div>목표: {project.goal}</div>
      </div>
      <div className="chat-section">
        <button>＋ 채팅 추가</button>
        {project.chats?.map((chat) => (
          <div key={chat.id} className="chat-record">
            {chat.content}
          </div>
        ))}
      </div>
    </div>
  );
}