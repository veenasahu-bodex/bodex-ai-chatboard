import { useRef, useState } from "react";
import {
  FiPaperclip,
  FiSend,
  FiX
} from "react-icons/fi";
import "./InputBox.css";

const API = "http://127.0.0.1:8000";

function InputBox({
  onSend,
  onFileUploaded,
  uploadedFile,
  onRemoveFile
}) {
  const [text, setText] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  const send = () => {
    const message = text.trim();

    if (!message || uploading) return;

    onSend(message);
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const uploadFile = async (file) => {
    if (!file) return;

    if (file.size > 20 * 1024 * 1024) {
      alert("Maximum file size is 20 MB.");
      return;
    }

    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API}/api/upload`, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "File upload failed."
        );
      }

      onFileUploaded(data);

    } catch (error) {
      console.error("UPLOAD ERROR:", error);
      alert(error.message || "Unable to upload file.");

    } finally {
      setUploading(false);

      if (fileRef.current) {
        fileRef.current.value = "";
      }
    }
  };

  return (
    <div className="input-area">

      {uploadedFile && (
        <div className="uploaded-file">

          <div className="file-info">
            <FiPaperclip />
            <span>{uploadedFile}</span>
          </div>

          <button
            type="button"
            onClick={onRemoveFile}
            title="Remove file"
          >
            <FiX />
          </button>

        </div>
      )}

      <div className="input-box">

        <button
          type="button"
          className="attach-btn"
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          title="Upload file"
        >
          <FiPaperclip />
        </button>

        <input
          ref={fileRef}
          type="file"
          hidden
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.webp,.gif"
          onChange={(e) => {
            const file = e.target.files?.[0];

            if (file) {
              uploadFile(file);
            }
          }}
        />

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            uploading
              ? "Uploading file..."
              : "Ask BETSY anything..."
          }
          rows={1}
          disabled={uploading}
        />

        <button
          type="button"
          className="send-btn"
          onClick={send}
          disabled={!text.trim() || uploading}
          title="Send"
        >
          <FiSend />
        </button>

      </div>

      <div className="input-help">
        PDF, DOC, DOCX, TXT, JPG, PNG, WEBP, GIF • Max 20 MB
      </div>

    </div>
  );
}

export default InputBox;