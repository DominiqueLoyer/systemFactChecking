
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface TFIDFChartProps {
  data: { term: string; score: number }[];
}

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f97316', '#10b981'];

const TFIDFChart: React.FC<TFIDFChartProps> = ({ data }) => {
  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 20 }}>
          <XAxis type="number" hide />
          <YAxis 
            dataKey="term" 
            type="category" 
            tick={{ fill: '#94a3b8', fontSize: 11 }} 
            width={70}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
            itemStyle={{ color: '#60a5fa' }}
          />
          <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={20}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TFIDFChart;
