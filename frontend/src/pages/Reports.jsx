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
      result = result.filter((report) => report.report_type === type);
    }

    if (search !== "") {
      result = result.filter((report) =>
        report.name.toLowerCase().includes(search.toLowerCase())
      );
    }

    setFilteredReports(result);
  }, [search, type, reports]);

  const handleView = (report) => {
    window.alert(
      `Report Details

Name: ${report.name}

Type: ${report.report_type}

Generated On: ${report.generated_on}

Status: ${report.status}`
    );
  };

  const handleDownload = (report) => {
    const content = `
Report Name: ${report.name}

Type: ${report.report_type}

Generated On: ${report.generated_on}

Status: ${report.status}
`;

    const blob = new Blob([content], { type: "text/plain" });

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;

    a.download = `${report.name}.txt`;

    a.click();

    window.URL.revokeObjectURL(url);
  };

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

        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          <option>All</option>
          <option>Weekly</option>
          <option>Monthly</option>
          <option>On Demand</option>
        </select>

      </div>

      <div className="reports-grid">

        {filteredReports.length === 0 ? (
          <p>No reports found.</p>
        ) : (
          filteredReports.map((report) => (
            <div className="report-card" key={report.id}>

              <div className="report-icon">
                <FileText size={32} />
              </div>

              <h3>{report.name}</h3>

              <p>
                <strong>Type:</strong> {report.report_type}
              </p>

              <p>
                <strong>Date:</strong> {report.generated_on}
              </p>

              <p>
                <strong>Status:</strong> {report.status}
              </p>

              <div className="report-actions">

                <button
                  className="view-btn"
                  onClick={() => handleView(report)}
                >
                  <Eye size={18} />
                  View
                </button>

                <button
                  className="download-btn"
                  onClick={() => handleDownload(report)}
                >
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