import { useEffect, useRef, useState } from "react";
import {
  FiCopy,
  FiCheck,
  FiTrash2
} from "react-icons/fi";
import InputBox from "./InputBox";
import Message from "./Message";
import "./ChatWindow.css";

const API = "http://localhost:8000";

const suggestions = [
  "What is BODEX?",
  "What is BODEX's primary mission?",
  "What does it mean for BODEX to be an AI-First company?",
  "What are the three core competencies of BODEX?",
  "What services does BODEX provide?",
  "What products does BODEX offer?"
];

function ChatWindow({ chat, updateChat }) {
  const bottomRef = useRef(null);
  const [copiedId, setCopiedId] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth"
    });
  }, [chat?.messages, loading]);

  if (!chat) return null;

  const sendMessage = async (text) => {
    const message = text.trim();

    if (!message || loading) return;

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: message
    };

    const previousMessages = chat.messages || [];

    const messages = [
      ...previousMessages,
      userMessage
    ];

    const updated = {
      ...chat,
      messages,
      title:
        previousMessages.length === 0
          ? message.slice(0, 35)
          : chat.title
    };

    updateChat(updated);
    setLoading(true);

    const start = performance.now();

    try {
      const response = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: message,

          file_id: chat.fileId || null,

          context: chat.fileContext || "",

          history: previousMessages.map((item) => ({
            role: item.role,
            content: item.content
          }))
        })
      });

      let data = {};

      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
          data.message ||
          `Server error: ${response.status}`
        );
      }

      const answer =
        data.reply ||
        data.response ||
        data.answer;

      if (!answer) {
        throw new Error(
          "BETSY returned an empty response."
        );
      }

      const elapsed =
        data.responseTime ||
        Number(
          (
            (performance.now() - start) /
            1000
          ).toFixed(2)
        );

      const aiMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: answer,
        time: elapsed
      };

      updateChat({
        ...updated,
        messages: [
          ...messages,
          aiMessage
        ]
      });

    } catch (error) {
      console.error("CHAT ERROR:", error);

      const errorMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content:
          error.message ||
          "Unable to connect with BODEX AI.",
        error: true
      };

      updateChat({
        ...updated,
        messages: [
          ...messages,
          errorMessage
        ]
      });

    } finally {
      setLoading(false);
    }
  };

  const copyMessage = async (message) => {
    try {
      await navigator.clipboard.writeText(
        message.content
      );

      setCopiedId(message.id);

      setTimeout(() => {
        setCopiedId(null);
      }, 1500);

    } catch (error) {
      console.error(
        "COPY ERROR:",
        error
      );
    }
  };

  const removeFile = async () => {
    if (!chat.fileId) return;

    try {
      await fetch(
        `${API}/api/file/${chat.fileId}`,
        {
          method: "DELETE"
        }
      );
    } catch (error) {
      console.error(
        "DELETE FILE ERROR:",
        error
      );
    }

    updateChat({
      ...chat,
      fileId: null,
      fileName: "",
      fileType: "",
      fileContext: ""
    });
  };

  const handleFileUploaded = (file) => {
    updateChat({
      ...chat,

      fileId:
        file.file_id || null,

      fileName:
        file.filename ||
        file.file_name ||
        "",

      fileType:
        file.file_type || "",

      fileContext:
        file.text ||
        file.file_context ||
        ""
    });
  };

  const clearCurrentChat = () => {
    updateChat({
      ...chat,
      messages: [],
      title: "New Chat"
    });
  };

  const isEmpty =
    chat.messages.length === 0;

  return (
    <main className="chat-window">

      <header className="chat-header">

        <div className="assistant-info">

          <div className="assistant-avatar">
            B
          </div>

          <div>
            <h2>BETSY</h2>

            <span>
              BODEX Enhanced Trusted Sidekick
            </span>
          </div>

        </div>

        {chat.messages.length > 0 && (
          <button
            className="delete-current"
            onClick={clearCurrentChat}
            title="Clear current chat"
          >
            <FiTrash2 />
          </button>
        )}

      </header>

      <section className="messages-area">

        {isEmpty ? (

          <div className="welcome">

            <div className="welcome-avatar">
              B
            </div>

            <h1>
              How can I help you?
            </h1>

            <p>
              Hello there! I'm BETSY — your
              BODEX Enhanced Trusted Sidekick.
            </p>

            <div className="suggestions">

              {suggestions.map(
                (question) => (
                  <button
                    key={question}
                    onClick={() =>
                      sendMessage(question)
                    }
                    disabled={loading}
                  >
                    {question}
                  </button>
                )
              )}

            </div>

          </div>

        ) : (

          <div className="message-container">

            {chat.messages.map(
              (message) => (

                <div
                  key={message.id}
                  className="message-wrapper"
                >

                  <Message
                    message={message}
                  />

                  {message.role ===
                    "assistant" &&
                    !message.error && (

                      <div className="message-actions">

                        <button
                          onClick={() =>
                            copyMessage(
                              message
                            )
                          }
                        >

                          {copiedId ===
                          message.id ? (
                            <>
                              <FiCheck />
                              Copied
                            </>
                          ) : (
                            <>
                              <FiCopy />
                              Copy
                            </>
                          )}

                        </button>

                        {message.time && (
                          <span>
                            ⚡{" "}
                            {message.time}s
                          </span>
                        )}

                      </div>

                    )}

                </div>

              )
            )}

            {loading && (
              <div className="typing-indicator">
                <div className="typing-avatar">
                  B
                </div>

                <div className="typing-content">
                  <strong>BETSY</strong>

                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />

          </div>

        )}

      </section>

      <InputBox
        onSend={sendMessage}
        onFileUploaded={
          handleFileUploaded
        }
        uploadedFile={
          chat.fileName
        }
        onRemoveFile={
          removeFile
        }
      />

      <div className="disclaimer">
        BETSY can make mistakes, please check
        and validate responses. © BODEX
      </div>

    </main>
  );
}

export default ChatWindow;