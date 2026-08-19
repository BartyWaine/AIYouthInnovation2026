import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getCompetition, getLeaderboard } from '../api/competitions'
import { useAuth } from '../context/AuthContext'

export function CompetitionDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [comp, setComp] = useState(null)
  const [board, setBoard] = useState([])

  useEffect(() => {
    getCompetition(id).then(setComp)
    getLeaderboard(id).then(setBoard).catch(() => {})
  }, [id])

  if (!comp) return <div className="p-6">Loading...</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Link to="/competitions" className="text-indigo-600 hover:underline">&larr; Back</Link>
      <h1 className="text-3xl font-bold mt-4 mb-2">{comp.name}</h1>
      <p className="text-gray-500 mb-6">{comp.category}</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg shadow text-center"><p className="text-2xl font-bold text-indigo-600">{comp.teams_count}</p><p className="text-gray-500 text-sm">Teams</p></div>
        <div className="bg-white p-4 rounded-lg shadow text-center"><p className="text-2xl font-bold text-green-600">{comp.deliverables_count}</p><p className="text-gray-500 text-sm">Deliverables</p></div>
        <Link to={`/competitions/${id}/deliverables`} className="bg-white p-4 rounded-lg shadow text-center hover:bg-indigo-50"><p className="text-indigo-600 font-semibold">Manage Deliverables &rarr;</p></Link>
        <Link to={`/competitions/${id}/teams`} className="bg-white p-4 rounded-lg shadow text-center hover:bg-indigo-50"><p className="text-indigo-600 font-semibold">View Teams &rarr;</p></Link>
      </div>

      <h2 className="text-xl font-semibold mb-4">Leaderboard</h2>
      {board.length === 0 ? <p className="text-gray-400">No scores yet</p> : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50"><tr><th className="p-3">Rank</th><th className="p-3">Team</th><th className="p-3">Score</th><th className="p-3">Evaluations</th></tr></thead>
            <tbody>{board.map(b => (
              <tr key={b.team_id} className="border-t">
                <td className="p-3 font-bold text-indigo-600">{b.rank}</td>
                <td className="p-3 font-medium">{b.team_name}</td>
                <td className="p-3">{b.total_score.toFixed(1)}</td>
                <td className="p-3">{b.num_scores}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  )
}
