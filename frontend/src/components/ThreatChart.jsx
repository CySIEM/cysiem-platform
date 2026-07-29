import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

import { getThreatActivity } from "../services/api";
import "./ThreatChart.css";

const ThreatChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadThreatData = async () => {
      try {
        const response = await getThreatActivity();
        setData(response);
      } catch (error) {
        console.error("Failed to load threat activity:", error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    loadThreatData();
  }, []);

  return (
    <div className="chart-card">
      <h3>Threat Activity (Last 7 Days)</h3>

      {loading ? (
        <p>Loading chart...</p>
      ) : data.length === 0 ? (
        <p>No threat activity available.</p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="day" />

            <YAxis />

            <Tooltip />

            <Line
              type="monotone"
              dataKey="threats"
              stroke="#2563eb"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default ThreatChart;