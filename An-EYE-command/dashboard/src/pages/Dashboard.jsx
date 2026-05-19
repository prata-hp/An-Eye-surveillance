import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import AlertCard from "../components/AlertCard";
import LiveMap from "../components/LiveMap";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import API from "../services/api";
import { createAlertsSocket } from "../websocket/socket";

function Dashboard() {
  const [incidents, setIncidents] = useState([]);
  const [lastEventAt, setLastEventAt] = useState(null);
  const [liveState, setLiveState] = useState("connecting");
  const [operator, setOperator] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  const [role] = useState(
    localStorage.getItem("role") || "Operator",
  );

  const socketRef = useRef(null);

  // prevents notification spam on initial socket connect
  const hasInitializedSocket = useRef(false);

  const navigate = useNavigate();

  const city =
    operator?.city ||
    localStorage.getItem("city") ||
    "Patna";

  const fetchIncidents = useCallback(async () => {
    const response = await API.get("/incidents", {
      params: {
        city,
      },
    });

    setIncidents(response.data);
  }, [city]);

  useEffect(() => {
    async function fetchOperator() {
      const username =
        localStorage.getItem("username") ||
        "operator1";

      const response = await API.get("/me", {
        params: {
          username,
        },
      });

      setOperator(response.data);
    }

    fetchOperator().catch(console.error);
  }, []);

  useEffect(() => {
    fetchIncidents().catch((error) => {
      console.error(error);
      setLiveState("offline");
    });
  }, [fetchIncidents]);

  // browser notification permission
  useEffect(() => {
    if ("Notification" in window) {

      if (Notification.permission !== "granted") {
        Notification.requestPermission()
          .catch(console.error);
      }

    }
  }, []);

  useEffect(() => {
    const socket = createAlertsSocket();

    socketRef.current = socket;

    socket.onopen = () => {
      setLiveState("live");

      socket.send("dashboard-connected");

      // allow notifications AFTER initial connect
      setTimeout(() => {
        hasInitializedSocket.current = true;
      }, 1000);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (
        data.type === "NEW_INCIDENT" ||
        data.type === "STATUS_UPDATED"
      ) {

        setLastEventAt(Date.now());

        setUnreadCount((count) => count + 1);

        fetchIncidents().catch(console.error);

        // only trigger notifications after initial load
        if (hasInitializedSocket.current) {

          // SOUND ALERT
          const audio = new Audio("/alert.mp3");

          audio.volume = 0.45;

          audio.play().catch(() => {
            console.log(
              "Browser blocked autoplay until user interaction.",
            );
          });

          // BROWSER NOTIFICATION
          if (Notification.permission === "granted") {

            new Notification("AN-EYE ALERT", {
              body:
                `${data.violence_type || "Violence"} detected`,
              icon: "/favicon.ico",
            });

          }

        }
      }
    };

    socket.onerror = () => {
      setLiveState("offline");
    };

    socket.onclose = () => {
      setLiveState("offline");
    };

    return () => {
      socket.close();
    };
  }, [fetchIncidents]);

  const metrics = useMemo(() => {
    const confirmed = incidents.filter((incident) => (
      [
        "UNDER_REVIEW",
        "ESCALATED",
        "RESOLVED",
      ].includes(incident.status)
    )).length;

    return {
      total: incidents.length,

      confirmed,

      falsePositive:
        incidents.filter(
          (incident) =>
            incident.status === "FALSE_POSITIVE",
        ).length,

      escalated:
        incidents.filter(
          (incident) =>
            incident.status === "ESCALATED",
        ).length,

      activeCameras:
        new Set(
          incidents.map(
            (incident) => incident.camera_id,
          ),
        ).size,
    };
  }, [incidents]);

  async function updateIncidentStatus(
    incidentId,
    status,
  ) {
    await API.patch(
      `/incidents/${incidentId}/status`,
      null,
      {
        params: {
          status,
        },
      },
    );

    await fetchIncidents();
  }

  async function openIncidentReview(
    incident,
  ) {

    if (incident.status === "NEW") {

      await updateIncidentStatus(
        incident.incident_id,
        "UNDER_REVIEW",
      );

    }

    navigate(
      `/review/${incident.incident_id}`,
    );
  }

  return (
    <div
      className={`dashboard-shell ${
        sidebarCollapsed
          ? "sidebar-collapsed"
          : ""
      }`}
    >
      <Sidebar
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      <main className="dashboard-main">

        <Topbar
          lastEventAt={lastEventAt}
          liveState={liveState}
          operator={operator}
          unreadCount={unreadCount}
        />

        <div className="map-stage">

          <LiveMap incidents={incidents} />

          <section
            className="floating-metrics"
            aria-label="Operational metrics"
          >

            <div className="metric-card">
              <span>Alerts Today</span>
              <strong>{metrics.total}</strong>
            </div>

            <div className="metric-card">
              <span>Confirmed</span>
              <strong>{metrics.confirmed}</strong>
            </div>

            <div className="metric-card">
              <span>False Positives</span>
              <strong>{metrics.falsePositive}</strong>
            </div>

            <div className="metric-card">
              <span>Escalated</span>
              <strong>{metrics.escalated}</strong>
            </div>

            <div className="metric-card">
              <span>Active Cameras</span>
              <strong>{metrics.activeCameras}</strong>
            </div>

          </section>

          <section className="floating-alert-queue">

            <div className="queue-header">

              <div className="queue-header-text">
                <p className="queue-label">
                  Incident Queue
                </p>

                <h3 className="queue-title">
                  Live Alerts
                </h3>
              </div>

              <div className="queue-city">
                {city}
              </div>

            </div>

            <div className="alerts-stack">

              {incidents.length === 0 ? (

                <div className="empty-state">
                  No incidents in queue.
                </div>

              ) : (

                incidents.map((incident) => (

                  <AlertCard
                    incident={incident}
                    key={incident.incident_id}
                    onOpenReview={openIncidentReview}
                    onStatusChange={updateIncidentStatus}
                    role={role}
                  />

                ))

              )}

            </div>

          </section>

        </div>

      </main>
    </div>
  );
}

export default Dashboard;