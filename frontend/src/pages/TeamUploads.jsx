import { useEffect, useState } from 'react'
import { getMyTeam, getMyTeamSubmissions } from '../api/teams'
import { listDeliverables, createSubmission, addFile, getSubmissionFiles, downloadFile, deleteFile } from '../api/deliverables'
import { getRankings } from '../api/competitions'
import { getFileIcon, formatFileSize } from '../utils'

export default function TeamUploads() {
  const [team, setTeam] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [submissions, setSubmissions] = useState([])
  const [files, setFiles] = useState({})
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState({})
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('uploads')
  const [rankings, setRankings] = useState([])

  const loadRankings = async (compId) => {
    try {
      const data = await getRankings(compId)
      setRankings(data)
    } catch {
      setRankings([])
    }
  }

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const myTeam = await getMyTeam()
      setTeam(myTeam)
      const dels = await listDeliverables(myTeam.competition_id)
      setDeliverables(dels)
      const subs = await getMyTeamSubmissions(myTeam.competition_id)
      setSubmissions(subs)
      const filesMap = {}
      for (const sub of subs) {
        try {
          filesMap[sub.id] = await getSubmissionFiles(sub.id)
        } catch {
          filesMap[sub.id] = []
        }
      }
      setFiles(filesMap)
      await loadRankings(myTeam.competition_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load upload page')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const getSubmissionForDeliverable = (delivId) => {
    return submissions.find(s => s.deliverable_id === delivId)
  }

  const handleUpload = async (delivId, file) => {
    setError('')
    setUploading(prev => ({ ...prev, [delivId]: 'uploading' }))
    try {
      let submission = getSubmissionForDeliverable(delivId)
      if (!submission) {
        submission = await createSubmission(delivId, team.id)
        setSubmissions(prev => [...prev, submission])
      }
      const result = await addFile(submission.id, file)
      setFiles(prev => ({
        ...prev,
        [submission.id]: [{
          id: result.id,
          original_filename: result.original_filename || file.name,
          file_type: result.file_type || file.type || '',
          file_size: result.file_size,
          version: result.version || 1,
          uploaded_at: result.uploaded_at,
          submitted_at: result.submitted_at || new Date().toISOString(),
        }]
      }))
      alert('File uploaded successfully!')
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(prev => ({ ...prev, [delivId]: false }))
    }
  }

  const loadFilesForSubmission = async (submission) => {
    if (!submission) return
    try {
      const submissionFiles = await getSubmissionFiles(submission.id)
      setFiles(prev => ({ ...prev, [submission.id]: submissionFiles }))
    } catch (err) {
      console.error('Failed to load files:', err)
    }
  }

  if (loading) return <div className="p-6">Loading...</div>
  if (error) return <div className="p-6 text-red-600">{error}</div>
  if (!team) return <div className="p-6">You are not assigned to any team.</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Team Uploads</h1>
      <p className="text-gray-500 mb-4">Team: {team.name} | Competition ID: {team.competition_id}</p>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('uploads')}
          className={`px-4 py-2 rounded text-sm ${activeTab === 'uploads' ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
        >
          Uploads
        </button>
        <button
          onClick={() => setActiveTab('rankings')}
          className={`px-4 py-2 rounded text-sm ${activeTab === 'rankings' ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
        >
          Rankings
        </button>
      </div>

      {activeTab === 'rankings' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-center">Rank</th>
                <th className="p-3">Team</th>
              </tr>
            </thead>
            <tbody>
              {rankings.length === 0 ? (
                <tr><td colSpan="2" className="p-4 text-center text-gray-500">No rankings available yet.</td></tr>
              ) : rankings.map(r => (
                <tr key={r.team_id} className={`border-t ${r.team_id === team.id ? 'bg-indigo-50' : ''}`}>
                  <td className="p-3 text-center font-bold">{r.rank}</td>
                  <td className="p-3">
                    {r.team_name}
                    {r.team_id === team.id && <span className="ml-2 text-xs text-indigo-600 font-semibold">(Your Team)</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'uploads' && (
      <div className="space-y-6">
        {deliverables.map(d => {
          const sub = getSubmissionForDeliverable(d.id)
          const submissionFiles = files[sub?.id] || []
          return (
            <div key={d.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-lg">{d.name}</h3>
                  <span className="inline-block px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs mt-1">
                    {d.category}
                  </span>
                  {d.description && <p className="text-sm text-gray-500 mt-1">{d.description}</p>}
                  {d.deadline && <p className="text-xs text-red-500 mt-1">Deadline: {new Date(d.deadline).toLocaleString()}</p>}
                </div>
                {sub && <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Submitted</span>}
              </div>

              {submissionFiles.length > 0 && (
                <div className="mb-4 space-y-2">
                  {submissionFiles.map(f => (
                    <div key={f.id} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                      <span className="text-2xl">{getFileIcon(f.original_filename)}</span>
                      <div className="flex-1">
                        <span className="font-medium text-sm">{f.original_filename}</span>
                        <span className="text-xs text-gray-500 ml-2">
                          {formatFileSize(f.file_size)}
                        </span>
                      </div>
                        <button
                          onClick={() => downloadFile(sub.id, f.id, f.original_filename).catch(err => setError(err.message || 'Download failed'))}
                          className="text-indigo-600 hover:text-indigo-800 text-xs px-2 py-1 border border-indigo-200 rounded"
                        >Download</button>
                        <button
                          onClick={async () => {
                            if (!window.confirm('Delete this file?')) return
                            try {
                              await deleteFile(sub.id, f.id)
                              const updated = await getSubmissionFiles(sub.id)
                              setFiles(prev => ({ ...prev, [sub.id]: updated }))
                            } catch (err) {
                              setError(err.response?.data?.detail || 'Delete failed')
                            }
                          }}
                          className="text-red-600 hover:text-red-800 text-xs px-2 py-1 border border-red-200 rounded"
                        >Delete</button>
                      <div className="flex flex-col items-end text-xs text-gray-400">
                        <span>v{f.version || 1}</span>
                        {f.submitted_at && <span>Submitted: {new Date(f.submitted_at).toLocaleString()}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <label className="flex items-center gap-3 text-sm cursor-pointer">
                <input
                  type="file"
                  accept=".docx,.pdf,.pptx,.zip,.mp4,.png,.jpg,.jpeg"
                  onChange={(e) => {
                    const file = e.target.files[0]
                    if (file) handleUpload(d.id, file)
                    e.target.value = ''
                  }}
                  disabled={uploading[d.id]}
                  className="hidden"
                />
                <span className={submissionFiles.length > 0 ? 'text-indigo-600 font-semibold' : 'text-gray-500'}>
                  {uploading[d.id] === 'uploading' ? 'Uploading...' : submissionFiles.length > 0 ? 'Replace File' : 'Choose File'}
                </span>
              </label>
              {uploading[d.id] === 'uploading' && <p className="text-xs text-gray-500 mt-2">Uploading...</p>}
            </div>
          )
        })}
        </div>
      )}
    </div>
  )
}
