import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { Member, Project, Allocation, IngestionError, TraceLog, Bottleneck } from '../types';

interface DataContextType {
  members: Member[];
  projects: Project[];
  assignments: Allocation[];
  ingestionErrors: IngestionError[];
  traceLogs: TraceLog[];
  bottlenecks: Bottleneck[];
  loading: boolean;
  ingesting: boolean;
  isLLMReady: boolean;
  progress: number;
  currentTask: string;
  fetchData: () => Promise<void>;
  fetchErrors: () => Promise<void>;
  handleIngest: () => Promise<void>;
  handleMatch: () => Promise<boolean>;
  handleRetryAll: () => Promise<void>;
  handleRetrySpecific: (id: number) => Promise<void>;
  handleUpdateName: (id: number, name: string) => Promise<void>;
  handleDeleteMember: (id: number) => Promise<void>;
  handleDeleteProject: (id: number) => Promise<void>;
  handleNukeProjects: () => Promise<void>;
  handleUpdateProjectTitle: (id: number, title: string) => Promise<void>;
  handleUpdateResume: (id: number, file: File) => Promise<void>;
  toggleSeniority: (id: number, currentStatus: boolean) => Promise<void>;
  toggleLock: (memberId: number, projectId: number, isLocked: boolean) => Promise<void>;
  handleManualAssign: (memberId: number, projectId: string) => Promise<void>;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [members, setMembers] = useState<Member[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [assignments, setAssignments] = useState<Allocation[]>([]);
  const [ingestionErrors, setIngestionErrors] = useState<IngestionError[]>([]);
  const [traceLogs, setTraceLogs] = useState<TraceLog[]>([]);
  const [bottlenecks, setBottlenecks] = useState<Bottleneck[]>([]);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [isLLMReady, setIsLLMReady] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTask, setCurrentTask] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [mRes, pRes, aRes] = await Promise.all([
        api.getMembers(),
        api.getProjects(),
        api.getAssignments()
      ]);
      setMembers(mRes.data);
      setProjects(pRes.data);
      setAssignments(aRes.data);

      const derivedBottlenecks = pRes.data.map((p: Project) => {
        const teamSize = aRes.data.filter((a: Allocation) => a.project_id === p.id).length;
        const required = p.required_skills || [];

        const teamSkills = aRes.data.filter((a: Allocation) => a.project_id === p.id)
          .flatMap((a: Allocation) => {
            const m = mRes.data.find((member: Member) => member.id === a.candidate_id);
            return m ? (m.skills || []).map(s => s.toLowerCase()) : [];
          });

        const gaps = required.filter(req => {
          const reqLow = req.toLowerCase();
          return !teamSkills.some(teamSkill =>
            teamSkill.includes(reqLow) || reqLow.includes(teamSkill)
          );
        });

        return {
          project_id: p.id,
          project_title: p.title,
          health_score: Math.round(((required.length - gaps.length) / (required.length || 1)) * 100),
          critical_skills: gaps,
          explanation: gaps.length > 0 ? `Missing ${gaps.length} critical skills.` : "Team is technically balanced.",
          is_at_risk: gaps.length > 0 || teamSize === 0
        };
      });
      setBottlenecks(derivedBottlenecks);

    } catch (err) {
      console.error("Fetch Data failed", err);
    }
  }, []);

  const fetchErrors = useCallback(async () => {
    try {
      const res = await api.getIngestionErrors();
      setIngestionErrors(res.data);
    } catch (err) {
      console.error("Fetch Errors failed", err);
    }
  }, []);

  useEffect(() => {
    const wsUrl = "ws://127.0.0.1:8000/api/ws/status";
    let socket: WebSocket | null = null;
    let reconnectTimer: any = null;

    const connect = () => {
      socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "refresh_data") { fetchData(); fetchErrors(); return; }
        if (data.type === "trace_log") { setTraceLogs(prev => [data.log, ...prev].slice(0, 50)); return; }

        const isIngesting = data.is_ingesting === "True" || data.is_ingesting === true;
        const isMatching = data.is_matching === "True" || data.is_matching === true;
        const isLLMReady = data.is_llm_ready === "True" || data.is_llm_ready === true;
        const currentProgress = data.progress !== undefined ? parseFloat(data.progress) : 0;

        setIngesting(isIngesting);
        setLoading(isMatching);
        setIsLLMReady(isLLMReady);
        if (data.progress !== undefined) {
          const newProgress = currentProgress;
          setProgress(newProgress);
          if (newProgress > 0) {
            fetchData();
            fetchErrors();
          }
        }
        if (data.current_task !== undefined) setCurrentTask(data.current_task);

        if (currentProgress === 1 || (isIngesting === false && isMatching === false)) {
          fetchData();
          fetchErrors();
        }
      };
      socket.onclose = () => { reconnectTimer = setTimeout(connect, 3000); };
    };
    connect();
    fetchData();
    fetchErrors();
    return () => {
      if (socket) socket.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [fetchData, fetchErrors]);

  const handleIngest = async () => {
    setIngesting(true); setProgress(0); setCurrentTask("Initializing...");
    try { await api.ingest(); } catch (err) { setIngesting(false); }
  };

  const handleRetryAll = async () => {
    setIngesting(true); setProgress(0); setCurrentTask("Retrying failures...");
    try { await api.retryAllIngestions(); } catch (err) { setIngesting(false); }
  };

  const handleRetrySpecific = async (id: number) => {
    setIngesting(true); setProgress(0); setCurrentTask("Retrying specific file...");
    try { await api.retryIngestion(id); } catch (err) { setIngesting(false); }
  };

  const handleUpdateName = async (id: number, name: string) => {
    try { await api.updateMember(id, { name }); fetchData(); } catch (e) { console.error(e); }
  };

  const handleDeleteMember = async (id: number) => {
    if (!window.confirm("Delete this member?")) return;
    try { await api.deleteMember(id); fetchData(); } catch (e) { console.error(e); }
  };

  const handleDeleteProject = async (id: number) => {
    if (!window.confirm("Delete this project?")) return;
    try { await api.deleteProject(id); fetchData(); } catch (e) { console.error(e); }
  };

  const handleNukeProjects = async () => {
    if (!window.confirm("🚨 NUKE ALL PROJECTS?")) return;
    try { await api.deleteAllProjects(); fetchData(); } catch (e) { console.error(e); }
  };

  const handleUpdateProjectTitle = async (id: number, title: string) => {
    try { await api.updateProjectTitle(id, title); fetchData(); } catch (e) { console.error(e); }
  };

  const handleUpdateResume = async (id: number, file: File) => {
    setIngesting(true); setCurrentTask(`Updating resume...`);
    try { await api.updateResume(id, file); } catch (e) { setIngesting(false); }
  };

  const handleMatch = async () => {
    setLoading(true); setProgress(0); setCurrentTask("Initializing...");
    try { await api.match(); return true; } catch (err) { setLoading(false); return false; }
  };

  const toggleSeniority = async (id: number, currentStatus: boolean) => {
    await api.updateMember(id, { is_senior: !currentStatus }); fetchData();
  };

  const toggleLock = async (memberId: number, projectId: number, isLocked: boolean) => {
    const newProjectId = isLocked ? null : projectId;
    try { await api.updateMember(memberId, { pinned_project_id: newProjectId }); await fetchData(); } catch (err) { fetchData(); }
  };

  const handleManualAssign = async (memberId: number, projectId: string) => {
    const newProjectIdNum = projectId === "" ? null : parseInt(projectId);
    try { await api.updateMember(memberId, { pinned_project_id: newProjectIdNum }); await fetchData(); } catch (err) { fetchData(); }
  };

  const value = {
    members, projects, assignments, ingestionErrors, traceLogs, bottlenecks,
    loading, ingesting, isLLMReady, progress, currentTask,
    fetchData, fetchErrors, handleIngest, handleMatch, handleRetryAll, handleRetrySpecific,
    handleUpdateName, handleDeleteMember, handleDeleteProject, handleNukeProjects,
    handleUpdateProjectTitle, handleUpdateResume,
    toggleSeniority, toggleLock, handleManualAssign
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

export const useData = () => {
  const context = useContext(DataContext);
  if (context === undefined) throw new Error('useData must be used within a DataProvider');
  return context;
};
