import {
  FiPlus,
  FiTrash2,
  FiMessageSquare,
  FiTrash
} from "react-icons/fi";
import "./Sidebar.css";

function Sidebar({
  chats,
  activeChatId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onClearAll
}) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-logo">B</div>
        <div>
          <div className="brand-name">BODEX</div>
          <div className="brand-subtitle">BETSY AI</div>
        </div>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        <FiPlus />
        <span>New Chat</span>
      </button>

      <div className="history-title">
        <span>Chat History</span>
        <span className="history-count">{chats.length}</span>
      </div>

      <div className="chat-list">
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={`history-item ${
              chat.id === activeChatId ? "active" : ""
            }`}
            onClick={() => onSelectChat(chat.id)}
          >
            <FiMessageSquare className="history-icon" />

            <span className="history-name">
              {chat.title || "New Chat"}
            </span>

            <button
              className="history-delete"
              title="Delete chat"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteChat(chat.id);
              }}
            >
              <FiTrash2 />
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-bottom">
        <button className="clear-btn" onClick={onClearAll}>
          <FiTrash />
          <span>Clear All Chats</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;