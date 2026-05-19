import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

import { formatStatus } from "../utils/status";


const statusColors = {
  NEW: "#ef233c",
  UNDER_REVIEW: "#f59e0b",
  PENDING: "#2563eb",
  ESCALATED: "#7c3aed",
  FALSE_POSITIVE: "#737373",
  RESOLVED: "#16a34a",
};


function markerRadius(incident) {
  const score = Number(incident.priority_score || 0);

  return Math.max(8, Math.min(18, score / 7));
}


function LiveMap({ incidents }) {
  return (
    <section className="map-background-layer" aria-label="Live incident map">
      <MapContainer
        center={[25.6196, 85.1622]}
        zoomControl={false}
        zoom={13}
        className="floating-map"
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {incidents.map((incident) => (
          <CircleMarker
            key={incident.incident_id}
            center={[incident.latitude, incident.longitude]}
            pathOptions={{
              color: "#fff7ed",
              fillColor: statusColors[incident.status] || "#2563eb",
              fillOpacity: 0.92,
              weight: 2,
            }}
            radius={markerRadius(incident)}
          >
            <Popup>
              <strong>{incident.camera_id}</strong>
              <br />
              {incident.location}
              <br />
              Status: {formatStatus(incident.status)}
              <br />
              Confidence: {Math.round(Number(incident.confidence || 0) * 100)}%
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </section>
  );
}


export default LiveMap;
