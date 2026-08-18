import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./Message.css";

function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`message ${
        isUser ? "user-message" : "ai-message"
      }`}
    >
      <div className="message-avatar">
        {isUser ? "You" : "B"}
      </div>

      <div className="message-content">
        <div className="message-name">
          {isUser ? "You" : "BETSY"}
        </div>

        <div className="message-text">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
}

export default Message;