import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Briefcase, GitMerge } from 'lucide-react';
import { Member, Project, Assignment } from '../../types';

interface SidebarProps {
  members?: Member[];
  projects?: Project[];
  assignments?: Assignment[];
  selectedMemberId?: number | null;
  setSelectedMemberId?: (id: number | null) => void;
  handleManualAssign?: (memberId: number, projectId: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  members,
  projects,
  assignments,
  selectedMemberId,
  setSelectedMemberId,
  handleManualAssign
}) => {
  const location = useLocation();
  const activeTab = location.pathname === '/' ? 'dashboard' : location.pathname.slice(1);

  const navItems = [
    { id: 'dashboard', path: '/', label: 'Overview', icon: LayoutDashboard },
    { id: 'members', path: '/members', label: 'Members', icon: Users },
    { id: 'projects', path: '/projects', label: 'Projects', icon: Briefcase },
    { id: 'alignment', path: '/alignment', label: 'Alignment', icon: GitMerge },
  ];

  const scrollToMember = (id: number) => {
    const el = document.getElementById(`member-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const scrollToProject = (id: string) => {
    const el = document.getElementById(`project-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <aside className="w-[260px] shrink-0 flex flex-col gap-[10px]">
      {navItems.map(({ id, path, label, icon: Icon }) => (
        <NavLink
          key={id}
          to={path}
          className={({ isActive }) => `
            flex items-center gap-[14px] px-6 py-4 rounded-[18px] text-ink font-medium transition-all duration-400 ease-[cubic-bezier(0.16,1,0.3,1)] text-left group
            ${isActive 
              ? 'bg-paper border border-clay shadow-[0_10px_30px_rgba(155,123,86,0.08)] opacity-100 translate-x-[6px]' 
              : 'bg-transparent border border-transparent opacity-70 hover:bg-white/45 hover:border-line hover:opacity-100'
            }
          `}
        >
          <Icon className="shrink-0 transition-transform duration-300 group-hover:scale-110" size={20} />
          {label}
        </NavLink>
      ))}

      {activeTab === 'members' && members && members.length > 0 && (
        <div className="mt-4 flex flex-col gap-2 transition-all duration-500 opacity-100 animate-in fade-in slide-in-from-top-4">
          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-moss/70 mb-2 px-6">Members Directory</h4>
          <div className="flex flex-col gap-1 mx-3">
            {members.map(m => (
              <button 
                key={m.id}
                onClick={() => scrollToMember(m.id)}
                className="w-full shrink-0 text-left px-3 py-2 text-[13px] text-ink/80 hover:text-ink hover:bg-white/40 rounded-lg transition-colors truncate"
              >
                {m.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'projects' && projects && projects.length > 0 && (
        <div className="mt-4 flex flex-col gap-2 transition-all duration-500 opacity-100 animate-in fade-in slide-in-from-top-4">
          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-moss/70 mb-2 px-6">Projects Directory</h4>
          <div className="flex flex-col gap-1 mx-3">
            {projects.map(p => (
              <button 
                key={p.id}
                onClick={() => scrollToProject(p.id)}
                className="w-full shrink-0 text-left px-3 py-2 text-[13px] text-ink/80 hover:text-ink hover:bg-white/40 rounded-lg transition-colors truncate"
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'alignment' && projects && projects.length > 0 && (
        <div className="mt-4 flex flex-col gap-2 transition-all duration-500 opacity-100 animate-in fade-in slide-in-from-top-4">
          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-moss/70 mb-2 px-6">Project Structure</h4>
          <div className="flex flex-col gap-0 mx-3 text-[13px] text-ink">
            {projects.map(p => {
              const team = assignments?.filter(a => a.project_id === p.id) || [];
              return (
                <div key={p.id} className="flex flex-col">
                  <button 
                    onClick={() => {
                      if (selectedMemberId && handleManualAssign) {
                        handleManualAssign(selectedMemberId, p.id.toString());
                        setSelectedMemberId?.(null);
                      } else {
                        scrollToProject(p.id);
                      }
                    }}
                    className={`w-full text-left px-3 py-1 hover:text-ink rounded transition-all truncate font-display text-[15px] font-medium flex items-center justify-between group/p ${selectedMemberId ? 'bg-clay/10 ring-1 ring-clay/20 text-clay animate-pulse' : 'hover:bg-white/40 text-ink'}`}
                  >
                    {p.title}
                    {selectedMemberId && <span className="text-[10px] font-bold opacity-0 group-hover/p:opacity-100 transition-opacity">MOVE HERE</span>}
                  </button>
                  {team.map((a, idx) => {
                    const member = members?.find(m => m.id === a.candidate_id);
                    const isLast = idx === team.length - 1;
                    const isSelected = selectedMemberId === member?.id;
                    return (
                      <button 
                        key={a.candidate_id} 
                        onClick={() => setSelectedMemberId?.(isSelected ? null : member?.id || null)}
                        className={`w-full px-6 py-0.5 whitespace-nowrap flex items-center gap-1.5 font-body transition-all hover:bg-white/20 rounded ${isSelected ? 'text-clay font-bold bg-white/40' : 'opacity-70 text-ink'}`}
                      >
                        <span className="text-clay/60">{isLast ? '└── ' : '├── '}</span>
                        <span className="truncate">{member?.name}</span>
                        <span className="text-[10px] opacity-50 font-bold tracking-tighter">({member?.is_senior ? 'S' : 'J'})</span>
                      </button>
                    );
                  })}
                  {team.length === 0 && (
                    <div className="px-6 py-0.5 opacity-40 italic font-body text-[12px]">
                      <span className="text-clay/60">└── </span>(empty)
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </aside>
  );
};
