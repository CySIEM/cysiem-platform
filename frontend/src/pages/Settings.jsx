import { useState } from "react";
import {
  User,
  Bell,
  Bot,
  Palette,
  Server,
  Save,
} from "lucide-react";
import "./Settings.css";

const Settings = () => {
  const [settings, setSettings] = useState({
    name: "SOC Analyst",
    email: "analyst@cysiem.com",
    apiUrl: "http://127.0.0.1:8000",
    emailAlerts: true,
    desktopAlerts: true,
    criticalOnly: false,
    darkMode: false,
    aiModel: "Llama 3.2",
    temperature: 0.7,
  });

  const handleChange = (field, value) => {
    setSettings((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h2>Settings</h2>
        <p>Manage your CySIEM preferences and system configuration.</p>
      </div>

      {/* Profile */}
      <div className="settings-card">
        <h3><User size={20} /> Profile</h3>

        <label>Name</label>
        <input
          type="text"
          value={settings.name}
          onChange={(e) => handleChange("name", e.target.value)}
        />

        <label>Email</label>
        <input
          type="email"
          value={settings.email}
          onChange={(e) => handleChange("email", e.target.value)}
        />
      </div>

      {/* Notifications */}
      <div className="settings-card">
        <h3><Bell size={20} /> Notifications</h3>

        <label>
          <input
            type="checkbox"
            checked={settings.emailAlerts}
            onChange={(e) =>
              handleChange("emailAlerts", e.target.checked)
            }
          />
          Email Alerts
        </label>

        <label>
          <input
            type="checkbox"
            checked={settings.desktopAlerts}
            onChange={(e) =>
              handleChange("desktopAlerts", e.target.checked)
            }
          />
          Desktop Notifications
        </label>

        <label>
          <input
            type="checkbox"
            checked={settings.criticalOnly}
            onChange={(e) =>
              handleChange("criticalOnly", e.target.checked)
            }
          />
          Critical Alerts Only
        </label>
      </div>

      {/* AI */}
      <div className="settings-card">
        <h3><Bot size={20} /> AI Configuration</h3>

        <label>AI Model</label>

        <select
          value={settings.aiModel}
          onChange={(e) => handleChange("aiModel", e.target.value)}
        >
          <option>Llama 3.2</option>
          <option>Gemma 2</option>
          <option>Mistral</option>
        </select>

        <label>Temperature</label>

        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={settings.temperature}
          onChange={(e) =>
            handleChange("temperature", e.target.value)
          }
        />
      </div>

      {/* Appearance */}
      <div className="settings-card">
        <h3><Palette size={20} /> Appearance</h3>

        <label>
          <input
            type="checkbox"
            checked={settings.darkMode}
            onChange={(e) =>
              handleChange("darkMode", e.target.checked)
            }
          />
          Enable Dark Mode
        </label>
      </div>

      {/* Backend */}
      <div className="settings-card">
        <h3><Server size={20} /> Backend</h3>

        <label>API URL</label>

        <input
          type="text"
          value={settings.apiUrl}
          onChange={(e) =>
            handleChange("apiUrl", e.target.value)
          }
        />

        <p className="status">
          Connection Status:
          <span className="online"> Online</span>
        </p>
      </div>

      <button className="save-btn">
        <Save size={18} />
        Save Settings
      </button>
    </div>
  );
};

export default Settings;