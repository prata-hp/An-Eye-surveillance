import { BrowserRouter, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import About from "./pages/About";
import Dashboard from "./pages/Dashboard";
import EscalationPage from "./pages/EscalationPage";
import History from "./pages/History";
import Login from "./pages/Login";
import Notifications from "./pages/Notifications";
import Review from "./pages/Review";
import SupervisorContact from "./pages/SupervisorContact";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
        <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
        <Route path="/supervisor" element={<ProtectedRoute><SupervisorContact /></ProtectedRoute>} />
        <Route path="/about" element={<ProtectedRoute><About /></ProtectedRoute>} />
        <Route path="/review/:incidentId" element={<ProtectedRoute><Review /></ProtectedRoute>} />
        <Route path="/escalate/:incidentId" element={<ProtectedRoute><EscalationPage /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  );
}


export default App;
