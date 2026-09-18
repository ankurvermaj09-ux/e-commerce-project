import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts";

const Colors = ["#22c55e", "#ef4444", "#f59e0b", "#3b82f6"];

export default function OrderRatioChart({ data }) {
  const ChartData = [
    { name: "Delivered", value: data?.delivered || 0 },
    { name: "Cancelled", value: data?.cancelled || 0 },
    { name: "Pending", value: data?.pending || 0 },
    { name: "Shipped", value: data?.shipped || 0 }
  ];

  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={ChartData}
            cx="50%"
            cy="50%"
            outerRadius={90}
            dataKey="value"
            label
          >
            {ChartData.map((_, index) => (
              <Cell key={index} fill={Colors[index]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}