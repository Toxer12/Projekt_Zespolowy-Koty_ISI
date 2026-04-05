import "./Projects.css";

function Projects() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Workspace</p>
          <h1 className="page-title">Moje projekty</h1>
        </div>
        <button className="create-btn">+ Nowy Projekt</button>
      </div>

      <div className="empty-state">
        <p>Brak projektów. Stwórz nowy aby zacząć.</p>
      </div>
    </div>
  );
}

export default Projects;
