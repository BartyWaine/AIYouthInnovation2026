import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getTeam } from '../api/teams'

export default function TeamDetail() {
  const { id } = useParams()
  const [team, setTeam] = useState(null)

  useEffect(() => { getTeam(id).then(setTeam) }, [id])

  if (!team) return <div className="p-6">Loading...</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Link to="/teams" className="text-indigo-600 hover:underline">&larr; Back to Teams</Link>
      <h1 className="text-3xl font-bold mt-4 mb-2">{team.name}</h1>
      <p className="text-gray-500 mb-6">Competition ID: {team.competition_id}</p>
      <h2 className="text-xl font-semibold mb-4">Members ({team.members?.length || 0})</h2>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50"><tr><th className="p-3">User ID</th><th className="p-3">Email</th><th className="p-3">Role</th></tr></thead>
          <tbody>{(team.members || []).map(m => (
            <tr key={m.id} className="border-t">
              <td className="p-3">{m.user_id}</td>
              <td className="p-3">{m.email}</td>
              <td className="p-3">{m.is_leader ? <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">Leader</span> : 'Member'}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
