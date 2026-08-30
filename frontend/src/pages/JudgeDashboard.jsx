import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  getCompetitionSubmissions,
  downloadFile,
  getSubmissionFiles,
} from '../api/deliverables'
import {
  listMyAssignments,
  getCriteria,
  createMyEvaluation,
  addScore,
  getCompetitionScores,
  listMyEvaluations,
  getJudgeAllSubmissions,
} from '../api/judges'
import { getFileIcon, formatFileSize } from '../utils'

export default function JudgeDashboard() {
  const navigate = useNavigate()
  const urlComp = new URLSearchParams(window.location.search).get('comp') || 'all'
  const [compId] = useState(urlComp)
  const isAll = compId === 'all'
  const [assignments, setAssignments] = useState([])
  const [submissions, setSubmissions] = useState([])
  const [criteria, setCriteria] = useState([])
  const [evaluations, setEvaluations] = useState([])
  const [scores, setScores] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('files')
  const [searchTeam, setSearchTeam] = useState('')
  const [localScores, setLocalScores] = useState({})

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [assignData, critData] = await Promise.all([
        listMyAssignments(),
        getCriteria(),
      ])
      let subData, evalData, scoreData
      if (isAll) {
        subData = await getJudgeAllSubmissions()
        evalData = await listMyEvaluations()
        scoreData = []
      } else {
        [subData, evalData, scoreData] = await Promise.all([
          getCompetitionSubmissions(compId),
          listMyEvaluations(compId),
          getCompetitionScores(compId),
        ])
      }
      setAssignments(assignData)
      setSubmissions(subData)
      setCriteria(critData)
      setEvaluations(evalData)
      setScores(scoreData)
      const initScores = {}
      for (const ev of evalData) {
        for (const sc of (ev.scores || [])) {
          initScores[`${ev.team_id}-${sc.criterion_id}`] = sc.score
        }
      }
      setLocalScores(initScores)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  const getEvaluationForTeam = (teamId) => {
    return evaluations.find(e => e.team_id === parseInt(teamId))
  }

  const getScoreForTeam = (teamId) => {
    return scores.find(s => s.team_id === parseInt(teamId))
  }

  const handleScoreSubmit = async (teamId, criterionId, score, comment) => {
    try {
      let evaluation = getEvaluationForTeam(teamId)
      if (!evaluation) {
        const teamSubmission = submissions.find(s => s.team_id === parseInt(teamId))
        const teamCompId = teamSubmission?.competition_id || (isAll ? parseInt(teamSubmission?.competition_id) || 1 : compId)
        const evalResult = await createMyEvaluation(teamId, teamCompId)
        evaluation = { id: evalResult.id, team_id: teamId, scores: [] }
        setEvaluations(prev => [...prev, evaluation])
      }
      await addScore(evaluation.id, criterionId, score, comment)
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit score')
    }
  }

  if (loading) return <div className="p-6">Loading dashboard...</div>
  if (error) return <div className="p-6 text-red-600">{error}</div>

  const teams = {}
  submissions.forEach(sub => {
    if (!teams[sub.team_id]) {
      teams[sub.team_id] = { name: sub.team_name, submissions: [] }
    }
    teams[sub.team_id].submissions.push(sub)
  })
  const teamList = Object.entries(teams)
  const filteredTeams = searchTeam
    ? teamList.filter(([teamId]) => String(teamId) === String(searchTeam))
    : teamList

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Judge Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('files')}
            className={`px-4 py-2 rounded text-sm ${activeTab === 'files' ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
          >
            View Files
          </button>
          <button
            onClick={() => setActiveTab('scores')}
            className={`px-4 py-2 rounded text-sm ${activeTab === 'scores' ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
          >
            Score Teams
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-gray-200 rounded text-sm"
          >
            Back
          </button>
        </div>
      </div>

      {activeTab === 'files' && (
        <>
          <p className="text-gray-500 mb-4">
        {isAll ? `Assigned to ${assignments.length} team(s) across all competitions` : `Assigned to ${assignments.length} team(s) in competition ${compId}`}
        &nbsp;|&nbsp;
        {isAll ? (
          <Link to="/judge-dashboard?comp=1" className="text-indigo-600 hover:underline">View Competition 1</Link>
        ) : (
          <Link to="/judge-dashboard?comp=all" className="text-indigo-600 hover:underline">View All Teams</Link>
        )}
      </p>
          {teamList.length === 0 ? (
            <p className="text-gray-500">No submissions found.</p>
          ) : (
            teamList.map(([teamId, team]) => (
              <div key={teamId} className="mb-8">
                <h2 className="text-xl font-semibold mb-3">
                  {isAll && team.submissions[0]?.competition_name ? team.submissions[0].competition_name + ' - ' : ''}Team: {team.name} (ID: {teamId})
                </h2>
                <div className="space-y-4">
                  {team.submissions.map(sub => (
                    <div key={sub.submission_id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-medium">{sub.deliverable_name}</h3>
                          <span className={`text-xs px-2 py-1 rounded ${
                            sub.status === 'SUBMITTED' || sub.status === 'READY'
                              ? 'bg-green-100 text-green-700'
                              : sub.status === 'OPEN'
                              ? 'bg-gray-100 text-gray-600'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {sub.status}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          Updated: {new Date(sub.updated_at).toLocaleString()}
                        </span>
                      </div>

                      {sub.files && sub.files.length > 0 ? (
                        <div className="mt-3 space-y-2">
                          {sub.files.map(f => (
                            <div key={f.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                              <div className="flex items-center gap-3">
                                <span className="text-2xl">{getFileIcon(f.original_filename)}</span>
                                <div>
                                  <span className="font-medium text-sm">{f.original_filename}</span>
                                  <span className="text-xs text-gray-500 ml-2">
                                    {formatFileSize(f.file_size)}
                                  </span>
                                </div>
                              </div>
                              <button
                                onClick={() => downloadFile(sub.submission_id, f.id, f.original_filename).catch(err => setError(err.message))}
                                className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700"
                              >
                                Download
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-400 mt-2">No files uploaded yet</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </>
      )}

      {activeTab === 'scores' && (
        <>
          <div className="flex gap-3 mb-4 items-center">
            <label className="text-sm font-medium text-gray-700">Go to Team ID:</label>
            <input
              type="number"
              min="1"
              placeholder="Enter team ID"
              value={searchTeam}
              onChange={e => setSearchTeam(e.target.value)}
              className="w-40 px-3 py-1 border rounded text-sm"
            />
            {searchTeam && (
              <button
                onClick={() => setSearchTeam('')}
                className="text-sm text-indigo-600 hover:underline"
              >
                Clear
              </button>
            )}
          </div>
          {teamList.length === 0 ? (
            <p className="text-gray-500">No teams to score.</p>
          ) : filteredTeams.length === 0 ? (
            <p className="text-gray-500">No team found with ID "{searchTeam}".</p>
          ) : (
            filteredTeams.map(([teamId, team]) => {
              const scoreData = getScoreForTeam(teamId)
              const evaluation = getEvaluationForTeam(teamId)
              return (
                <div key={teamId} className="border rounded-lg p-4 mb-6">
                  <div className="flex justify-between items-center mb-3">
                    <h2 className="text-xl font-semibold">Team: {team.name} (ID: {teamId})</h2>
                    {scoreData && (
                      <span className="text-lg font-bold text-indigo-600">
                        Score: {scoreData.total_score}/{scoreData.max_possible} ({scoreData.num_judges || 1} judge{scoreData.num_judges !== 1 ? 's' : ''})
                      </span>
                    )}
                  </div>

                  {evaluation && (
                    <p className="text-xs text-gray-500 mb-2">Evaluation ID: {evaluation.id}</p>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                     {criteria.map(c => {
                      const existing = evaluation?.scores?.find(s => s.criterion === c.name)?.score
                      const savedScore = existing !== undefined ? existing : c.weight
                      const localKey = `${teamId}-${c.id}`
                      const displayValue = localScores[localKey] !== undefined ? localScores[localKey] : savedScore
                      return (
                        <div key={c.id} className="border p-3 rounded">
                          <label className="block text-sm font-medium mb-1">{c.name}</label>
                          <div className="flex items-center gap-2">
                              <input
                               type="number"
                               min="0"
                               max={c.weight}
                               step="1"
                               value={displayValue}
                              onChange={e => setLocalScores(prev => ({ ...prev, [localKey]: parseFloat(e.target.value) || 0 }))}
                              onBlur={e => {
                                const score = parseFloat(e.target.value)
                                if (!isNaN(score)) handleScoreSubmit(teamId, c.id, score, '')
                              }}
                              className="w-full px-2 py-1 border rounded text-sm"
                            />
                          </div>
                          <div className="flex justify-between text-xs text-gray-500">
                            <span>0</span>
                            <span>{c.weight}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })
          )}
        </>
      )}
    </div>
  )
}
