import React, { useState } from 'react';
import { Maximize2, Minimize2, Map as MapIcon, Info, Users, Box, Network } from 'lucide-react';
import { Member, Project, Allocation } from '../../types';

interface TopologyMapProps {
    members: Member[];
    projects: Project[];
    assignments: Allocation[];
    onSelectNode?: (type: 'member' | 'project', id: number) => void;
}

export const TopologyMap: React.FC<TopologyMapProps> = ({ members, projects, assignments, onSelectNode }) => {
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [mapError, setMapError] = useState(false);

    if (members.length === 0 && projects.length === 0) return null;

    return (
        <div className={`
      relative flex flex-col gap-6 transition-all duration-500
      ${isFullscreen ? 'fixed inset-0 p-10 bg-paper z-[150]' : 'w-full'}
    `}>
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <MapIcon size={24} className="text-ink" />
                    <div>
                        <h2 className="font-display text-[32px] tracking-tight">Technical Topology</h2>
                        <p className="text-[12px] text-ink/40 uppercase tracking-widest font-bold">Semantic Clustering View (pgvector)</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => window.location.reload()}
                        className="p-3 bg-white border border-line rounded-xl hover:bg-paper transition-all shadow-sm flex items-center gap-2 text-[12px] font-bold uppercase tracking-widest"
                        title="Refresh Map"
                    >
                        <Box size={16} />
                    </button>
                    <button
                        onClick={() => setIsFullscreen(!isFullscreen)}
                        className="p-3 bg-white border border-line rounded-xl hover:bg-paper transition-all shadow-sm flex items-center gap-2 text-[12px] font-bold uppercase tracking-widest"
                    >
                        {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                        {isFullscreen ? 'Exit Fullscreen' : 'Expand View'}
                    </button>
                </div>
            </div>

            <div className="relative grow h-[600px] border-2 border-line/40 rounded-[40px] bg-white overflow-hidden shadow-inner group">
                {assignments.length === 0 ? (
                    <div className="w-full h-full flex flex-col items-center justify-center bg-[#fdfaf7] text-center p-12">
                        <div className="w-20 h-20 bg-moss/5 rounded-full flex items-center justify-center mb-6">
                            <Network size={40} className="text-moss opacity-20" />
                        </div>
                        <h3 className="font-display text-2xl mb-2">Topology Map Pending</h3>
                        <p className="text-ink/50 max-w-md mx-auto text-sm leading-relaxed">
                            The semantic relationship graph will be generated once you initiate the **Global Alignment** process.
                            This map clusters members around project intent using high-dimensional vector space.
                        </p>
                    </div>
                ) : (
                    <iframe
                        src="/match_map.html"
                        className="w-full h-full border-none"
                        title="Technical Topology Map"
                        onError={() => setMapError(true)}
                    />
                )}

                {assignments.length > 0 && (
                    <>

                        <div className="absolute bottom-6 right-6 p-4 bg-paper/90 backdrop-blur border border-line rounded-2xl shadow-xl flex flex-col gap-3 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                            <div className="flex items-center gap-2">
                                <Box size={14} className="text-[#4A5D4E]" />
                                <span className="text-[10px] font-bold uppercase tracking-wider text-ink/60">Project (Intent)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Users size={14} className="text-[#1A1A1A]" />
                                <span className="text-[10px] font-bold uppercase tracking-wider text-ink/60">Member (Profile)</span>
                            </div>
                            <div className="h-px bg-line/50 my-1" />
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-0.5 bg-[#c7b9a4]" />
                                <span className="text-[10px] font-bold uppercase tracking-wider text-ink/40">Semantic Fit Link</span>
                            </div>
                        </div>


                        <div className="absolute top-6 left-6 flex items-center gap-2 px-3 py-2 bg-ink text-paper rounded-full text-[9px] font-black uppercase tracking-[0.2em] shadow-2xl opacity-50">
                            <Info size={12} />
                            Interactive Graph: Scroll to zoom, Drag to explore
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
