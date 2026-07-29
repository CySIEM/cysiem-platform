import { useEffect, useState } from "react";
import { Search, Monitor } from "lucide-react";
import "./Assets.css";

const sampleAssets = [
  {
    hostname: "Server-01",
    ip: "192.168.1.10",
    os: "Ubuntu 22.04",
    status: "Online",
    risk: "High",
  },
  {
    hostname: "Workstation-12",
    ip: "192.168.1.45",
    os: "Windows 11",
    status: "Online",
    risk: "Medium",
  },
  {
    hostname: "Firewall",
    ip: "10.0.0.1",
    os: "pfSense",
    status: "Online",
    risk: "Low",
  },
  {
    hostname: "Database-01",
    ip: "192.168.1.20",
    os: "CentOS",
    status: "Offline",
    risk: "Critical",
  },
];

const Assets = () => {
  const [assets, setAssets] = useState([]);
  const [filteredAssets, setFilteredAssets] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    setAssets(sampleAssets);
    setFilteredAssets(sampleAssets);
  }, []);

  useEffect(() => {
    const result = assets.filter(
      (asset) =>
        asset.hostname.toLowerCase().includes(search.toLowerCase()) ||
        asset.ip.includes(search)
    );

    setFilteredAssets(result);
  }, [search, assets]);

  return (
    <div className="assets-page">
      <div className="assets-header">
        <h2>Assets</h2>
        <p>Monitor all connected systems and endpoints.</p>
      </div>

      <div className="assets-search">
        <Search size={18} />
        <input
          type="text"
          placeholder="Search hostname or IP..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="assets-table-card">
        <table>
          <thead>
            <tr>
              <th>Host</th>
              <th>IP Address</th>
              <th>Operating System</th>
              <th>Status</th>
              <th>Risk</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {filteredAssets.map((asset, index) => (
              <tr key={index}>
                <td>
                  <Monitor size={16} style={{ marginRight: 8 }} />
                  {asset.hostname}
                </td>

                <td>{asset.ip}</td>

                <td>{asset.os}</td>

                <td>
                  <span
                    className={`status ${asset.status.toLowerCase()}`}
                  >
                    {asset.status}
                  </span>
                </td>

                <td>
                  <span
                    className={`risk ${asset.risk.toLowerCase()}`}
                  >
                    {asset.risk}
                  </span>
                </td>

                <td>
                  <button className="view-btn">
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Assets;