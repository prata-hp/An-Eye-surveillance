import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import API from "../services/api";
import {
  formatStatus,
  getStatusClass,
} from "../utils/status";


export default function EscalationPage() {
  const { incidentId } = useParams();
  const [auditLogs, setAuditLogs] = useState([]);
  const [incident, setIncident] = useState(null);
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [incidentResponse, auditResponse] = await Promise.all([
          API.get(`/incidents/${incidentId}`),
          API.get("/audit-logs", {
            params: {
              incident_id: incidentId,
            },
          }),
        ]);
        const incidentData = incidentResponse.data;

        setIncident(incidentData);
        setAuditLogs(auditResponse.data);

        const stationResponse = await API.get("/nearby-stations", {
          params: {
            lat: incidentData.latitude,
            lng: incidentData.longitude,
          },
        });

        setStations(stationResponse.data);

        if (stationResponse.data.length > 0) {
          setSelectedStation(stationResponse.data[0].name);
        }
      } catch (requestError) {
        console.error(requestError);
        setError("Escalation data could not be loaded.");
      }
    }

    loadData();
  }, [incidentId]);

  async function handleSubmit(event) {
    event.preventDefault();

    try {
      await API.post("/dispatch-report", {
        incident_id: incidentId,
        station: selectedStation,
        note,
      });

      setSent(true);
    } catch (requestError) {
      console.error(requestError);
      setError("Dispatch report could not be sent.");
    }
  }

  if (error) {
    return (
      <main className="escalation-page">
        <div className="review-error">{error}</div>
        <Link className="back-link" to={`/review/${incidentId}`}>Back to review</Link>
      </main>
    );
  }

  if (!incident) {
    return (
      <main className="escalation-page">
        <div className="review-loading">Loading escalation desk...</div>
      </main>
    );
  }

  const confidence = Math.round(Number(incident.confidence || 0) * 100);
  const timestamp = incident.timestamp || incident.created_at;
  const suggestedStation = stations[0];

  return (
    <main className="escalation-page">
      <header className="review-header">
        <div>
          <p>Dispatch Coordination</p>
          <h1>Escalation Desk</h1>
        </div>
        <Link className="back-link" to={`/review/${incidentId}`}>Back to review</Link>
      </header>

      <div className="escalation-shell">
        <section className="incident-summary">
          <div className="summary-header">
            <div>
              <p>Incident Summary</p>
              <h2>{incident.camera_id}</h2>
            </div>

            <span className={`status-pill ${getStatusClass(incident.status)}`}>
              {formatStatus(incident.status)}
            </span>
          </div>

          <div className="summary-grid">
            <div>
              <label>Camera ID</label>
              <strong>{incident.camera_id}</strong>
            </div>

            <div>
              <label>Location</label>
              <strong>{incident.location}</strong>
            </div>

            <div>
              <label>Timestamp</label>
              <strong>{new Date(timestamp).toLocaleString()}</strong>
            </div>

            <div>
              <label>AI Confidence</label>
              <strong>{confidence}%</strong>
            </div>

            <div>
              <label>Suggested Station</label>
              <strong>
                {suggestedStation
                  ? `${suggestedStation.name} - ${suggestedStation.distance_km} km`
                  : "No station found"}
              </strong>
            </div>
          </div>

          <div className="timeline-panel">
            <h3>Action Timeline</h3>

            <div className="timeline escalation-timeline">
              {auditLogs.length === 0 ? (
                <div className="timeline-item">
                  <strong>{new Date(timestamp).toLocaleTimeString()}</strong>
                  <span>Awaiting dispatch action.</span>
                </div>
              ) : (
                auditLogs.map((log, index) => (
                  <div
                    className="timeline-item"
                    key={log.id || index}
                  >
                    <strong>{new Date(log.timestamp).toLocaleTimeString()}</strong>
                    <span className={`status-pill ${getStatusClass(log.action)}`}>
                      {formatStatus(log.action)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        <section className="dispatch-form-panel">
          <div className="dispatch-header">
            <div>
              <h2>Dispatch Form</h2>
              <p>Nearest stations ranked by distance.</p>
            </div>
          </div>

          <form
            className="dispatch-form"
            onSubmit={handleSubmit}
          >
            <div className="form-row">
              <label htmlFor="station">Assign Station</label>

              <select
                id="station"
                value={selectedStation}
                onChange={(event) => setSelectedStation(event.target.value)}
              >
                {stations.map((station) => (
                  <option
                    key={station.name}
                    value={station.name}
                  >
                    {station.name} - {station.distance_km} km
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <label htmlFor="officer-note">Officer Note</label>

              <textarea
                id="officer-note"
                value={note}
                onChange={(event) => setNote(event.target.value)}
              />
            </div>

            <button
              className="send-report-btn"
              disabled={!selectedStation}
              type="submit"
            >
              Send Report
            </button>

            {sent && (
              <p className="dispatch-confirmation">Dispatch report sent.</p>
            )}
          </form>
        </section>
      </div>
    </main>
  );
}
