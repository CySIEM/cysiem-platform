import { useState } from "react";
import { Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";

import Dashboard from "./pages/Dashboard";
import Copilot from "./pages/Copilot";
import Alerts from "./pages/Alerts";
import Investigation from "./pages/Investigation";
import Reports from "./pages/Reports";
import Assets from "./pages/Assets";
import Settings from "./pages/Settings";

import "./App.css";

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
  };

  return (
    <>
      <Navbar toggleSidebar={toggleSidebar} />

      <div className="main-container">
        <Sidebar
          isOpen={isSidebarOpen}
          toggleSidebar={toggleSidebar}
        />

        <div className="content">
          <Routes>
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
          </Routes>
        </div>
      </div>
    </>
  );
}

export default App;