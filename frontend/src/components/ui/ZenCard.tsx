import React from 'react';

interface ZenCardProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const ZenCard: React.FC<ZenCardProps> = ({ children, className = '', style }) => {
  return (
    <div 
      className={`bg-paper/80 border border-line rounded-[20px] p-7 shadow-[0_20px_50px_rgba(120,100,70,0.08)] backdrop-blur-[2px] ${className}`}
      style={style}
    >
      {children}
    </div>
  );
};
