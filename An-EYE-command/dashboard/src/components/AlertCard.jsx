import { useNavigate } from "react-router-dom";
import { useMemo } from "react";

import {
  formatStatus,
  getStatusClass,
} from "../utils/status";


export default function AlertCard({ incident }) {
  const navigate = useNavigate();

  const liveTime = useMemo(() => {
    return new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }, []);

  const confidence = Math.round(Number(incident.confidence || 0) * 100);

  return (
    <button
      className="alert-card"
      onClick={() => navigate(`/review/${incident.incident_id}`)}
      type="button"
    >
      <div className="alert-row-top">
        <div className="alert-title">
          {incident.camera_id}
          {" · "}
          {incident.location}
        </div>

        <div className={`status-pill ${getStatusClass(incident.status)}`}>
          {formatStatus(incident.status)}
        </div>
      </div>

      <div className="alert-row-bottom">
        <span>{liveTime}</span>
        <span>{confidence}%</span>
      </div>
    </button>
  );
}
