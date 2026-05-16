import React from 'react';
import { ZenCard } from '../ui/ZenCard';
import { ZenButton } from '../ui/ZenButton';
import { Network, AlertCircle, RefreshCcw, Activity, Map as MapIcon } from 'lucide-react';
import { Member, Project, Allocation, IngestionError, Bottleneck } from '../../types';
import { BottleneckReport } from './BottleneckReport';
import { TopologyMap } from './TopologyMap';

interface DashboardProps {
  members: Member[];
  projects: Project[];
  assignments: Allocation[];
  ingestionErrors: IngestionError[];
  bottlenecks: Bottleneck[];
  showGraph: boolean;
  setShowGraph: (show: boolean) => void;
  handleRetryAll: () => Promise<void>;
  handleRetrySpecific: (id: number) => Promise<void>;
}

export const Dashboard: React.FC<DashboardProps> = ({
  members, projects, assignments, ingestionErrors, bottlenecks, showGraph, setShowGraph,
  handleRetryAll, handleRetrySpecific
}) => {
  const stats = [
    { label: 'Members', value: members.length, sub: 'Active Members' },
    { label: 'Initiatives', value: projects.length, sub: 'Active Projects' },
    { label: 'Alignment', value: assignments.length, sub: 'Team Allocations' },
  ];

  return (
    <div className="flex flex-col gap-12">

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map(stat => (
          <ZenCard key={stat.label} className="flex flex-col items-center justify-center py-10 text-center">
            <span className="text-xs uppercase tracking-[0.12em] text-moss mb-2">{stat.label}</span>
            <span className="font-display text-[64px] leading-[0.95] my-[10px]">{stat.value}</span>
            <p className="text-[#6d645a] text-[13px] mt-2">{stat.sub}</p>
          </ZenCard>
        ))}
      </div>

      {/* 2. Topology Map (Full Width) */}
      <TopologyMap
        members={members}
        projects={projects}
        assignments={assignments}
      />

      {/* 3. Ingestion Errors (Alert Style) */}
      {ingestionErrors.length > 0 && (
        <ZenCard className="border-clay/20 bg-clay/[0.02]">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-clay/10 rounded-full text-clay">
                <AlertCircle size={20} />
              </div>
              <div>
                <h2 className="font-display text-[24px] leading-tight text-ink">Intelligence Bottlenecks</h2>
                <p className="text-[#6d645a] text-[13px]">{ingestionErrors.length} documents require manual review or retry</p>
              </div>
            </div>
            <ZenButton
              variant="outline"
              onClick={handleRetryAll}
              className="flex items-center gap-2 border-clay/30 text-clay hover:bg-clay hover:text-paper transition-all"
            >
              <RefreshCcw size={16} /> Recover All
            </ZenButton>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-line">
                  <th className="py-3 px-4 text-[11px] uppercase tracking-widest text-moss font-medium">Filename</th>
                  <th className="py-3 px-4 text-[11px] uppercase tracking-widest text-moss font-medium">Type</th>
                  <th className="py-3 px-4 text-[11px] uppercase tracking-widest text-moss font-medium">Error Trace</th>
                  <th className="py-3 px-4 text-[11px] uppercase tracking-widest text-moss font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {ingestionErrors.map((error) => (
                  <tr key={error.id} className="border-b border-line/50 hover:bg-paper-dark/30 transition-colors">
                    <td className="py-4 px-4 text-[13px] font-medium text-ink">{error.filename}</td>
                    <td className="py-4 px-4 text-[12px] text-[#6d645a] capitalize">{error.file_type}</td>
                    <td className="py-4 px-4 text-[12px] text-clay/80 max-w-[400px] truncate" title={error.error_message}>
                      {error.error_message}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button
                        onClick={() => handleRetrySpecific(error.id)}
                        className="p-2 text-[#6d645a] hover:text-clay hover:bg-clay/10 rounded-full transition-all"
                        title="Retry Ingestion"
                      >
                        <RefreshCcw size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ZenCard>
      )}

      {/* 4. Bottleneck Report */}
      <BottleneckReport bottlenecks={bottlenecks} />
    </div>
  );
};
