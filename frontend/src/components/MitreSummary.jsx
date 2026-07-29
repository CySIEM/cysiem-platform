import "./MitreSummary.css";

const MitreSummary = () => {
  return (
    <div className="mitre-card">
      <h3>MITRE ATT&CK Summary</h3>

      <div className="technique">
        <span>T1059</span>
        <p>Command and Scripting Interpreter</p>
      </div>

      <div className="technique">
        <span>T1190</span>
        <p>Exploit Public-Facing Application</p>
      </div>

      <div className="technique">
        <span>T1110</span>
        <p>Brute Force</p>
      </div>

      <div className="technique">
        <span>T1566</span>
        <p>Phishing</p>
      </div>
    </div>
  );
};

export default MitreSummary;