import { useEffect, useState } from "react";
import TaskForm from "./components/Taskform";
import TaskList from "./components/Tasklist";
import ChatBot from "./components/ChatBot";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [tasks, setTasks] = useState([]);

  const fetchTasks = async () => {
    const response = await fetch(`${API_BASE_URL}/tasks`);

    const data = await response.json();

    setTasks(data);
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <div className="app-shell">
      <header className="hero-panel">
        <div>
          <p className="eyebrow">AI Productivity Suite</p>
          <h1>Sync Sphere</h1>
          <p className="hero-copy">Create tasks, track work, and share updates instantly through Slack.</p>
        </div>
      </header>

      <main className="content-grid">
        <section className="panel">
          <ChatBot />
        </section>

        <section className="panel">
          <TaskForm fetchTasks={fetchTasks} />
        </section>
      </main>

      <section className="panel panel--wide">
        <TaskList tasks={tasks} />
      </section>
    </div>
  );
}

export default App;