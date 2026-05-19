import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import MiniMap from "../components/MiniMap";
import API from "../services/api";
import {
  formatStatus,
  getStatusClass,
} from "../utils/status";


function Review() {
  const { incidentId } = useParams();
  const navigate = useNavigate();
  const [auditLogs, setAuditLogs] = useState([]);
  const [incident, setIncident] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchIncident() {
      try {
        const [incidentResponse, auditResponse] = await Promise.all([
          API.get(`/incidents/${incidentId}`),
          API.get("/audit-logs", {
            params: {
              incident_id: incidentId,
            },
          }),
        ]);

        setIncident(incidentResponse.data);
        setAuditLogs(auditResponse.data);
      } catch (requestError) {
        console.error(requestError);
        setError("Incident could not be loaded.");
      }
    }

    fetchIncident();
  }, [incidentId]);

  async function updateIncidentStatus(status) {
    try {
      await API.patch(`/incidents/${incidentId}/status`, null, {
        params: {
          status,
        },
      });

      setIncident((currentIncident) => ({
        ...currentIncident,
        status,
      }));
    } catch (requestError) {
      console.error(requestError);
      setError("Incident status could not be updated.");
    }
  }

  function markFalsePositive() {
    updateIncidentStatus("FALSE_POSITIVE");
  }

  function reviewLater() {
    updateIncidentStatus("PENDING");
  }

  if (error) {
    return (
      <main className="review-page">
        <div className="review-error">{error}</div>
        <Link className="back-link" to="/">Back to dashboard</Link>
      </main>
    );
  }

  if (!incident) {
    return (
      <main className="review-page">
        <div className="review-loading">Loading incident...</div>
      </main>
    );
  }

  const confidence = Math.round(Number(incident.confidence || 0) * 100);

  return (
    <main className="review-page">
      <header className="review-header">
        <div>
          <p>Incident Review</p>
          <h1>{incident.location}</h1>
        </div>
        <Link className="back-link" to="/">Back to dashboard</Link>
      </header>

      <section className="review-layout">
        <div className="review-main">
          <section className="evidence-panel">
            <div className="panel-heading">
              <div>
                <p>Video Review</p>
                <h2>{incident.camera_id}</h2>
              </div>
              <div className="review-top-actions">
                <span className={`status-pill ${getStatusClass(incident.status)}`}>
                  {formatStatus(incident.status)}
                </span>

                <a
                  href="https://timid-opt-lure.ngrok-free.dev/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="embedded-live-btn"
                >
                  <img
                    src="/aeye-logo.png"
                    alt="A-EYE"
                    className="embedded-live-icon"
                  />

                  <span>Live Feed</span>
                </a>
              </div>
            </div>

            <div className="video-shell">
              <video controls src={incident.clip_path || incident.clip_url}>
                <track kind="captions" />
              </video>
              <div className="video-fallback">
                <strong>{incident.camera_id}</strong>
                <span>Confidence {confidence}%</span>
              </div>
            </div>

            <div className="review-metadata-grid">
              <div className="meta-chip">
                <label>Camera</label>
                <strong>{incident.camera_id}</strong>
              </div>

              <div className="meta-chip">
                <label>Location</label>
                <strong>{incident.location}</strong>
              </div>

              <div className="meta-chip">
                <label>Time</label>
                <strong>
                  {new Date(incident.timestamp || incident.created_at).toLocaleString()}
                </strong>
              </div>

              <div className="meta-chip">
                <label>Confidence</label>
                <strong>{confidence}%</strong>
              </div>
            </div>

            <div className="decision-panel">
              <button
                className="decision-btn false"
                onClick={markFalsePositive}
                type="button"
              >
                <strong>False Positive</strong>
                <span>Mark incident as harmless.</span>
              </button>

              <button
                className="decision-btn pending"
                onClick={reviewLater}
                type="button"
              >
                <strong>Review Later</strong>
                <span>Return incident to pending queue.</span>
              </button>

              <button
                className="decision-btn escalate"
                onClick={() => navigate(`/escalate/${incident.incident_id}`)}
                type="button"
              >
                <strong>Escalate</strong>
                <span>Open dispatch coordination.</span>
              </button>
            </div>
          </section>
        </div>

        <aside className="review-side-column">
          <div className="mini-map-panel">
            <div className="panel-title">
              <h3>Mini Map</h3>
              <p>Focused location context.</p>
            </div>

            <div className="mini-map-card">
              <a
                href="https://maps.google.com/?q=25.6196,85.1622"
                target="_blank"
                rel="noopener noreferrer"
                className="map-route-btn"
              >
                Open in Maps
              </a>

              <MiniMap incident={incident} />
            </div>
          </div>

          <div className="background-alerts">
            <div className="panel-title">
              <h3>Action Timeline</h3>
              <p>Incident review and operator activity.</p>
            </div>

            <div className="background-alerts-list">
              {auditLogs.length === 0 ? (
                <div className="background-alert-card">
                  <strong>No operator actions yet</strong>
                  <span>Awaiting review activity.</span>
                </div>
              ) : (
                auditLogs.slice(0, 6).map((log, index) => (
                  <div
                    className="background-alert-card"
                    key={log.id || index}
                  >
                    <strong className={`status-pill ${getStatusClass(log.action)}`}>
                      {formatStatus(log.action)}
                    </strong>
                    <span>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}


export default Review;
