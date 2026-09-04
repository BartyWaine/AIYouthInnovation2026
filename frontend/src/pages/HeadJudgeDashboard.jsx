import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getAllScores,
  updateEvaluationStatus,
  correctScore as correctScoreApi,
  getEvaluationAudit,
  getCriteria,
  getAveragedScores,
} from '../api/judges'
import { listCompetitions } from '../api/competitions'

const STATUS_COLORS = {
  OPEN: 'bg-gray-100 text-gray-700',
  SUBMITTED: 'bg-blue-100 text-blue-700',
  LOCKED: 'bg-yellow-100 text-yellow-700',
  FINALIZED: 'bg-green-100 text-green-700',
}

function StatusBadge({ status }) {
  return (
    <span className={`text-xs px-2 py-1 rounded font-medium ${STATUS_COLORS[status] || 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}

export default function HeadJudgeDashboard() {
  const [allScores, setAllScores] = useState([])
  const [avgScores, setAvgScores] = useState([])
  const [criteria, setCriteria] = useState([])
  const [competitions, setCompetitions] = useState([])
  const [compId, setCompId] = useState('')
  const [activeEval, setActiveEval] = useState(null)
  const [auditLogs, setAuditLogs] = useState([])
  const [correctModal, setCorrectModal] = useState(null)
  const [correctScoreValue, setCorrectScoreValue] = useState('')
  const [correctReason, setCorrectReason] = useState('')
  const [reopenReason, setReopenReason] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionMsg, setActionMsg] = useState('')
  const [bulkStatus, setBulkStatus] = useState('')
  const [bulkReason, setBulkReason] = useState('')
  const [showBulkReason, setShowBulkReason] = useState(false)

  useEffect(() => {
    loadCriteria()
    listCompetitions().then(setCompetitions).catch(() => {})
  }, [])

  const loadCriteria = async () => {
    try {
      const data = await getCriteria()
      setCriteria(data)
    } catch { /* criteria optional */
    }
  }

  const loadAllScores = async (competitionId) => {
    if (!competitionId) return
    setLoading(true)
    setError('')
    try {
      const [data, avgData] = await Promise.all([
        getAllScores(competitionId),
        getAveragedScores(competitionId),
      ])
      setAllScores(data)
      setAvgScores(avgData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load scores')
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (evalId, newStatus, reason) => {
    if (newStatus === 'OPEN' && !reason?.trim()) {
      setError('Reason is required to reopen a finalized evaluation')
      return
    }
    setError('')
    try {
      const result = await updateEvaluationStatus(evalId, newStatus, reason || undefined)
      if (result.changed) {
        showMsg(`Evaluation ${newStatus.toLowerCase()}d successfully`)
        await loadAllScores(compId)
        if (activeEval?.evaluation_id === evalId) {
          setActiveEval(prev => ({ ...prev, status: newStatus }))
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to ${newStatus.toLowerCase()} evaluation`)
    }
  }

  const handleCorrection = async () => {
    if (!correctModal || !correctScoreValue || !correctReason.trim()) return
    setError('')
    try {
      const result = await correctScoreApi(
        correctModal.evaluation_id,
        correctModal.criterion_id,
        parseFloat(correctScoreValue),
        correctReason.trim()
      )
      showMsg(`Corrected: ${result.old_value} → ${result.new_value}`)
      setCorrectModal(null)
      setCorrectScoreValue('')
      setCorrectReason('')
      await loadAllScores(compId)
      if (activeEval) loadAudit(activeEval.evaluation_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to correct score')
    }
  }

  const handleBulkStatus = async (targetStatus) => {
    if (!targetStatus) return
    const evalIds = allScores.map(e => e.evaluation_id)
    if (evalIds.length === 0) return
    const reason = targetStatus === 'OPEN' ? (bulkReason.trim() || 'Bulk reopen by head judge') : undefined
    let success = 0, failed = 0
    for (const id of evalIds) {
      try {
        await updateEvaluationStatus(id, targetStatus, reason)
        success++
      } catch {
        failed++
      }
    }
    showMsg(`Bulk ${targetStatus.toLowerCase()}: ${success} succeeded${failed ? `, ${failed} failed` : ''}`)
    await loadAllScores(compId)
    setBulkStatus('')
    setBulkReason('')
    setShowBulkReason(false)
  }

  const loadAudit = async (evalId) => {
    try {
      const logs = await getEvaluationAudit(evalId)
      setAuditLogs(logs)
    } catch {
      setAuditLogs([])
    }
  }

  const handleRowClick = async (evalEntry) => {
    if (activeEval?.evaluation_id === evalEntry.evaluation_id) {
      setActiveEval(null)
      setAuditLogs([])
      return
    }
    setActiveEval(evalEntry)
    await loadAudit(evalEntry.evaluation_id)
  }

  const showMsg = (msg) => {
    setActionMsg(msg)
    setTimeout(() => setActionMsg(''), 3000)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Head Judge Dashboard</h1>
        <div className="flex gap-2 items-center">
          <select
            value={compId}
            onChange={e => { setCompId(e.target.value); setActiveEval(null) }}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="">Select competition</option>
            {competitions.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button
            onClick={() => loadAllScores(compId)}
            disabled={!compId}
            className="px-4 py-2 bg-indigo-600 text-white rounded text-sm disabled:opacity-50"
          >
            Load
          </button>
        </div>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm">{error}</div>}
      {actionMsg && <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded text-sm">{actionMsg}</div>}

      {loading ? (
        <div className="text-gray-500">Loading...</div>
      ) : !compId ? (
        <div className="text-gray-500">Select a competition to view all judges' evaluations.</div>
      ) : (
        <>
          <div className="mb-4 flex items-center gap-3">
            <span className="text-sm text-gray-600">
              {avgScores.length} team(s) ranked
            </span>
            <div className="flex items-center gap-2 ml-auto">
              <select
                value={bulkStatus}
                onChange={e => { setBulkStatus(e.target.value); setShowBulkReason(e.target.value === 'OPEN') }}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="">Bulk action...</option>
                <option value="LOCKED">Lock All</option>
                <option value="FINALIZED">Finalize All</option>
                <option value="OPEN">Reopen All</option>
              </select>
              {showBulkReason && (
                <input
                  type="text"
                  placeholder="Reason for reopening"
                  value={bulkReason}
                  onChange={e => setBulkReason(e.target.value)}
                  className="border rounded px-2 py-1 text-sm w-48"
                />
              )}
              <button
                onClick={() => handleBulkStatus(bulkStatus)}
                disabled={!bulkStatus || allScores.length === 0}
                className="px-3 py-1 bg-indigo-600 text-white rounded text-sm disabled:opacity-50"
              >
                Apply
              </button>
            </div>
          </div>

          {/* Averaged score table */}
          <div className="overflow-x-auto border rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="p-3 text-left">Rank</th>
                  <th className="p-3 text-left">Team</th>
                  <th className="p-3 text-center">Judges</th>
                  <th className="p-3 text-center">Total</th>
                  {criteria.map(c => (
                    <th key={c.id} className="p-3 text-center">{c.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {avgScores.length === 0 && (
                  <tr><td colSpan={criteria.length + 4} className="p-4 text-center text-gray-400">No scores yet</td></tr>
                )}
                {avgScores.map((team, idx) => (
                  <tr key={team.team_id} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-bold text-indigo-600">#{idx + 1}</td>
                    <td className="p-3 font-medium">{team.team_name || 'Team ' + team.team_id}</td>
                    <td className="p-3 text-center">{team.num_judges}</td>
                    <td className="p-3 text-center font-bold">{team.total_score} / {team.max_possible}</td>
                    {criteria.map(c => {
                      const cs = team.criterion_scores[c.name]
                      return (
                        <td key={c.id} className="p-3 text-center">
                          {cs ? (
                            <span>{cs.avg} <span className="text-xs text-gray-400">({cs.count})</span></span>
                          ) : (
                            <span className="text-gray-300">—</span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Individual evaluation management */}
          <h2 className="text-lg font-semibold mt-8 mb-3">Manage Individual Evaluations</h2>
          <div className="overflow-x-auto border rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="p-3 text-left">Team</th>
                  <th className="p-3 text-left">Judge</th>
                  <th className="p-3 text-center">Status</th>
                  {criteria.map(c => (
                    <th key={c.id} className="p-3 text-center">{c.name}</th>
                  ))}
                  <th className="p-3 text-center">Actions</th>
                </tr>
              </thead>
              <tbody>
                {allScores.map(ev => (
                  <tr key={ev.evaluation_id} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{ev.team_name || `Team ${ev.team_id}`}</td>
                    <td className="p-3">{ev.judge_email}</td>
                    <td className="p-3 text-center"><StatusBadge status={ev.status} /></td>
                    {criteria.map(c => {
                      const scoreRow = ev.scores?.find(s => s.criterion_id === c.id)
                      return (
                        <td key={c.id} className="p-3 text-center">
                          {scoreRow ? (
                            <div className="flex flex-col items-center gap-1">
                              <span className="font-medium">{scoreRow.score}</span>
                              {scoreRow.corrected_by_user_id && (
                                <span className="text-xs text-orange-500">corrected</span>
                              )}
                              <button
                                onClick={() => setCorrectModal({ ...scoreRow, evaluation_id: ev.evaluation_id })}
                                className="text-xs text-indigo-600 hover:underline"
                              >
                                Edit
                              </button>
                            </div>
                          ) : (
                            <span className="text-gray-300">—</span>
                          )}
                        </td>
                      )
                    })}
                    <td className="p-3 text-center">
                      <button
                        onClick={() => handleRowClick(ev)}
                        className="text-xs text-indigo-600 hover:underline"
                      >
                        {activeEval?.evaluation_id === ev.evaluation_id ? 'Hide' : 'Audit'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Audit panel */}
          {activeEval && (
            <div className="mt-6 border rounded-lg p-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">
                  Evaluation Details — {activeEval.team_name} / {activeEval.judge_email}
                </h2>
                <StatusBadge status={activeEval.status} />
              </div>

              <div className="mb-4 flex gap-2 flex-wrap">
                {activeEval.status !== 'LOCKED' && (
                  <button
                    onClick={() => handleStatusChange(activeEval.evaluation_id, 'LOCKED')}
                    className="px-3 py-1 bg-yellow-500 text-white rounded text-sm"
                  >Lock</button>
                )}
                {activeEval.status === 'LOCKED' && (
                  <>
                    <button
                      onClick={() => handleStatusChange(activeEval.evaluation_id, 'FINALIZED')}
                      className="px-3 py-1 bg-green-600 text-white rounded text-sm"
                    >Finalize</button>
                    <button
                      onClick={() => handleStatusChange(activeEval.evaluation_id, 'OPEN')}
                      className="px-3 py-1 bg-gray-400 text-white rounded text-sm"
                    >Unlock</button>
                  </>
                )}
                {activeEval.status === 'FINALIZED' && (
                  <div className="flex gap-2 items-center">
                    <input
                      type="text"
                      placeholder="Reason required to reopen"
                      value={reopenReason}
                      onChange={e => setReopenReason(e.target.value)}
                      className="border rounded px-2 py-1 text-sm flex-1"
                    />
                    <button
                      onClick={() => handleStatusChange(activeEval.evaluation_id, 'OPEN', reopenReason)}
                      disabled={!reopenReason.trim()}
                      className="px-3 py-1 bg-gray-600 text-white rounded text-sm disabled:opacity-50"
                    >Reopen</button>
                  </div>
                )}
              </div>

              {/* Audit log */}
              <div>
                <h3 className="text-sm font-medium text-gray-600 mb-2">Audit Trail</h3>
                {auditLogs.length === 0 ? (
                  <p className="text-sm text-gray-400">No actions recorded.</p>
                ) : (
                  <div className="space-y-1">
                    {auditLogs.map(log => (
                      <div key={log.id} className="flex gap-3 text-xs bg-gray-50 p-2 rounded">
                        <span className="text-gray-400 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</span>
                        <span className="font-medium text-indigo-700">{log.action}</span>
                        {log.old_value && log.new_value && (
                          <span className="text-gray-600">{log.old_value} → {log.new_value}</span>
                        )}
                        {log.actor_role && <span className="text-gray-400">by {log.actor_role}</span>}
                        {log.reason && <span className="text-gray-500 italic">"{log.reason}"</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Correction modal */}
      {correctModal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 shadow-xl">
            <h3 className="text-lg font-semibold mb-4">Correct Score</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">New Score (1-{criteria.find(c => c.id === correctModal?.criterion_id)?.weight || 10})</label>
                <input
                  type="number"
                  min="1"
                  max={criteria.find(c => c.id === correctModal?.criterion_id)?.weight || 10}
                  step="1"
                  value={correctScoreValue}
                  onChange={e => setCorrectScoreValue(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Reason (required)</label>
                <textarea
                  value={correctReason}
                  onChange={e => setCorrectReason(e.target.value)}
                  className="w-full border rounded px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Explain why this correction is needed..."
                />
              </div>
              {error && <p className="text-red-600 text-sm">{error}</p>}
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => { setCorrectModal(null); setCorrectScoreValue(''); setCorrectReason(''); setError('') }}
                className="px-4 py-2 bg-gray-200 rounded text-sm"
              >Cancel</button>
              <button
                onClick={handleCorrection}
                disabled={!correctScoreValue || !correctReason.trim()}
                className="px-4 py-2 bg-indigo-600 text-white rounded text-sm disabled:opacity-50"
              >Save Correction</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
