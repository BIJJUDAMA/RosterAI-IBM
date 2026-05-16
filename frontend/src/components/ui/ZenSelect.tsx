import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

interface ZenSelectProps {
  value: string | number;
  onChange: (val: string) => void;
  options: { value: string | number; label: string }[];
  placeholder?: string;
}

export const ZenSelect: React.FC<ZenSelectProps> = ({ value, onChange, options, placeholder = "Select..." }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectedOption = options.find(opt => String(opt.value) === String(value));

  return (
    <div className="relative w-full text-[14px]" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between bg-white/70 border ${isOpen ? 'border-moss bg-white shadow-[0_0_0_3px_rgba(92,106,87,0.1)]' : 'border-line'} rounded-[10px] px-3 py-2.5 text-ink font-body transition-all duration-200 outline-none hover:bg-white`}
      >
        <span className="truncate pr-2">
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown size={16} className={`text-moss shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-max min-w-full right-0 mt-2 bg-paper border border-line rounded-[12px] shadow-[0_15px_40px_rgba(37,34,32,0.12)] overflow-hidden">
          <ul className="max-h-[300px] overflow-y-auto py-1 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-line/60 [&::-webkit-scrollbar-thumb]:rounded-full">
            {options.map((opt) => (
              <li
                key={opt.value}
                onClick={() => {
                  onChange(String(opt.value));
                  setIsOpen(false);
                }}
                className={`px-4 py-3 cursor-pointer transition-colors duration-150 flex items-center whitespace-nowrap ${
                  String(opt.value) === String(value)
                    ? 'bg-clay/15 text-moss font-medium' 
                    : 'text-ink hover:bg-white/60 hover:text-moss'
                }`}
              >
                {opt.label}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
