import api from './client'

export const listDeliverables = (compId) => api.get('/deliverables', { params: { competition_id: compId } }).then(r => r.data)
export const createDeliverable = (data) => api.post('/deliverables', null, { params: data }).then(r => r.data)
export const listSubmissions = (delivId) => api.get(`/deliverables/${delivId}/submissions`).then(r => r.data)
export const createSubmission = (delivId, teamId) => api.post(`/deliverables/${delivId}/submissions`, null, { params: { team_id: teamId } }).then(r => r.data)
export const updateSubmissionStatus = (subId, status) => api.patch(`/deliverables/submissions/${subId}/status`, null, { params: { new_status: status } }).then(r => r.data)
export const addFile = (submissionId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/deliverables/submissions/${submissionId}/files`, formData).then(r => r.data)
}
export const getSubmissionFiles = (submissionId) => api.get(`/deliverables/submissions/${submissionId}/files`).then(r => r.data)
export const deleteFile = (submissionId, fileId) => api.delete(`/deliverables/submissions/${submissionId}/files/${fileId}`).then(r => r.data)
export const listSubmissionFiles = (delivId) => api.get(`/deliverables/${delivId}/submissions`).then(r => r.data)
export const downloadFile = async (submissionId, fileId, filename) => {
  const token = localStorage.getItem('token')
  const res = await fetch(`/api/v1/deliverables/submissions/${submissionId}/files/${fileId}/download`, {
    headers: { 'Authorization': `Bearer ${token}` },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || 'download'
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}
export const getCompetitionSubmissions = (compId) => api.get(`/deliverables/competitions/${compId}/submissions`).then(r => r.data)
