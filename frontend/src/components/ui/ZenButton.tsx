import React from 'react';

interface ZenButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost';
  children: React.ReactNode;
}

export const ZenButton: React.FC<ZenButtonProps> = ({ variant = 'primary', children, className = '', ...props }) => {
  const baseStyles = "rounded-full px-5 py-[11px] font-medium transition-all duration-200 hover:scale-[1.03] disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-moss text-paper hover:shadow-[0_10px_24px_rgba(92,106,87,0.24)]",
    ghost: "bg-transparent text-moss border border-moss"
  };

  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
