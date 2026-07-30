import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { getAlerts } from "../services/api";
import "./Alerts.css";

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("All");
  const [status, setStatus] = useState("All");

  useEffect(() => {
    const loadAlerts = async () => {
      const data = await getAlerts();
      setAlerts(data);
      setFilteredAlerts(data);
    };

    loadAlerts();
  }, []);

  useEffect(() => {
    let result = alerts;

    if (severity !== "All") {
      result = result.filter((a) => a.severity === severity);
    }

    if (status !== "All") {
      result = result.filter((a) => a.status === status);
    }

    if (search !== "") {
      result = result.filter(
        (a) =>
          a.title.toLowerCase().includes(search.toLowerCase()) ||
          a.source.toLowerCase().includes(search.toLowerCase())
      );
    }

    setFilteredAlerts(result);
  }, [search, severity, status, alerts]);

  const handleView = (selectedAlert) => {
    window.alert(
      `Alert Details

Title: ${selectedAlert.title}

Source: ${selectedAlert.source}

Severity: ${selectedAlert.severity}

Status: ${selectedAlert.status}`
    );
  };

  return (
    <div className="alerts-page">

      <div className="alerts-header">
        <h2>Security Alerts</h2>
        <p>Monitor and investigate security threats.</p>
      </div>

      <div className="filters">

        <div className="search-box">
          <Search size={18} />

          <input
            type="text"
            placeholder="Search alerts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

        </div>

        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
        >
          <option>All</option>
          <option>Critical</option>
          <option>High</option>
          <option>Medium</option>
          <option>Low</option>
        </select>

        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option>All</option>
          <option>Open</option>
          <option>Investigating</option>
          <option>Closed</option>
          <option>Resolved</option>
        </select>

      </div>

      <div className="table-card">

        <table>

          <thead>

            <tr>
              <th>Source</th>
              <th>Threat</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Action</th>
            </tr>

          </thead>

          <tbody>

            {filteredAlerts.length === 0 ? (
              <tr>
                <td colSpan="5">No alerts found.</td>
              </tr>
            ) : (
              filteredAlerts.map((alert) => (
                <tr key={alert.id}>

                  <td>{alert.source}</td>

                  <td>{alert.title}</td>

                  <td>
                    <span className={`severity ${alert.severity.toLowerCase()}`}>
                      {alert.severity}
                    </span>
                  </td>

                  <td>{alert.status}</td>

                  <td>
                    <button
                      className="view-btn"
                      onClick={() => handleView(alert)}
                    >
                      View
                    </button>
                  </td>

                </tr>
              ))
            )}

          </tbody>

        </table>

      </div>

    </div>
  );
};

export default Alerts;