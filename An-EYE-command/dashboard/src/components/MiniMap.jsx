import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";


function MiniMap({ incident }) {
  return (
    <MapContainer
      center={[incident.latitude, incident.longitude]}
      zoom={16}
      className="mini-map"
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <CircleMarker
        center={[incident.latitude, incident.longitude]}
        pathOptions={{
          color: "#fff7ed",
          fillColor: "#ef233c",
          fillOpacity: 0.95,
          weight: 2,
        }}
        radius={12}
      >
        <Popup>
          <strong>{incident.camera_id}</strong>
          <br />
          {incident.location}
        </Popup>
      </CircleMarker>
    </MapContainer>
  );
}


export default MiniMap;
