import React, { useState, useRef } from 'react';
import { Network, Pencil, Trash2, UploadCloud, Check, X } from 'lucide-react';
import { ZenSelect } from '../ui/ZenSelect';
import { Member, Project } from '../../types';

interface MembersProps {
  members: Member[];
  projects: Project[];
  ingesting: boolean;
  handleIngest: () => void;
  toggleSeniority: (id: number, currentStatus: boolean) => void;
  handleManualAssign: (memberId: number, projectId: string) => void;
  handleUpdateName: (id: number, name: string) => void;
  handleDeleteMember: (id: number) => void;
  handleUpdateResume: (id: number, file: File) => void;
}

export const Members: React.FC<MembersProps> = ({
  members, projects, toggleSeniority, handleManualAssign,
  handleUpdateName, handleDeleteMember, handleUpdateResume
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditingName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeMemberId, setActiveMemberId] = useState<number | null>(null);

  const projectOptions = [
    { value: "", label: "Auto Align" },
    ...projects.map(p => ({ value: p.id, label: p.title }))
  ];

  const startEditing = (m: Member) => {
    setEditingId(m.id);
    setEditingName(m.name);
  };

  const saveName = (id: number) => {
    handleUpdateName(id, editName);
    setEditingId(null);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && activeMemberId) {
      handleUpdateResume(activeMemberId, e.target.files[0]);
    }
  };

  const filteredMembers = members.filter(m => {
    const searchLower = searchQuery.toLowerCase();
    const skills = m.skills || [];
    const skillMatch = skills.some(s => s.toLowerCase().includes(searchLower));
    return (
      m.name.toLowerCase().includes(searchLower) ||
      skillMatch ||
      m.developer_summary?.toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="flex flex-col gap-6">
      <input type="file" ref={fileInputRef} onChange={onFileChange} className="hidden" accept=".pdf" />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-[clamp(30px,4vw,48px)] leading-[0.95] mb-1">Members</h2>
          <p className="text-[#5f574e] mb-5">Available members and skill profiles</p>
        </div>
      </div>

      <div className="flex gap-3 mb-6">
        <div className="grow relative">
          <Network className="absolute left-4 top-1/2 -translate-y-1/2 text-moss opacity-60" size={20} />
          <input 
            type="text" 
            placeholder="Search by name, skills, or summary..." 
            className="w-full pl-11 h-[50px] text-base bg-white/60 border border-line rounded-[10px] transition-all duration-300 focus:bg-white focus:border-clay focus:shadow-[0_0_0_4px_rgba(155,123,86,0.1)] outline-none"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="flex flex-col gap-6">
        {filteredMembers.map((m, idx) => (
          <div 
            key={m.id} 
            id={`member-${m.id}`}
            className="group relative focus-within:z-50 p-6 border border-line rounded-[16px] bg-white/45 flex flex-col gap-3 transition-all duration-700 ease-out translate-y-0 opacity-100 shadow-[0_20px_50px_rgba(120,100,70,0.08)]"
            style={{ transitionDelay: `${idx * 20}ms` }}
          >
            {/* Hover Actions */}
            <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button 
                onClick={() => { setActiveMemberId(m.id); fileInputRef.current?.click(); }}
                title="Update Resume"
                className="p-2 bg-moss/5 text-moss hover:bg-moss/10 rounded-lg transition-colors"
              >
                <UploadCloud size={14} />
              </button>
              <button 
                onClick={() => handleDeleteMember(m.id)}
                title="Delete Member"
                className="p-2 bg-clay/5 text-clay hover:bg-clay/10 rounded-lg transition-colors"
              >
                <Trash2 size={14} />
              </button>
            </div>

            <div className="flex items-center gap-4 mb-4 flex-nowrap shrink-0 max-w-[85%]">
              {editingId === m.id ? (
                <div className="flex items-center gap-2">
                  <input 
                    className="font-display text-[24px] bg-white border border-line p-1 rounded"
                    value={editName}
                    onChange={(e) => setEditingName(e.target.value)}
                    autoFocus
                  />
                  <button onClick={() => saveName(m.id)} className="text-moss"><Check size={18}/></button>
                  <button onClick={() => setEditingId(null)} className="text-clay"><X size={18}/></button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <h3 className="font-display text-[32px] text-ink uppercase tracking-[0.02em] m-0 whitespace-nowrap overflow-hidden text-ellipsis" title={m.name}>{m.name}</h3>
                  <button onClick={() => startEditing(m)} className="text-moss opacity-0 group-hover:opacity-100 transition-opacity"><Pencil size={14}/></button>
                </div>
              )}
              <button 
                onClick={() => toggleSeniority(m.id, m.is_senior)}
                className={`shrink-0 inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[11px] font-semibold uppercase tracking-wider transition-all duration-300 border border-line ${m.is_senior ? 'bg-ink text-paper border-ink shadow-[0_4px_12px_rgba(37,34,32,0.15)]' : 'bg-white/50 text-moss hover:bg-white hover:-translate-y-[1px]'}`}
              >
                {m.is_senior ? 'Senior' : 'Junior'}
              </button>
            </div>

            <div className="w-full mb-2">
              <div className="flex flex-wrap gap-2">
                  {m.skills && m.skills.map(skill => (
                    <span key={skill} className="inline-flex items-center gap-2 px-3.5 py-2 border border-line rounded-full bg-white/50 text-[13px]">{skill}</span>
                  ))}
              </div>
            </div>

            <div className="w-full mt-2 mb-2">
              <ZenSelect 
                value={m.pinned_project_id || ""}
                onChange={(val) => handleManualAssign(m.id, val)}
                options={projectOptions}
              />
            </div>

            <p className="text-[#6d645a] text-[13px] mt-2 leading-relaxed">
              {m.developer_summary}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
