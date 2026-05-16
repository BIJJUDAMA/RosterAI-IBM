import React from 'react';
import { ShieldAlert, ShieldCheck, Zap, Activity } from 'lucide-react';
import { Bottleneck } from '../../types';

interface BottleneckReportProps {
  bottlenecks: Bottleneck[];
}

export const BottleneckReport: React.FC<BottleneckReportProps> = ({ bottlenecks = [] }) => {
  const atRisk = bottlenecks.filter(b => b?.is_at_risk);
  const healthy = bottlenecks.filter(b => !b?.is_at_risk);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity size={24} className="text-ink" />
          <h2 className="font-display text-[32px] tracking-tight">Project Health & Risk</h2>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-clay/10 text-clay rounded-full text-[12px] font-bold uppercase tracking-widest border border-clay/20">
            <ShieldAlert size={14} /> {atRisk.length} At Risk
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-moss/10 text-moss rounded-full text-[12px] font-bold uppercase tracking-widest border border-moss/20">
            <ShieldCheck size={14} /> {healthy.length} Balanced
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {bottlenecks.map((b) => (
          <div 
            key={b.project_id} 
            className={`
              p-6 rounded-[32px] border-2 transition-all duration-300
              ${b.is_at_risk 
                ? 'border-clay/40 bg-clay/[0.03] shadow-lg hover:shadow-xl hover:border-clay/60' 
                : 'border-line/40 bg-white/50 hover:bg-white shadow-sm'
              }
            `}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="font-display text-[22px] leading-tight m-0 max-w-[70%]">{b.project_title}</h3>
              <div className="flex flex-col items-end">
                <span className="text-[10px] uppercase tracking-widest font-black opacity-40">Health</span>
                <span className={`font-display text-[24px] ${b.health_score < 50 ? 'text-clay' : 'text-moss'}`}>
                  {b.health_score}%
                </span>
              </div>
            </div>

            <p className="text-[12px] text-ink/60 mb-6 leading-relaxed italic">
              "{b.explanation}"
            </p>

            {b.critical_skills.length > 0 && (
              <div className="flex flex-col gap-3">
                <span className="text-[9px] uppercase tracking-[0.2em] font-black text-clay">Critical Skill Gaps</span>
                <div className="flex flex-wrap gap-2">
                  {b.critical_skills.map((skill) => (
                    <span 
                      key={skill} 
                      className="px-3 py-1.5 bg-clay text-paper text-[10px] font-black uppercase tracking-widest rounded-full border-2 border-clay/20"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {!b.is_at_risk && (
              <div className="flex items-center gap-2 text-moss">
                <Zap size={14} className="fill-moss/20" />
                <span className="text-[10px] font-black uppercase tracking-[0.2em]">Technically Saturated</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
