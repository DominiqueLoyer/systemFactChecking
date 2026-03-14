
import React from 'react';

interface MetricCardProps {
  label: string;
  value: number;
  color?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, color = "bg-blue-500" }) => {
  const percentage = Math.min(100, Math.max(0, value * 100));
  
  return (
    <div className="flex flex-col gap-1 w-full">
      <div className="flex justify-between text-xs font-medium text-slate-400">
        <span>{label}</span>
        <span>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
        <div 
          className={`h-full ${color} transition-all duration-500`} 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default MetricCard;
