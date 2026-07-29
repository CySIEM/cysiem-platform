import {
  ScanSearch,
  FileText,
  Bot,
  RefreshCw,
} from "lucide-react";

import "./QuickActions.css";

const QuickActions = () => {
  const handleAction = (action) => {
    alert(`${action} clicked!`);
  };

  return (
    <div className="quick-actions-card">
      <h3>Quick Actions</h3>

      <div className="quick-actions-grid">
        <button
          className="action-btn"
          onClick={() => handleAction("Run Scan")}
        >
          <ScanSearch size={24} />
          <span>Run Scan</span>
        </button>

        <button
          className="action-btn"
          onClick={() => handleAction("Generate Report")}
        >
          <FileText size={24} />
          <span>Generate Report</span>
        </button>

        <button
          className="action-btn"
          onClick={() => handleAction("AI Analysis")}
        >
          <Bot size={24} />
          <span>AI Analysis</span>
        </button>

        <button
          className="action-btn"
          onClick={() => handleAction("Refresh Dashboard")}
        >
          <RefreshCw size={24} />
          <span>Refresh</span>
        </button>
      </div>
    </div>
  );
};

export default QuickActions;