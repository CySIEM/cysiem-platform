import {
  ShieldAlert,
  Bug,
  Clock,
  FileText,
  CheckCircle,
} from "lucide-react";
import "./Investigation.css";

const Investigation = () => {
  return (
    <div className="investigation-page">

      <div className="page-header">
        <h2>Threat Investigation</h2>
        <p>Analyze incidents and review AI-generated recommendations.</p>
      </div>

      <div className="investigation-grid">

        {/* Incident Details */}
        <div className="card">
          <h3><ShieldAlert size={20} /> Incident Details</h3>

          <div className="details">
            <p><strong>Threat:</strong> SQL Injection</p>
            <p><strong>Severity:</strong> High</p>
            <p><strong>Status:</strong> Active</p>
            <p><strong>Source:</strong> Web Server</p>
            <p><strong>Detected:</strong> 28 July 2026 - 10:20 AM</p>
          </div>
        </div>

        {/* AI Analysis */}
        <div className="card">
          <h3><Bug size={20} /> AI Analysis</h3>

          <p>
            The detected SQL Injection attack attempted to manipulate database
            queries through unsanitized user input. Immediate mitigation is
            recommended to prevent unauthorized access.
          </p>
        </div>

        {/* MITRE Mapping */}
        <div className="card">
          <h3><FileText size={20} /> MITRE ATT&CK</h3>

          <ul>
            <li>T1190 - Exploit Public-Facing Application</li>
            <li>T1059 - Command and Scripting Interpreter</li>
          </ul>
        </div>

        {/* Timeline */}
        <div className="card">
          <h3><Clock size={20} /> Timeline</h3>

          <ul className="timeline">
            <li>10:20 - Threat Detected</li>
            <li>10:22 - Alert Generated</li>
            <li>10:25 - AI Investigation Started</li>
            <li>10:30 - Analyst Assigned</li>
          </ul>
        </div>

        {/* Recommendations */}
        <div className="card full-width">
          <h3><CheckCircle size={20} /> Recommended Actions</h3>

          <ul>
            <li>✔ Block suspicious IP address</li>
            <li>✔ Enable Web Application Firewall rules</li>
            <li>✔ Patch vulnerable endpoint</li>
            <li>✔ Review database logs</li>
            <li>✔ Rotate exposed credentials</li>
          </ul>
        </div>

      </div>
    </div>
  );
};

export default Investigation;