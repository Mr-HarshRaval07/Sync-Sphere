import { useEffect, useState } from "react";
import TaskForm from "./components/TaskForm";
import TaskList from "./components/TaskList";
import ChatBot from "./components/ChatBot";

function App() {
  const [tasks, setTasks] = useState([]);

  const fetchTasks = async () => {
    const response = await fetch(
      "http://127.0.0.1:8000/tasks"
    );

    const data = await response.json();

    setTasks(data);
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <div>
      <h1>Sync Sphere</h1>
      <ChatBot/>

      <TaskForm fetchTasks={fetchTasks} />

      <hr />

      <TaskList tasks={tasks} />
    </div>
  );
}

export default App;