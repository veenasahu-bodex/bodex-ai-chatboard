import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import "./App.css";

const createChat = () => ({
  id: Date.now() + Math.random(),
  title: "New Chat",
  messages: [],
  fileId: null,
  fileName: "",
  fileType: "",
  fileContext: ""
});

function App() {
  const [firstChat] = useState(createChat);
  const [chats, setChats] = useState([firstChat]);
  const [activeChatId, setActiveChatId] = useState(firstChat.id);

  const activeChat =
    chats.find((chat) => chat.id === activeChatId) || chats[0];

  const updateChat = (updatedChat) => {
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === updatedChat.id ? updatedChat : chat
      )
    );
  };

  const newChat = () => {
    const chat = createChat();
    setChats((prev) => [...prev, chat]);
    setActiveChatId(chat.id);
  };

  const deleteChat = (id) => {
    setChats((prev) => {
      const remaining = prev.filter((chat) => chat.id !== id);

      if (remaining.length === 0) {
        const chat = createChat();
        setActiveChatId(chat.id);
        return [chat];
      }

      if (id === activeChatId) {
        setActiveChatId(remaining[remaining.length - 1].id);
      }

      return remaining;
    });
  };

  const clearAll = () => {
    const chat = createChat();
    setChats([chat]);
    setActiveChatId(chat.id);
  };

  return (
    <div className="app">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onNewChat={newChat}
        onSelectChat={setActiveChatId}
        onDeleteChat={deleteChat}
        onClearAll={clearAll}
      />

      <ChatWindow
        chat={activeChat}
        updateChat={updateChat}
      />
    </div>
  );
}

export default App;