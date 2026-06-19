function TaskList({ tasks }) {
  return (
    <div>
      <h2>All Tasks</h2>

      {tasks.map((task, index) => (
        <div key={index}>
          <h3>{task.title}</h3>
          <p>Assigned To: {task.assignedTo}</p>
          <p>Status: {task.status}</p>
          <hr />
        </div>
      ))}
    </div>
  );
}

export default TaskList;