import React from 'react';
import { STATUS_COLORS } from '../../constants';

interface BadgeProps {
  value: string;
  label?: string;
  type?: keyof typeof STATUS_COLORS;
}

export function Badge({ value, label, type }: BadgeProps) {
  const colorClass = type && STATUS_COLORS[type] ? STATUS_COLORS[type] : 'bg-gray-100 text-gray-800';
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {label || value}
    </span>
  );
}