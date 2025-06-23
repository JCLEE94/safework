import React, { ReactNode } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: {
    value: number;
    isUp: boolean;
  };
  color: string;
}

export function StatCard({ title, value, icon, trend, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 hover:scale-105">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{value}</p>
          {trend && (
            <div className="flex items-center mt-2">
              {trend.isUp ? (
                <TrendingUp size={16} className="text-green-500" />
              ) : (
                <TrendingDown size={16} className="text-red-500" />
              )}
              <span className={`text-sm ml-1 ${trend.isUp ? 'text-green-500' : 'text-red-500'}`}>
                {Math.abs(trend.value)}%
              </span>
            </div>
          )}
        </div>
        <div className={`p-4 rounded-full ${color} bg-opacity-20`}>
          {icon}
        </div>
      </div>
    </div>
  );
}