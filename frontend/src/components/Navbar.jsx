import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Navbar.css";

import {
  UserCircle,
  Menu,
  Settings,
  User,
  LogOut,
  Bell,
} from "lucide-react";

const Navbar = ({ toggleSidebar }) => {
  const [open, setOpen] = useState(false);

  const dropdownRef = useRef(null);

  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target)
      ) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );
    };
  }, []);

  // ===========================
  // Profile
  // ===========================

  const handleProfile = () => {
    navigate("/profile");
    setOpen(false);
  };

  // ===========================
  // Settings
  // ===========================

  const handleSettings = () => {
    navigate("/settings");
    setOpen(false);
  };

  // ===========================
  // Logout
  // ===========================

  const handleLogout = () => {
    const confirmLogout = window.confirm(
      "Do you want to logout?"
    );

    if (confirmLogout) {
      localStorage.clear();

      navigate("/");
    }

    setOpen(false);
  };

  return (
    <nav className="navbar">

      <div className="navbar-left">

        <button
          className="menu-btn"
          onClick={toggleSidebar}
        >
          <Menu size={28} />
        </button>

        <h2>🛡️ CySIEM Platform</h2>

      </div>

      <div className="navbar-right">

        <input
          type="text"
          placeholder="Search..."
          className="search-bar"
        />

        <button className="notification-btn">
          <Bell size={22} />
        </button>

        <div
          className="profile"
          ref={dropdownRef}
        >

          <div
            className="profile-info"
            onClick={() => setOpen(!open)}
          >
            <UserCircle
              size={38}
              color="#fff"
            />

            <span>Admin</span>
          </div>

          {open && (

            <div className="profile-dropdown">

              <button onClick={handleProfile}>
                <User size={18} />
                My Profile
              </button>

              <button onClick={handleSettings}>
                <Settings size={18} />
                Settings
              </button>

              <button onClick={handleLogout}>
                <LogOut size={18} />
                Logout
              </button>

            </div>

          )}

        </div>

      </div>

    </nav>
  );
};

export default Navbar;