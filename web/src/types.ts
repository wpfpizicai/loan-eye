import React from 'react';

export type ViewType = 'overview' | 'details' | 'industry';

export interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: React.ReactNode;
  iconBgColor: string;
}

export interface NoteData {
  title: string;
  competitor: string;
  interactions: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  time: string;
  imageUrl?: string;
}
