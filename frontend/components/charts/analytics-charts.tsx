"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

const volume = [
  { day: "Mon", conversations: 42, voice: 9 },
  { day: "Tue", conversations: 58, voice: 14 },
  { day: "Wed", conversations: 51, voice: 12 },
  { day: "Thu", conversations: 73, voice: 19 },
  { day: "Fri", conversations: 64, voice: 16 },
  { day: "Sat", conversations: 38, voice: 8 },
  { day: "Sun", conversations: 31, voice: 7 }
];

const agents = [
  { agent: "FAQ", usage: 61 },
  { agent: "Lead", usage: 18 },
  { agent: "Scheduling", usage: 13 },
  { agent: "Escalation", usage: 8 }
];

export function VolumeChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={volume}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="day" />
        <YAxis />
        <Tooltip />
        <Area dataKey="conversations" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.18} />
        <Area dataKey="voice" stroke="#10b981" fill="#10b981" fillOpacity={0.16} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function AgentUsageChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={agents}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="agent" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="usage" fill="#3b82f6" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
