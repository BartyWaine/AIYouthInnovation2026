import { useAuth } from '../context/AuthContext'
import { useEffect, useState } from 'react'
import { listCompetitions } from '../api/competitions'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const { user } = useAuth()
  const [competitions, setCompetitions] = useState([])

  useEffect(() => { listCompetitions().then(setCompetitions).catch(() => {}) }, [])

  const isTeamMember = user?.role === 'TEAM_MEMBER' || user?.role === 'TEAM_LEADER'
  const isJudge = user?.role === 'JUDGE'

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
      <p className="text-gray-600 mb-6">Welcome, <span className="font-semibold">{user?.email}</span> ({user?.role})</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white p-6 rounded-lg shadow"><p className="text-3xl font-bold text-indigo-600">{competitions.length}</p><p className="text-gray-500">Competitions</p></div>
        <div className="bg-white p-6 rounded-lg shadow"><p className="text-3xl font-bold text-green-600">{user?.role}</p><p className="text-gray-500">Your Role</p></div>
        {isTeamMember && <div className="bg-white p-6 rounded-lg shadow"><Link to="/uploads" className="text-indigo-600 hover:underline font-semibold">Go to My Uploads &rarr;</Link></div>}
        {isJudge && <div className="bg-white p-6 rounded-lg shadow"><Link to="/judge-dashboard" className="text-indigo-600 hover:underline font-semibold">Go to Judge Dashboard &rarr;</Link></div>}
        <div className="bg-white p-6 rounded-lg shadow"><Link to="/competitions" className="text-indigo-600 hover:underline font-semibold">View Competitions &rarr;</Link></div>
      </div>
      <h2 className="text-xl font-semibold mb-4">Competitions</h2>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50"><tr><th className="p-3">ID</th><th className="p-3">Name</th><th className="p-3">Category</th><th className="p-3">Actions</th></tr></thead>
          <tbody>{competitions.map(c => (
            <tr key={c.id} className="border-t"><td className="p-3">{c.id}</td><td className="p-3 font-medium">{c.name}</td><td className="p-3">{c.category}</td><td className="p-3"><Link to={`/competitions/${c.id}`} className="text-indigo-600 hover:underline">Details</Link></td></tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
