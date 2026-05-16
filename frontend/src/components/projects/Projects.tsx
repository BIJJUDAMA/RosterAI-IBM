import React, { useState } from 'react';
import { Briefcase, Trash2, XCircle, Edit2, Check, X } from 'lucide-react';
import { Project } from '../../types';
import { ZenButton } from '../ui/ZenButton';
import { api } from '../../api/client';

interface ProjectsProps {
  projects: Project[];
  handleDeleteProject: (id: number) => void;
  handleNukeProjects: () => void;
  handleUpdateTitle: (id: number, title: string) => Promise<void>;
}

export const Projects: React.FC<ProjectsProps> = ({ 
  projects, handleDeleteProject, handleNukeProjects, handleUpdateTitle
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');

  const startEditing = (p: Project) => {
    setEditingId(p.id);
    setEditValue(p.title);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditValue('');
  };

  const saveTitle = async (id: number) => {
    try {
      await handleUpdateTitle(id, editValue);
      setEditingId(null);
    } catch (err) {
      console.error("Failed to update title:", err);
    }
  };

  const filteredProjects = projects.filter(p => {
    const searchLower = searchQuery.toLowerCase();
    const mission = p.mission_statement || "";
    const skills = p.required_skills || [];
    const skillMatch = skills.some(s => s.toLowerCase().includes(searchLower));
    return (
      p.title.toLowerCase().includes(searchLower) ||
      mission.toLowerCase().includes(searchLower) ||
      skillMatch
    );
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-[clamp(30px,4vw,48px)] leading-[0.95] mb-1">Projects</h2>
          <p className="text-[#5f574e] mb-5">Active initiatives and requirements</p>
        </div>
        {projects.length > 0 && (
          <ZenButton 
            variant="ghost" 
            onClick={handleNukeProjects}
            className="flex items-center gap-2 text-clay hover:bg-clay/5 border-clay/20"
          >
            <XCircle size={16} /> Nuke All
          </ZenButton>
        )}
      </div>

      <div className="flex gap-3 mb-6">
        <div className="grow relative">
          <Briefcase className="absolute left-4 top-1/2 -translate-y-1/2 text-moss opacity-60" size={20} />
          <input 
            type="text" 
            placeholder="Search projects..." 
            className="w-full pl-11 h-[50px] text-base bg-white/60 border border-line rounded-[10px] transition-all duration-300 focus:bg-white focus:border-clay focus:shadow-[0_0_0_4px_rgba(155,123,86,0.1)] outline-none"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="flex flex-col gap-6">
        {filteredProjects.map((p, idx) => (
          <div 
            key={p.id} 
            id={`project-${p.id}`}
            className="group relative p-8 border border-line rounded-[24px] bg-white/45 flex flex-col gap-6 transition-all duration-700 ease-out translate-y-0 opacity-100 shadow-[0_20px_50px_rgba(120,100,70,0.06)]"
            style={{ transitionDelay: `${idx * 60}ms` }}
          >
            <button 
              onClick={() => handleDeleteProject(p.id)}
              className="absolute top-6 right-6 p-3 bg-clay/5 text-clay opacity-0 group-hover:opacity-100 transition-opacity rounded-xl hover:bg-clay/10"
              title="Delete Project"
            >
              <Trash2 size={16} />
            </button>

            <div className="flex justify-between items-start">
              <div className="grow pr-8">
                {editingId === p.id ? (
                  <div className="flex items-center gap-3 mb-3">
                    <input 
                      type="text" 
                      className="font-display text-[32px] leading-[0.95] bg-white border-b-2 border-clay outline-none w-full"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      autoFocus
                    />
                    <button onClick={() => saveTitle(p.id)} className="p-2 text-moss hover:bg-moss/10 rounded-lg"><Check size={20}/></button>
                    <button onClick={cancelEditing} className="p-2 text-clay hover:bg-clay/10 rounded-lg"><X size={20}/></button>
                  </div>
                ) : (
                  <div className="flex items-center gap-4 group/title mb-3">
                    <h3 className="font-display text-[42px] leading-[0.95] mt-0">{p.title}</h3>
                    <button 
                      onClick={() => startEditing(p)}
                      className="opacity-0 group-hover/title:opacity-100 p-2 text-moss/40 hover:text-moss transition-opacity"
                    >
                      <Edit2 size={18} />
                    </button>
                  </div>
                )}
                <p className="text-[#6d645a] text-[15px] leading-relaxed max-w-[800px]">
                  {p.mission_statement}
                </p>
              </div>
            </div>
            
            <div className="mt-2 flex flex-col gap-4">
              <div className="flex flex-wrap gap-2.5">
                {p.required_skills && p.required_skills.map(tech => (
                  <span key={tech} className="inline-flex items-center px-4 py-2 border border-line/40 rounded-full bg-white/60 text-[13px] font-medium shadow-sm">{tech}</span>
                ))}
              </div>

              {p.compatibility_insights && Object.keys(p.compatibility_insights).length > 0 && (
                <div className="p-4 rounded-xl bg-clay/5 border border-clay/10">
                  <h4 className="text-[11px] uppercase tracking-wider text-clay/60 font-bold mb-3">Compatibility Suggestions</h4>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(p.compatibility_insights).map(([target, pool]) => (
                      <div key={target} className="flex items-center gap-2">
                        <span className="text-[13px] font-medium text-moss">{target}</span>
                        <span className="text-line">→</span>
                        <span className="text-[13px] italic text-[#6d645a]">{pool}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
