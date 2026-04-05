import "./Projects.css";

function Projects() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Workspace</p>
          <h1 className="page-title">My Projects</h1>
        </div>
        <button className="create-btn">+ New Project</button>
      </div>

      <div className="empty-state">
        <p>No projects yet. Create your first one to get started.</p>
      </div>
    </div>
  );
}

export default Projects;
