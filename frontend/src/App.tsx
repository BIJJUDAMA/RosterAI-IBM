import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useData } from './hooks/useData';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { Dashboard } from './components/dashboard/Dashboard';
import { Members } from './components/members/Members';
import { Projects } from './components/projects/Projects';
import { Alignment } from './components/alignment/Alignment';

export default function App() {
  const {
    members,
    projects,
    assignments,
    ingestionErrors,
    bottlenecks,
    loading,
    ingesting,
    handleIngest,
    handleMatch,
    handleRetryAll,
    handleRetrySpecific,
    handleUpdateName,
    handleDeleteMember,
    handleDeleteProject,
    handleNukeProjects,
    handleUpdateProjectTitle,
    handleUpdateResume,
    toggleSeniority,
    toggleLock,
    handleManualAssign
  } = useData();

  const [showGraph, setShowGraph] = useState(false);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    setTimeout(() => setRevealed(true), 100);
  }, []);

  return (
    <div className="min-h-screen p-[5vh_6vw_8vh] bg-zen-gradient bg-paper relative overflow-hidden font-body text-ink">
      <div className="absolute inset-0 pointer-events-none opacity-8 opacity-[0.08] bg-[url('data:image/svg+xml,%3Csvg_viewBox=%220_0_200_200%22_xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter_id=%22n%22%3E%3CfeTurbulence_type=%22fractalNoise%22_baseFrequency=%220.95%22_numOctaves=%223%22/%3E%3C/filter%3E%3Crect_width=%22100%25%22_height=%22100%25%22_filter=%22url(%23n)%22/%3E%3C/svg%3E')]" />
      
      <div className="max-w-[1400px] mx-auto relative z-10">
        <Header 
          showGraph={showGraph}
          setShowGraph={setShowGraph}
        />

        <div className={`flex gap-[60px] mt-10 transition-all duration-700 ease-out ${revealed ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-[22px]'}`}>
          <Sidebar 
            members={members}
            projects={projects}
            assignments={assignments}
          />

          <main className="flex-1 overflow-y-auto pr-4 terminal-scroll custom-scrollbar">
            <Routes>
              <Route path="/" element={
                <Dashboard 
                  members={members}
                  projects={projects}
                  assignments={assignments}
                  ingestionErrors={ingestionErrors}
                  bottlenecks={bottlenecks}
                  showGraph={showGraph}
                  setShowGraph={setShowGraph}
                  handleRetryAll={handleRetryAll}
                  handleRetrySpecific={handleRetrySpecific}
                />
              } />
              <Route path="/members" element={
                <Members 
                  members={members}
                  projects={projects}
                  ingesting={ingesting}
                  handleIngest={handleIngest}
                  toggleSeniority={toggleSeniority}
                  handleManualAssign={handleManualAssign}
                  handleUpdateName={handleUpdateName}
                  handleDeleteMember={handleDeleteMember}
                  handleUpdateResume={handleUpdateResume}
                />
              } />
              <Route path="/projects" element={
                <Projects 
                  projects={projects}
                  handleDeleteProject={handleDeleteProject}
                  handleNukeProjects={handleNukeProjects}
                  handleUpdateTitle={handleUpdateProjectTitle}
                />
              } />
              <Route path="/alignment" element={
                <Alignment 
                  members={members}
                  projects={projects}
                  assignments={assignments}
                  onManualAssign={handleManualAssign}
                  onToggleLock={toggleLock}
                  showGraph={showGraph}
                />
              } />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </div>
  );
}
