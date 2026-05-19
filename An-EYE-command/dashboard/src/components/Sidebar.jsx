import {
  Bell,
  History,
  Info,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";


function Sidebar({ collapsed, setCollapsed }) {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("city");
    localStorage.removeItem("precinct");
    localStorage.removeItem("username");

    navigate("/login");
  }

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-top">
        <button
          aria-label="Toggle navigation"
          className="menu-btn"
          onClick={() => setCollapsed(!collapsed)}
          type="button"
        >
          <Menu size={20} />
        </button>
      </div>

      {!collapsed && (
        <>
          <div className="sidebar-section-label">OPERATIONS</div>

          <nav className="sidebar-nav" aria-label="Operations navigation">
            <NavLink
              className={({ isActive }) => (
                isActive ? "nav-item active" : "nav-item"
              )}
              to="/"
            >
              <LayoutDashboard size={18} />
              <span>Dashboard</span>
              <i className="dot" />
            </NavLink>

            <NavLink
              className={({ isActive }) => (
                isActive ? "nav-item active" : "nav-item"
              )}
              to="/history"
            >
              <History size={18} />
              <span>History</span>
              <i className="dot" />
            </NavLink>

            <NavLink
              className={({ isActive }) => (
                isActive ? "nav-item active" : "nav-item"
              )}
              to="/notifications"
            >
              <Bell size={18} />
              <span>Notifications</span>
              <i className="dot" />
            </NavLink>
          </nav>

          <div className="sidebar-section-label support">SUPPORT</div>

          <nav className="sidebar-nav" aria-label="Support navigation">
            <NavLink
              className={({ isActive }) => (
                isActive ? "nav-item active" : "nav-item"
              )}
              to="/supervisor"
            >
              <MessageSquare size={18} />
              <span>Contact Supervisor</span>
              <i className="dot" />
            </NavLink>

            <NavLink
              className={({ isActive }) => (
                isActive ? "nav-item active" : "nav-item"
              )}
              to="/about"
            >
              <Info size={18} />
              <span>About</span>
              <i className="dot" />
            </NavLink>
          </nav>
        </>
      )}

      <div className="sidebar-footer">
        <button className="nav-item logout-btn" onClick={handleLogout} type="button">
          <LogOut size={18} />
          {!collapsed && <span>Logout</span>}
        </button>

        {!collapsed && (
          <div className="control-note">
            Control note
            <br />
            Alerts update silently while review is open.
            Escalation suggestion uses nearest station queue.
          </div>
        )}
      </div>
    </aside>
  );
}


export default Sidebar;
