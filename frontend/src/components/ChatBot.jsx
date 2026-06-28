import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function ChatBot() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");

  const sendMessage = async () => {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
      }),
    });

    const data = await res.json();

    setResponse(data.reply);
    setMessage("");
  };

  return (
    <div>
      <h2>Sync Sphere AI</h2>

      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a task..."
      />

      <button onClick={sendMessage}>
        Send
      </button>

      <p>{response}</p>
    </div>
  );
}

export default ChatBot;