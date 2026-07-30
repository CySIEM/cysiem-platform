import { useEffect, useState } from "react";
import { Search, Monitor } from "lucide-react";
import { getAssets } from "../services/api";
import "./Assets.css";

const Assets = () => {
  const [assets, setAssets] = useState([]);
  const [filteredAssets, setFilteredAssets] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const loadAssets = async () => {
      const data = await getAssets();

      setAssets(data);
      setFilteredAssets(data);
    };

    loadAssets();
  }, []);

  useEffect(() => {
    const result = assets.filter(
      (asset) =>
        asset.hostname.toLowerCase().includes(search.toLowerCase()) ||
        asset.ip_address.includes(search)
    );

    setFilteredAssets(result);
  }, [search, assets]);

  const handleView = (asset) => {
    window.alert(
`Asset Details

Hostname: ${asset.hostname}

IP Address: ${asset.ip_address}

Operating System: ${asset.operating_system}

Type: ${asset.asset_type}

Owner: ${asset.owner}

Status: ${asset.status}

Risk: ${asset.risk_level}

Last Scan: ${asset.last_scan}`
    );
  };

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

            {filteredAssets.map((asset) => (

              <tr key={asset.id}>

                <td>
                  <Monitor size={16} style={{ marginRight: 8 }} />
                  {asset.hostname}
                </td>

                <td>{asset.ip_address}</td>

                <td>{asset.operating_system}</td>

                <td>
                  <span className={`status ${asset.status.toLowerCase()}`}>
                    {asset.status}
                  </span>
                </td>

                <td>
                  <span className={`risk ${asset.risk_level.toLowerCase()}`}>
                    {asset.risk_level}
                  </span>
                </td>

                <td>

                  <button
                    className="view-btn"
                    onClick={() => handleView(asset)}
                  >
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