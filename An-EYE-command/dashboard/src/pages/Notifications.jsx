import { useEffect, useState } from "react";

import CommandPageShell from "../components/CommandPageShell";
import API from "../services/api";
import {
  formatStatus,
  getStatusClass,
} from "../utils/status";


function Notifications() {
  const [incidents, setIncidents] = useState([]);

  useEffect(() => {
    async function fetchIncidents() {
      const response = await API.get("/incidents", {
        params: {
          city: localStorage.getItem("city") || "Patna",
        },
      });

      setIncidents(response.data);
    }

    fetchIncidents().catch(console.error);
  }, []);

  return (
    <CommandPageShell
      subtitle="All alert traffic, filterable by operational state."
      title="Notifications"
    >
      <section className="panel notifications-box">
        <div className="map-topbar">
          <div>
            <h3 className="panel-title">Notifications</h3>
            <div className="panel-sub">All alert traffic, filterable by operational state.</div>
          </div>
          <div className="filters">
            <button className="filter-btn active" type="button">New</button>
            <button className="filter-btn" type="button">Reviewed</button>
            <button className="filter-btn" type="button">Escalated</button>
          </div>
        </div>

        <div className="notify-body">
          <div className="alerts-stack page-alerts-stack">
            {incidents.length === 0 ? (
              <div className="empty-state">No notifications in queue.</div>
            ) : (
              incidents.map((incident) => (
                <article className="alert-card" key={incident.incident_id}>
                  <div className="alert-row-top">
                    <div>
                      <div className="alert-title">
                        {incident.camera_id}
                        {" · "}
                        {incident.location}
                      </div>
                    </div>
                    <span className={`status-pill ${getStatusClass(incident.status)}`}>
                      {formatStatus(incident.status)}
                    </span>
                  </div>
                  <div className="alert-row-bottom">
                    <span>{incident.incident_id}</span>
                    <span>{Math.round(Number(incident.confidence || 0) * 100)}%</span>
                  </div>
                  <div className="alert-note">Auto-clipped relay available for officer action.</div>
                </article>
              ))
            )}
          </div>
        </div>
      </section>
    </CommandPageShell>
  );
}


export default Notifications;
