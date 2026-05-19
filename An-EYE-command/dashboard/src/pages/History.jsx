import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import CommandPageShell from "../components/CommandPageShell";
import API from "../services/api";
import {
  formatStatus,
  getStatusClass,
} from "../utils/status";


function History() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    async function fetchLogs() {
      const response = await API.get("/audit-logs");

      setLogs(response.data);
    }

    fetchLogs().catch(console.error);
  }, []);

  return (
    <CommandPageShell
      subtitle="Reviewed and archived incidents with action trace."
      title="Case History"
    >
      <section className="history-panel">
        <div className="map-topbar">
          <div>
            <h3 className="panel-title">Case History</h3>
            <div className="panel-sub">Reviewed and archived incidents with action trace.</div>
          </div>
          <span>{logs.length} records</span>
        </div>

        <div className="history-table">
          <div className="history-table__head">
            <span>Incident</span>
            <span>Operator</span>
            <span>Action</span>
            <span>Notes</span>
            <span>Time</span>
          </div>

          {logs.map((log) => (
            <div className="history-table__row" key={log.id}>
              <Link to={`/review/${log.incident_id}`}>{log.incident_id}</Link>
              <span>{log.operator_id}</span>
              <strong className={`status-pill ${getStatusClass(log.action)}`}>
                {formatStatus(log.action)}
              </strong>
              <span>{log.notes}</span>
              <time>{new Date(log.timestamp).toLocaleString()}</time>
            </div>
          ))}
        </div>
      </section>
    </CommandPageShell>
  );
}


export default History;
