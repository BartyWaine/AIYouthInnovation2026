import { useEffect, useState } from 'react'
import { getAveragedScores } from '../api/judges'
import { listCompetitions } from '../api/competitions'

export default function Scoreboard() {
  const [competitions, setCompetitions] = useState([])
  const [compId, setCompId] = useState('')
  const [scores, setScores] = useState([])
  const [criteria, setCriteria] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    listCompetitions().then(setCompetitions).catch(() => {})
  }, [])

  useEffect(() => {
    if (!compId) return
    setLoading(true)
    setError('')
    getAveragedScores(compId)
      .then(data => {
        setScores(data)
        if (data.length > 0) {
          const crits = Object.entries(data[0].criterion_scores || {}).map(([name, info]) => ({
            name,
            weight: info.weight || 0,
          }))
          setCriteria(crits.sort((a, b) => b.weight - a.weight))
        }
      })
      .catch(err => setError(err.response?.data?.detail || 'Failed to load scores'))
      .finally(() => setLoading(false))
  }, [compId])

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Scoreboard</h1>
        <select
          value={compId}
          onChange={e => setCompId(e.target.value)}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="">Select competition</option>
          {competitions.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm">{error}</div>}

      {!compId && (
        <p className="text-gray-500">Select a competition to view the scoreboard.</p>
      )}

      {loading && <p className="text-gray-500">Loading...</p>}

      {compId && !loading && scores.length === 0 && (
        <p className="text-gray-500">No scores available yet for this competition.</p>
      )}

      {compId && !loading && scores.length > 0 && (
        <>
          <div className="mb-4 text-sm text-gray-600">
            {scores.length} team(s) ranked | Total score: weighted average out of 100
          </div>

          <div className="overflow-x-auto border rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-indigo-50 border-b">
                <tr>
                  <th className="p-3 text-left">Rank</th>
                  <th className="p-3 text-left">Team</th>
                  <th className="p-3 text-center">Judges</th>
                  <th className="p-3 text-center">Score / 100</th>
                  {criteria.map(c => (
                    <th key={c.name} className="p-3 text-center">
                      {c.name}
                      <span className="block text-xs font-normal text-gray-400">x{c.weight}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {scores.map((team, idx) => (
                  <tr key={team.team_id} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-bold text-indigo-600">#{idx + 1}</td>
                    <td className="p-3 font-medium">{team.team_name || 'Team ' + team.team_id}</td>
                    <td className="p-3 text-center">{team.num_judges}</td>
                    <td className="p-3 text-center font-bold text-lg">{team.total_score}</td>
                    {criteria.map(c => {
                      const cs = team.criterion_scores?.[c.name]
                      return (
                        <td key={c.name} className="p-3 text-center">
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
        </>
      )}
    </div>
  )
}
