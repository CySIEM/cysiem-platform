import React from "react";
import "./Navbar.css";
import { UserCircle, Menu } from "lucide-react";

const Navbar = ({ toggleSidebar }) => {
  return (
    <nav className="navbar">
      <div className="navbar-left">

        {/* Mobile Menu Button */}
        <button className="menu-btn" onClick={toggleSidebar}>
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

        <button className="notification-btn">🔔</button>

        <div className="profile">
          <UserCircle size={38} color="#fff" />
          <span>Admin</span>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;