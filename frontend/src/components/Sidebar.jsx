import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Bot,
  ShieldAlert,
  Search,
  FileText,
  Server,
  Settings,
} from "lucide-react";
import "./Sidebar.css";

const Sidebar = ({ isOpen, toggleSidebar }) => {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div className="sidebar-overlay" onClick={toggleSidebar}></div>
      )}

      <div className={`sidebar ${isOpen ? "active" : ""}`}>
        <h3 className="sidebar-title">MENU</h3>

        <ul>
          <li>
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              onClick={toggleSidebar}
            >
              <LayoutDashboard size={20} />
              <span>Dashboard</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/copilot"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              onClick={toggleSidebar}
            >
              <Bot size={20} />
              <span>AI Copilot</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/alerts"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              onClick={toggleSidebar}
            >
              <ShieldAlert size={20} />
              <span>Alerts</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/investigation"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              onClick={toggleSidebar}
            >
              <Search size={20} />
              <span>Investigation</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/reports"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              onClick={toggleSidebar}
            >
              <FileText size={20} />
              <span>Reports</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/assets"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              onClick={toggleSidebar}
            >
              <Server size={20} />
              <span>Assets</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              onClick={toggleSidebar}
            >
              <Settings size={20} />
              <span>Settings</span>
            </NavLink>
          </li>
        </ul>
      </div>
    </>
  );
};

export default Sidebar;