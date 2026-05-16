import axios from 'axios';

const API_BASE = "http://127.0.0.1:8000/api/";

const client = axios.create({
  baseURL: API_BASE,
});

export const api = {
  getMembers: () => client.get('members'),
  getProjects: () => client.get('projects'),
  getAssignments: () => client.get('assignments'),
  getStatus: () => client.get('status'),
  ingest: () => client.post('ingest'),
  getIngestionErrors: () => client.get('ingest/errors'),
  retryAllIngestions: () => client.post('ingest/retry/all'),
  retryIngestion: (id: number) => client.post(`ingest/retry/${id}`),
  match: () => client.post('match'),
  exportUrl: `${API_BASE}export`,
  updateMember: (id: number, data: any) => client.put(`members/${id}`, data),
  deleteMember: (id: number) => client.delete(`members/${id}`),
  updateProject: (id: number, data: any) => client.put(`projects/${id}`, data),
  updateProjectTitle: (id: number, title: string) => client.patch(`projects/${id}`, { title }),
  deleteProject: (id: number) => client.delete(`projects/${id}`),
  deleteAllProjects: () => client.delete('projects'),
  updateResume: (id: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post(`ingest/update-resume/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getWhatIf: (data: { candidate_id: number, source_project_id?: number, target_project_id: number }) => client.post('what-if', data),
  getBatchWhatIf: (data: { candidate_id: number, source_project_id?: number, target_project_ids: number[] }) => client.post('what-if/batch', data),
  explainAssignment: (candidateId: number) => client.post(`assignments/${candidateId}/explain`),
};
