import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'

export default function CompetitionTeams() {
  const { compId } = useParams()
  const [teams, setTeams] = useState([])

  useEffect(() => { api.get(`/competitions/${compId}/teams`).then(r => setTeams(r.data)) }, [compId])

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Link to={`/competitions/${compId}`} className="text-indigo-600 hover:underline">&larr; Back</Link>
      <h1 className="text-2xl font-bold mt-4 mb-6">Teams in Competition</h1>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50"><tr><th className="p-3">ID</th><th className="p-3">Name</th><th className="p-3">Members</th><th className="p-3">Actions</th></tr></thead>
          <tbody>{teams.map(t => (
            <tr key={t.id} className="border-t hover:bg-gray-50">
              <td className="p-3">{t.id}</td><td className="p-3 font-medium">{t.name}</td><td className="p-3">{t.members_count}</td>
              <td className="p-3"><Link to={`/teams/${t.id}`} className="text-indigo-600 hover:underline text-sm">Details</Link></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
