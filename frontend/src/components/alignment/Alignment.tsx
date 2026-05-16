import React, { useState, useEffect } from 'react';
import { Play, Lock, UserMinus, Info, Zap, MessageSquareQuote, Loader2, Download, GripVertical } from 'lucide-react';
import { ZenCard } from '../ui/ZenCard';
import { ZenButton } from '../ui/ZenButton';
import { DndContext, useDraggable, useDroppable, DragEndEvent, DragOverlay, defaultDropAnimationSideEffects } from '@dnd-kit/core';
import { ZenSelect } from '../ui/ZenSelect';
import { Member, Project, Assignment, WhatIfResponse } from '../../types';
import { api } from '../../api/client';
import { useData } from '../../hooks/useData';

interface AlignmentProps {
  members: Member[];
  projects: Project[];
  assignments: Assignment[];
  loading: boolean;
  handleMatch: () => void;
  toggleLock: (memberId: number, projectId: number, isLocked: boolean) => void;
  handleManualAssign: (memberId: number, projectId: string) => void;
  selectedMemberId: number | null;
  setSelectedMemberId: (id: number | null) => void;
}

import ReactMarkdown from 'react-markdown';

// Draggable Member Component
const DraggableMember: React.FC<{
  member: Member;
  assignment?: Assignment;
  isSelected: boolean;
  isLocked: boolean;
  isPending: boolean;
  isTarget: boolean;
  onSelect: () => void;
  onExplain: () => void;
  onManualAssign: (val: string) => void;
  onUnlock: () => void;
  explainingId: number | null;
  projectOptions: any[];
}> = ({
  member, assignment, isSelected, isLocked, isPending, isTarget,
  onSelect, onExplain, onManualAssign, onUnlock, explainingId, projectOptions
}) => {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
      id: `member-${member.id}`,
      data: { memberId: member.id }
    });

    const style = transform ? {
      transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    } : undefined;

    const explanation = isPending ? null : assignment?.reasons?.find(r => !r.startsWith("ONBOARDING_BRIEF:"));
    const onboardingBrief = assignment?.reasons?.find(r => r.startsWith("ONBOARDING_BRIEF:"))?.replace("ONBOARDING_BRIEF: ", "");

    return (
      <div ref={setNodeRef} style={style} className={`flex flex-col gap-3 ${isDragging ? 'opacity-50 z-50' : ''}`}>
        <div
          className={`
          group px-8 py-5 rounded-[22px] border transition-all duration-200 flex items-center gap-6
          ${isSelected ? 'bg-ink border-ink text-paper shadow-xl' : 'border-line/40 bg-white/50 hover:bg-white'}
          ${isLocked && !isSelected ? 'border-clay/40 ring-1 ring-clay/20' : ''}
          ${isDragging ? 'shadow-2xl scale-105' : ''}
        `}
        >
          <div className="flex items-center gap-4 grow">
            <div {...listeners} {...attributes} className="cursor-grab active:cursor-grabbing p-1 -ml-4 opacity-30 hover:opacity-100 transition-opacity">
              <GripVertical size={20} />
            </div>
            <div
              className="flex items-center gap-4 grow cursor-pointer"
              onClick={onSelect}
            >
              <h4 className="font-display text-[26px] uppercase tracking-tight m-0 flex items-center gap-3">
                {isLocked && <Lock size={18} className={isSelected ? 'text-paper/60' : 'text-clay'} />}
                {member.name}
              </h4>
              <span className={`inline-flex items-center px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border ${isSelected ? 'bg-paper/10 border-paper/30 text-paper' : 'bg-line/20 border-line/40 text-moss'}`}>
                {member.is_senior ? 'Senior' : 'Junior'}
              </span>
              {isPending && !isSelected && !isTarget && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onExplain();
                  }}
                  disabled={explainingId === member.id}
                  className="ml-4 flex items-center gap-2 px-3 py-1.5 bg-clay text-paper text-[10px] font-black uppercase tracking-widest rounded-full hover:bg-clay-dark transition-colors shadow-lg active:scale-95 disabled:opacity-50"
                >
                  {explainingId === member.id ? <Loader2 size={12} className="animate-spin" /> : <MessageSquareQuote size={12} />}
                  Explain Move
                </button>
              )}
              {!isSelected && !isTarget && !isPending && (
                <span className="hidden xl:block absolute right-8 top-1/2 -translate-y-1/2 text-[9px] font-black text-clay opacity-0 group-hover:opacity-20 transition-opacity tracking-[0.3em] pointer-events-none">
                  DRAG TO REASSIGN
                </span>
              )}
            </div>
          </div>

          <div className={`relative flex items-center gap-8 pl-8 border-l border-line/20 ${isSelected ? 'text-paper' : 'text-ink'}`}>
            <div className="flex flex-col items-center">
              <span className="text-[10px] uppercase tracking-widest opacity-50 mb-1 font-bold">Fit Score</span>
              <span className="font-display text-[24px] leading-none">{assignment?.fit_score || 0}</span>
            </div>

            <div className="h-[40px] w-px bg-line/30 mx-2" />

            <div className="w-[180px]">
              <ZenSelect
                value={member.pinned_project_id || ""}
                onChange={onManualAssign}
                options={projectOptions}
                className={`h-[44px] text-[13px] ${isSelected ? 'bg-paper/10 border-paper/30 text-paper' : ''}`}
              />
            </div>

            {isLocked && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onUnlock();
                }}
                className={`p-3 rounded-xl border transition-all duration-300 ${isSelected ? 'bg-paper/10 border-paper/30 hover:bg-paper/20' : 'border-line/40 bg-white hover:bg-paper shadow-sm'}`}
                title="Unpin member"
              >
                <UserMinus size={18} />
              </button>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2 ml-4">
          {explanation && !isSelected && !isTarget && (
            <div className="px-8 py-3 bg-moss/[0.03] border border-moss/10 rounded-[18px] flex gap-3 items-start animate-in fade-in slide-in-from-left-4">
              <Info size={14} className="text-moss mt-0.5 shrink-0 opacity-60" />
              <p className="text-[12px] text-[#5f574e] italic leading-relaxed">{explanation}</p>
            </div>
          )}

          {onboardingBrief && !isSelected && !isTarget && (
            <div className="px-8 py-4 bg-clay/[0.03] border border-clay/10 rounded-[22px] flex flex-col gap-1 animate-in fade-in slide-in-from-left-6">
              <div className="flex items-center gap-2 mb-2">
                <Zap size={12} className="text-clay fill-clay" />
                <span className="text-[9px] font-black uppercase tracking-[0.2em] text-clay">AI Jumpstart Brief</span>
              </div>
              <div className="text-[12px] text-ink/80 leading-relaxed font-medium prose prose-sm max-w-none prose-p:m-0 prose-strong:text-ink prose-ul:my-1 prose-li:m-0">
                <ReactMarkdown>{onboardingBrief}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };


const DroppableProject: React.FC<{
  project: Project;
  team: Assignment[];
  members: Member[];
  isSelectedMemberTarget: boolean;
  projectOptions: any[];
  whatIf?: WhatIfResponse;
  selectedMemberId: number | null;
  onSelectMember: (id: number | null) => void;
  onExplainManual: (id: number) => void;
  onManualAssign: (mid: number, pid: string) => void;
  onToggleLock: (mid: number, pid: number, locked: boolean) => void;
  onProjectClick: (pid: string) => void;
  explainingId: number | null;
}> = ({
  project: p, team, members, isSelectedMemberTarget, projectOptions, whatIf,
  selectedMemberId, onSelectMember, onExplainManual, onManualAssign, onToggleLock, onProjectClick, explainingId
}) => {
    const { setNodeRef, isOver } = useDroppable({
      id: `project-${p.id}`,
      data: { projectId: p.id }
    });

    return (
      <div
        ref={setNodeRef}
        id={`project-${p.id}`}
        className={`
        relative p-8 border-2 rounded-[32px] transition-all duration-300 flex flex-col gap-8
        ${isSelectedMemberTarget || isOver
            ? 'border-clay bg-clay/[0.04] shadow-[0_30px_70px_rgba(155,123,86,0.15)]'
            : 'border-line/40 bg-white/45 shadow-[0_20px_50px_rgba(120,100,70,0.06)]'
          }
        ${isOver ? 'ring-2 ring-clay scale-[1.01]' : ''}
      `}
      >
        <div className="flex justify-between items-start gap-8">
          <div className="flex flex-col gap-4 grow">
            <h3 className="font-display text-[clamp(32px,5vw,42px)] leading-[1.1] m-0 max-w-[800px]">{p.title}</h3>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`shrink-0 px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest ${p.complexity === 'Hard' ? 'bg-ink text-paper' : 'bg-line text-moss'}`}>
                {p.complexity}
              </span>
              <div className="shrink-0 inline-flex items-center gap-2 px-4 py-1.5 border border-line rounded-full bg-white/60 text-[11px] font-bold uppercase tracking-widest">Team: {team.length}</div>
            </div>
          </div>
          {isSelectedMemberTarget && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onProjectClick(p.id.toString());
              }}
              className="shrink-0 flex items-center gap-2 text-paper font-bold text-[12px] tracking-widest bg-clay hover:bg-clay-dark px-8 py-4 rounded-full border-2 border-clay shadow-2xl transition-all active:scale-95"
            >
              <Play size={14} className="rotate-90 fill-current" /> ADD MEMBER HERE
            </button>
          )}
        </div>

        <div className="flex flex-col gap-2">
          {team.map(a => {
            const member = members.find(m => m.id === a.candidate_id);
            if (!member) return null;
            const isLocked = member.pinned_project_id === p.id;
            const isSelected = selectedMemberId === member.id;
            const isPending = a.reasons?.[0] === "PENDING_MANUAL_EXPLANATION";

            return (
              <DraggableMember
                key={member.id}
                member={member}
                assignment={a}
                isSelected={isSelected}
                isLocked={isLocked}
                isPending={isPending}
                isTarget={isSelectedMemberTarget}
                onSelect={() => onSelectMember(isSelected ? null : member.id)}
                onExplain={() => onExplainManual(member.id)}
                onManualAssign={(val) => onManualAssign(member.id, val)}
                onUnlock={() => onToggleLock(member.id, p.id, true)}
                explainingId={explainingId}
                projectOptions={projectOptions}
              />
            );
          })}


          {selectedMemberId && !team.some(a => a.candidate_id === selectedMemberId) && whatIf && (
            <div className="mt-4 px-8 py-6 bg-clay/[0.05] border-2 border-dashed border-clay/30 rounded-[28px] animate-in slide-in-from-top-2">
              <div className="flex items-center gap-3 mb-2">
                <Zap size={16} className="text-clay fill-clay" />
                <h5 className="text-[11px] font-black uppercase tracking-[0.2em] text-clay">Semantic Impact Preview</h5>
              </div>
              <p className="text-[14px] text-ink/80 font-medium mb-3">"{whatIf.reasoning || whatIf.insight}"</p>
              <div className="flex gap-4">
                <div className="flex flex-col">
                  <span className="text-[9px] uppercase tracking-widest opacity-50 font-bold">New Fit Score</span>
                  <span className="text-[14px] font-bold text-ink">{whatIf.target_score_impact}</span>
                </div>
                {whatIf.source_score_impact !== 0 && (
                  <div className="flex flex-col">
                    <span className="text-[9px] uppercase tracking-widest opacity-50 font-bold">Origin Impact</span>
                    <span className="text-[14px] font-bold text-clay">{whatIf.source_score_impact}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {team.length === 0 && !isSelectedMemberTarget && (
            <div className="text-center py-20 border-2 border-dashed border-line/30 rounded-[32px] bg-white/10">
              <p className="text-[#6d645a] text-[16px] italic font-medium opacity-50">Empty project. Select or drag a member to assign them here.</p>
            </div>
          )}
        </div>
      </div>
    );
  };

export const Alignment: React.FC<AlignmentProps> = ({
  members, projects, assignments, loading, handleMatch, toggleLock, handleManualAssign,
  selectedMemberId, setSelectedMemberId
}) => {
  const [whatIfData, setWhatIfData] = useState<Record<number, WhatIfResponse>>({});
  const [explainingId, setExplainingId] = useState<number | null>(null);
  const { fetchData } = useData();

  const projectOptions = [
    { value: "", label: "Auto Align" },
    ...projects.map(p => ({ value: p.id, label: p.title }))
  ];

  const unassignedMembers = members.filter(m =>
    !assignments.some(a => a.candidate_id === m.id)
  );

  const handleProjectClick = (projectId: string) => {
    if (selectedMemberId) {
      handleManualAssign(selectedMemberId, projectId);
      setSelectedMemberId(null);
    }
  };

  const handleExplainManual = async (candidateId: number) => {
    setExplainingId(candidateId);
    try {
      await api.explainAssignment(candidateId);
      fetchData();
    } catch (err) {
      console.error("Manual explanation failed", err);
    } finally {
      setExplainingId(null);
    }
  };

  // Drag End Handler
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const memberId = active.data.current?.memberId;
    const projectId = over.data.current?.projectId;

    if (memberId && projectId) {
      handleManualAssign(memberId, projectId.toString());
    }
  };

  useEffect(() => {
    if (selectedMemberId) {
      const sourceAssignment = assignments.find(a => a.candidate_id === selectedMemberId);
      const targetProjectIds = projects
        .filter(p => p.id !== sourceAssignment?.project_id)
        .map(p => p.id);

      if (targetProjectIds.length > 0) {
        api.getBatchWhatIf({
          candidate_id: selectedMemberId,
          source_project_id: sourceAssignment?.project_id,
          target_project_ids: targetProjectIds
        }).then(res => {
          setWhatIfData(res.data.insights);
        }).catch(err => {
          console.error("Batch What-If failed", err);
        });
      }
    } else {
      setWhatIfData({});
    }
  }, [selectedMemberId, assignments, projects]);

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="flex flex-col gap-10">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-[clamp(30px,4vw,48px)] leading-[0.95] mb-1">Alignment Engine</h2>
            <p className="text-[#5f574e] mb-5">Optimized team allocations</p>
          </div>

          <div className="flex items-center gap-4">
            <ZenButton
              onClick={() => window.open(api.exportUrl, '_blank')}
              className="px-10 py-5 rounded-[24px] bg-white border border-line text-ink hover:bg-paper transition-all active:scale-95 shadow-xl flex items-center gap-4"
            >
              <Download size={18} />
              <span className="font-display text-[22px] tracking-tight">Export Report</span>
            </ZenButton>
          </div>
        </div>

        <div className={`p-8 border-2 border-dashed rounded-[32px] transition-all duration-300 ${selectedMemberId ? 'border-clay bg-clay/[0.02]' : 'border-line/40 bg-white/20'}`}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <h4 className="text-[11px] font-bold uppercase tracking-[0.2em] text-moss opacity-70">Member Bench</h4>
              {selectedMemberId && <span className="px-2 py-0.5 bg-clay text-paper text-[9px] font-bold rounded uppercase tracking-wider">Teleport Active</span>}
            </div>
            <span className="text-[11px] text-[#6d645a] opacity-50 italic">Drag or click a member to reassign them</span>
          </div>
          <div className="flex flex-wrap gap-3">
            {unassignedMembers.map(m => {
              const isSelected = selectedMemberId === m.id;
              return (
                <DraggableMember
                  key={m.id}
                  member={m}
                  isSelected={isSelected}
                  isLocked={false}
                  isPending={false}
                  isTarget={!!selectedMemberId}
                  onSelect={() => setSelectedMemberId(isSelected ? null : m.id)}
                  onExplain={() => { }}
                  onManualAssign={(val) => handleManualAssign(m.id, val)}
                  onUnlock={() => { }}
                  explainingId={null}
                  projectOptions={projectOptions}
                />
              );
            })}
            {unassignedMembers.length === 0 && (
              <p className="text-[#6d645a] text-[14px] italic opacity-50 py-2">All members are currently assigned.</p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-12">
          {projects.map((p, idx) => (
            <DroppableProject
              key={p.id}
              project={p}
              team={assignments.filter(a => a.project_id === p.id)}
              members={members}
              isSelectedMemberTarget={!!selectedMemberId}
              projectOptions={projectOptions}
              whatIf={whatIfData[p.id]}
              selectedMemberId={selectedMemberId}
              onSelectMember={setSelectedMemberId}
              onExplainManual={handleExplainManual}
              onManualAssign={handleManualAssign}
              onToggleLock={toggleLock}
              onProjectClick={handleProjectClick}
              explainingId={explainingId}
            />
          ))}
        </div>
      </div>
    </DndContext>
  );
};
