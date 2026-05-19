import { useEffect, useState } from "react";

import API from "../services/api";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";


function CommandPageShell({ children, subtitle, title }) {
  const [operator, setOperator] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    async function fetchOperator() {
      const username = localStorage.getItem("username") || "operator1";
      const response = await API.get("/me", {
        params: {
          username,
        },
      });

      setOperator(response.data);
    }

    fetchOperator().catch(console.error);
  }, []);

  return (
    <div className={`dashboard-shell page-shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <Sidebar
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      <main className="command-page-main">
        <Topbar
          operator={operator}
          subtitle={subtitle}
          title={title}
        />

        <div className="command-page-content">
          {children}
        </div>
      </main>
    </div>
  );
}


export default CommandPageShell;
