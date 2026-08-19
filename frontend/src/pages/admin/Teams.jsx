import { useEffect, useState } from 'react'
import { listTeams, createTeam, deleteTeam } from '../../api/teams'
import { listCompetitions } from '../../api/competitions'
import { Link } from 'react-router-dom'

export default function AdminTeams() {
  const [teams, setTeams] = useState([])
  const [comps, setComps] = useState([])
  const [name, setName] = useState('')
  const [compId, setCompId] = useState('')
  const [msg, setMsg] = useState('')

  const load = () => listTeams().then(setTeams)
  useEffect(() => { load(); listCompetitions().then(setComps) }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await createTeam({ name, competition_id: parseInt(compId) })
      setName('')
      setMsg('Team created!')
      load()
    } catch (err) { setMsg(err.response?.data?.detail || 'Error') }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this team?')) return
    await deleteTeam(id)
    load()
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Manage Teams</h1>

      <form onSubmit={handleCreate} className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-lg font-semibold mb-4">Create New Team</h2>
        {msg && <div className="bg-blue-100 text-blue-700 p-2 rounded mb-3 text-sm">{msg}</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input type="text" placeholder="Team Name" value={name} onChange={e => setName(e.target.value)} className="border p-3 rounded" required />
          <select value={compId} onChange={e => setCompId(e.target.value)} className="border p-3 rounded" required>
            <option value="">Select Competition</option>
            {comps.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <button type="submit" className="mt-4 bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700">Create</button>
      </form>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50"><tr><th className="p-3">ID</th><th className="p-3">Name</th><th className="p-3">Competition</th><th className="p-3">Members</th><th className="p-3">Actions</th></tr></thead>
          <tbody>{teams.map(t => (
            <tr key={t.id} className="border-t hover:bg-gray-50">
              <td className="p-3">{t.id}</td>
              <td className="p-3 font-medium">{t.name}</td>
              <td className="p-3">{t.competition_id}</td>
              <td className="p-3">{t.members_count || 0}</td>
              <td className="p-3 flex gap-2">
                <Link to={`/teams/${t.id}`} className="text-indigo-600 hover:underline text-sm">View</Link>
                <button onClick={() => handleDelete(t.id)} className="text-red-600 hover:underline text-sm">Delete</button>
              </td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
