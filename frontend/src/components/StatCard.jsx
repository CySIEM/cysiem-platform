import "./StatCard.css";

const StatCard = ({ title, value, color }) => {
  return (
    <div className="stat-card">
      <div
        className="card-indicator"
        style={{ backgroundColor: color }}
      ></div>

      <div className="card-content">
        <h4>{title}</h4>
        <h2>{value}</h2>
      </div>
    </div>
  );
};

export default StatCard;