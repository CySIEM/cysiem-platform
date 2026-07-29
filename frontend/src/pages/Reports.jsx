import { useEffect, useState } from "react";
import { Search, FileText, Download, Eye } from "lucide-react";
import { getReports } from "../services/api";
import "./Reports.css";

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [filteredReports, setFilteredReports] = useState([]);
  const [search, setSearch] = useState("");
  const [type, setType] = useState("All");

  useEffect(() => {
    const loadReports = async () => {
      const data = await getReports();
      setReports(data);
      setFilteredReports(data);
    };

    loadReports();
  }, []);

  useEffect(() => {
    let result = reports;

    if (type !== "All") {
      result = result.filter((report) => report.type === type);
    }

    if (search !== "") {
      result = result.filter(
        (report) =>
          report.title.toLowerCase().includes(search.toLowerCase()) ||
          report.author.toLowerCase().includes(search.toLowerCase())
      );
    }

    setFilteredReports(result);
  }, [search, type, reports]);

  return (
    <div className="reports-page">
      <div className="reports-header">
        <h2>Security Reports</h2>
        <p>View and download generated security reports.</p>
      </div>

      <div className="reports-filters">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search reports..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option>All</option>
          <option>Threat Report</option>
          <option>Audit Report</option>
          <option>Incident Report</option>
        </select>
      </div>

      <div className="reports-grid">
        {filteredReports.length === 0 ? (
          <p>No reports found.</p>
        ) : (
          filteredReports.map((report, index) => (
            <div className="report-card" key={index}>
              <div className="report-icon">
                <FileText size={32} />
              </div>

              <h3>{report.title}</h3>

              <p>
                <strong>Type:</strong> {report.type}
              </p>

              <p>
                <strong>Date:</strong> {report.date}
              </p>

              <p>
                <strong>Author:</strong> {report.author}
              </p>

              <div className="report-actions">
                <button className="view-btn">
                  <Eye size={18} />
                  View
                </button>

                <button className="download-btn">
                  <Download size={18} />
                  Download
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Reports;