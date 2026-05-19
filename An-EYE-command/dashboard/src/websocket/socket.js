const ALERTS_SOCKET_URL = import.meta.env.VITE_WS_URL;

export function createAlertsSocket() {
  return new WebSocket(ALERTS_SOCKET_URL);
}

export default createAlertsSocket;