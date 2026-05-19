import { Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";


function Topbar({ lastEventAt, liveState, operator, subtitle, title = "Control Center", unreadCount = 0 }) {
  const navigate = useNavigate();
  const updatedText = lastEventAt
    ? `${Math.max(0, Math.round((Date.now() - lastEventAt) / 1000))}s ago`
    : "waiting";
  const operatorName = operator?.name || localStorage.getItem("username") || "Operator";
  const operatorInitials = operatorName.slice(0, 2).toUpperCase();
  const operatorMeta = operator
    ? `${operator.shift} - ${operator.desk}`
    : "Loading shift";

  return (
    <header className="topbar">
      <div>
        <h2>{title}</h2>
        <p>
          {subtitle || `Live CCTV relay - South precinct belt - Updated ${updatedText}`}
        </p>
      </div>

      <div className="topbar-right">
        {liveState && (
          <span className={`connection-dot connection-dot--${liveState}`}>
            {liveState}
          </span>
        )}

        <button
          aria-label="Notifications"
          className="notification-btn"
          onClick={() => navigate("/notifications")}
          type="button"
        >
          <Bell size={18} />
          {unreadCount > 0 && <span>{unreadCount}</span>}
        </button>

        <div className="operator-chip">
          <div>
            <strong>{operatorName}</strong>
            <p>{operatorMeta}</p>
          </div>

          <div className="operator-avatar">
            {operatorInitials}
          </div>
        </div>
      </div>
    </header>
  );
}


export default Topbar;
