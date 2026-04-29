import { useEffect, useState } from "react";
import { appApi } from "../../api";
import "./Invites.css";

const ROLE_LABELS   = { admin: 'Admin', editor: 'Edytor', viewer: 'Widz' };
const STATUS_LABELS = { pending: 'Oczekuje', accepted: 'Zaakceptowane', declined: 'Odrzucone', cancelled: 'Anulowane' };

function Invites() {
  const [sent, setSent]         = useState([]);
  const [received, setReceived] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [tab, setTab]           = useState("received");

  const fetchInvites = async () => {
    setLoading(true);
    try {
      const res = await appApi.get("/invites/");
      setSent(res.data.sent);
      setReceived(res.data.received);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchInvites(); }, []);

  const handleRespond = async (id, action) => {
    try {
      const res = await appApi.post(`/invites/${id}/respond/`, { action });
      setReceived((prev) => prev.map((i) => i.id === id ? res.data : i));
    } catch (err) {
      alert(err.response?.data?.error || "Błąd.");
    }
  };

  const handleCancel = async (id) => {
    try {
      const res = await appApi.post(`/invites/${id}/cancel/`);
      setSent((prev) => prev.map((i) => i.id === id ? res.data : i));
    } catch (err) {
      alert(err.response?.data?.error || "Błąd.");
    }
  };

  const pendingCount = received.filter((i) => i.status === 'pending').length;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Współpraca</p>
          <h1 className="page-title">Zaproszenia</h1>
        </div>
      </div>

      <div className="filter-tabs">
        <button
          className={`filter-tab ${tab === 'received' ? 'active' : ''}`}
          onClick={() => setTab('received')}
        >
          Otrzymane
          {pendingCount > 0 && <span className="invite-badge">{pendingCount}</span>}
        </button>
        <button
          className={`filter-tab ${tab === 'sent' ? 'active' : ''}`}
          onClick={() => setTab('sent')}
        >
          Wysłane
        </button>
      </div>

      {loading && <div className="state-msg">Ładowanie…</div>}

      {!loading && tab === 'received' && (
        <div className="invite-list">
          {received.length === 0 && <p className="state-msg">Brak otrzymanych zaproszeń.</p>}
          {received.map((inv) => (
            <div key={inv.id} className={`invite-card ${inv.status}`}>
              <div className="invite-info">
                <span className="invite-project">{inv.project_name}</span>
                <span className="invite-meta">
                  Od: <strong>{inv.invited_by_name}</strong>
                  {' · '}rola: <strong>{ROLE_LABELS[inv.role] ?? inv.role}</strong>
                </span>
              </div>
              <span className={`invite-status ${inv.status}`}>{STATUS_LABELS[inv.status]}</span>
              {inv.status === 'pending' && (
                <div className="invite-actions">
                  <button className="btn btn-gold" onClick={() => handleRespond(inv.id, 'accept')}>
                    Akceptuj
                  </button>
                  <button className="btn" onClick={() => handleRespond(inv.id, 'decline')}>
                    Odrzuć
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && tab === 'sent' && (
        <div className="invite-list">
          {sent.length === 0 && <p className="state-msg">Brak wysłanych zaproszeń.</p>}
          {sent.map((inv) => (
            <div key={inv.id} className={`invite-card ${inv.status}`}>
              <div className="invite-info">
                <span className="invite-project">{inv.project_name}</span>
                <span className="invite-meta">
                  Do: <strong>{inv.invitee_name}</strong>
                  {' · '}rola: <strong>{ROLE_LABELS[inv.role] ?? inv.role}</strong>
                </span>
              </div>
              <span className={`invite-status ${inv.status}`}>{STATUS_LABELS[inv.status]}</span>
              {inv.status === 'pending' && (
                <button className="btn btn-danger" onClick={() => handleCancel(inv.id)}>
                  Anuluj
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Invites;
