import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import "./TopThreats.css";

const data = [
  { name: "Malware", value: 35 },
  { name: "SQL Injection", value: 25 },
  { name: "Brute Force", value: 20 },
  { name: "Phishing", value: 15 },
  { name: "XSS", value: 5 },
];

const COLORS = [
  "#EF4444",
  "#F97316",
  "#FACC15",
  "#3B82F6",
  "#10B981",
];

const TopThreats = () => {
  return (
    <div className="top-threats-card">
      <h3>Top Threat Categories</h3>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            outerRadius={100}
            label
          >
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>

          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TopThreats;