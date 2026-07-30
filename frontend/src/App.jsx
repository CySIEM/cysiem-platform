import { useState } from "react";
import { Routes, Route, useLocation } from "react-router-dom";

import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Copilot from "./pages/Copilot";
import Alerts from "./pages/Alerts";
import Investigation from "./pages/Investigation";
import Reports from "./pages/Reports";
import Assets from "./pages/Assets";
import Settings from "./pages/Settings";
import Profile from "./pages/Profile";

import "./App.css";

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const location = useLocation();

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
  };

  const isLoginPage = location.pathname === "/login";

  return (
    <>
      {!isLoginPage && (
        <Navbar toggleSidebar={toggleSidebar} />
      )}

      <div className={isLoginPage ? "" : "main-container"}>
        {!isLoginPage && (
          <Sidebar
            isOpen={isSidebarOpen}
            toggleSidebar={toggleSidebar}
          />
        )}

        <div className={isLoginPage ? "" : "content"}>
          <Routes>
            {/* Login */}
            <Route path="/login" element={<Login />} />

            {/* Dashboard */}
            <Route path="/" element={<Dashboard />} />

            {/* AI Copilot */}
            <Route path="/copilot" element={<Copilot />} />

            {/* Alerts */}
            <Route path="/alerts" element={<Alerts />} />

            {/* Investigation */}
            <Route
              path="/investigation"
              element={<Investigation />}
            />

            {/* Reports */}
            <Route
              path="/reports"
              element={<Reports />}
            />

            {/* Assets */}
            <Route
              path="/assets"
              element={<Assets />}
            />

            {/* Settings */}
            <Route
              path="/settings"
              element={<Settings />}
            />

            {/* Profile */}
            <Route
              path="/profile"
              element={<Profile />}
            />
          </Routes>
        </div>
      </div>
    </>
  );
}

export default App;