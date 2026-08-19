import pathlib

SRC = pathlib.Path(r"D:\AIYouthInnovation2026\frontend\src")

# --- Admin: Competitions Management ---
(SRC / "pages" / "admin" / "Competitions.jsx").write_text("""import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listCompetitions, createCompetition, deleteCompetition } from '../../api/competitions'

const CATEGORIES = ['AI for Engineering and Technology', 'AI for Social Innovation', 'AI for Entrepreneurship']

export default function AdminCompetitions() {
  const [comps, setComps] = useState([])
  const [name, setName] = useState('')
  const [category, setCategory] = useState(CATEGORIES[0])
  const [msg, setMsg] = useState('')

  const load = () => listCompetitions().then(setComps)
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await createCompetition({ name, category })
      setName('')
      setMsg('Competition created!')
      load()
    } catch (err) { setMsg(err.response?.data?.detail || 'Error') }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this competition?')) return
    await deleteCompetition(id)
    load()
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Manage Competitions</h1>

      <form onSubmit={handleCreate} className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-lg font-semibold mb-4">Create New Competition</h2>
        {msg && <div className="bg-blue-100 text-blue-700 p-2 rounded mb-3 text-sm">{msg}</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input type="text" placeholder="Competition Name" value={name} onChange={e => setName(e.target.value)} className="border p-3 rounded" required />
          <select value={category} onChange={e => setCategory(e.target.value)} className="border p-3 rounded">
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <button type="submit" className="mt-4 bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700">Create</button>
      </form>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50"><tr><th className="p-3">ID</th><th className="p-3">Name</th><th className="p-3">Category</th><th className="p-3">Actions</th></tr></thead>
          <tbody>{comps.map(c => (
            <tr key={c.id} className="border-t hover:bg-gray-50">
              <td className="p-3">{c.id}</td>
              <td className="p-3 font-medium">{c.name}</td>
              <td className="p-3 text-sm">{c.category}</td>
              <td className="p-3 flex gap-2">
                <Link to={`/competitions/${c.id}`} className="text-indigo-600 hover:underline text-sm">View</Link>
                <button onClick={() => handleDelete(c.id)} className="text-red-600 hover:underline text-sm">Delete</button>
              </td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
""")

# --- Admin: Teams Management ---
(SRC / "pages" / "admin" / "Teams.jsx").write_text("""import { useEffect, useState } from 'react'
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
""")

# --- Admin: Users Management ---
(SRC / "api" / "admin.js").write_text("""import api from './client'

export const listUsers = () => api.get('/admin/users').then(r => r.data)
export const createUser = (email, password, role) => api.post('/admin/users', null, { params: { email, password, role } }).then(r => r.data)
export const listAuditLogs = () => api.get('/admin/audit-logs').then(r => r.data)
""")

(SRC / "pages" / "admin" / "Users.jsx").write_text("""import { useEffect, useState } from 'react'
import { listUsers, createUser } from '../../api/admin'

const ROLES = ['TEAM_MEMBER', 'TEAM_LEADER', 'JUDGE', 'LECTURER', 'ADMIN']

export default function AdminUsers() {
  const [users, setUsers] = useState([])
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('TEAM_MEMBER')
  const [msg, setMsg] = useState('')

  const load = () => listUsers().then(setUsers).catch(() => {})
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await createUser(email, password, role)
      setEmail('')
      setPassword('')
      setMsg('User created!')
      load()
    } catch (err) { setMsg(err.response?.data?.detail || 'Error') }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Manage Users</h1>

      <form onSubmit={handleCreate} className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-lg font-semibold mb-4">Create New User</h2>
        {msg && <div className="bg-blue-100 text-blue-700 p-2 rounded mb-3 text-sm">{msg}</div>}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="border p-3 rounded" required />
          <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="border p-3 rounded" required />
          <select value={role} onChange={e => setRole(e.target.value)} className="border p-3 rounded">
            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        <button type="submit" className="mt-4 bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700">Create</button>
      </form>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50"><tr><th className="p-3">ID</th><th className="p-3">Email</th><th className="p-3">Role</th></tr></thead>
          <tbody>{users.map(u => (
            <tr key={u.id} className="border-t hover:bg-gray-50">
              <td className="p-3">{u.id}</td>
              <td className="p-3">{u.email}</td>
              <td className="p-3"><span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">{u.role}</span></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
""")

# --- Admin: Audit Logs ---
(SRC / "pages" / "admin" / "AuditLogs.jsx").write_text("""import { useEffect, useState } from 'react'
import { listAuditLogs } from '../../api/admin'

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  useEffect(() => { listAuditLogs().then(setLogs).catch(() => {}) }, [])

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50"><tr><th className="p-3">ID</th><th className="p-3">User</th><th className="p-3">Action</th><th className="p-3">Entity</th><th className="p-3">Timestamp</th></tr></thead>
          <tbody>{logs.map(l => (
            <tr key={l.id} className="border-t hover:bg-gray-50">
              <td className="p-3">{l.id}</td>
              <td className="p-3">{l.user_id}</td>
              <td className="p-3 font-mono">{l.action}</td>
              <td className="p-3">{l.entity_type} #{l.entity_id}</td>
              <td className="p-3 text-gray-500">{l.timestamp}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
""")

# --- Team Detail Page ---
(SRC / "pages" / "TeamDetail.jsx").write_text("""import { useEffect, useState } from 'react'
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
""")

# --- Updated App.jsx with all routes ---
(SRC / "App.jsx").write_text("""import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import { CompetitionDetail } from './pages/Competitions'
import AdminCompetitions from './pages/admin/Competitions'
import AdminTeams from './pages/admin/Teams'
import AdminUsers from './pages/admin/Users'
import AuditLogs from './pages/admin/AuditLogs'
import TeamDetail from './pages/TeamDetail'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-6">Loading...</div>
  return user ? children : <Navigate to="/login" />
}

function AppRoutes() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/competitions" element={<PrivateRoute><AdminCompetitions /></PrivateRoute>} />
        <Route path="/competitions/:id" element={<PrivateRoute><CompetitionDetail /></PrivateRoute>} />
        <Route path="/teams" element={<PrivateRoute><AdminTeams /></PrivateRoute>} />
        <Route path="/teams/:id" element={<PrivateRoute><TeamDetail /></PrivateRoute>} />
        <Route path="/users" element={<PrivateRoute><AdminUsers /></PrivateRoute>} />
        <Route path="/audit-logs" element={<PrivateRoute><AuditLogs /></PrivateRoute>} />
        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </>
  )
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}
""")

# --- Updated Navbar with all links ---
(SRC / "components" / "Navbar.jsx").write_text("""import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'ADMIN'

  return (
    <nav className="bg-indigo-600 text-white px-6 py-3 flex justify-between items-center shadow-lg">
      <Link to="/" className="text-xl font-bold">AI Youth Innovation 2026</Link>
      <div className="flex gap-4 items-center text-sm">
        {user ? (
          <>
            <Link to="/dashboard" className="hover:text-indigo-200">Dashboard</Link>
            <Link to="/competitions" className="hover:text-indigo-200">Competitions</Link>
            <Link to="/teams" className="hover:text-indigo-200">Teams</Link>
            {isAdmin && <Link to="/users" className="hover:text-indigo-200">Users</Link>}
            {isAdmin && <Link to="/audit-logs" className="hover:text-indigo-200">Audit Logs</Link>}
            <span className="text-indigo-200">{user.email}</span>
            <button onClick={logout} className="bg-indigo-800 px-3 py-1 rounded hover:bg-indigo-900">Logout</button>
          </>
        ) : (
          <Link to="/login" className="hover:text-indigo-200">Login</Link>
        )}
      </div>
    </nav>
  )
}
""")

print("All admin pages created!")
print("Pages: Competitions, Teams, Users, AuditLogs, TeamDetail")
print("Updated: App.jsx (routes), Navbar.jsx (links)")