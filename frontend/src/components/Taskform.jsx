import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function TaskForm({ fetchTasks }) {
  const [title, setTitle] = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [status, setStatus] = useState("Pending");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !assignedTo.trim()) {
      setMessage("Please fill in the title and assignee.");
      return;
    }

    setIsSubmitting(true);
    setMessage("");

    const task = {
      title: title.trim(),
      assignedTo: assignedTo.trim(),
      status: status || "Pending",
    };

    try {
      console.log("API_BASE_URL:", API_BASE_URL);
      console.log("Sending task:", task);
      const response = await fetch(`${API_BASE_URL}/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(task),
      });

      if (!response.ok) {
        throw new Error("Task could not be created");
      }

      setTitle("");
      setAssignedTo("");
      setStatus("Pending");
      setMessage("Task created successfully 🎉");
      fetchTasks();
    } catch (error) {
      setMessage("Something went wrong while creating the task.");
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="task-card">
      <div className="task-card__header">
        <div>
          <p className="eyebrow">Task Manager</p>
          <h2>Create a new task</h2>
        </div>
        <span className="pill">Slack ready</span>
      </div>

      <div className="task-card__body">
        <label className="field">
          <span>Task title</span>
          <input
            type="text"
            placeholder="Write a task title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>

        <label className="field">
          <span>Assigned to</span>
          <input
            type="text"
            placeholder="Who should handle this?"
            value={assignedTo}
            onChange={(e) => setAssignedTo(e.target.value)}
          />
        </label>

        <label className="field">
          <span>Status</span>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
          </select>
        </label>
      </div>

      <div className="task-card__footer">
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating..." : "Create Task"}
        </button>
        {message ? <p className="form-message">{message}</p> : null}
      </div>
    </form>
  );
}

export default TaskForm;