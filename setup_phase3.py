import pathlib

SRC = pathlib.Path(r"D:\AIYouthInnovation2026\frontend\src")

# --- API: Deliverables & Submissions ---
(SRC / "api" / "deliverables.js").write_text("""import api from './client'

export const listDeliverables = (compId) => api.get('/deliverables', { params: { competition_id: compId } }).then(r => r.data)
export const createDeliverable = (data) => api.post('/deliverables', null, { params: data }).then(r => r.data)
export const listSubmissions = (delivId) => api.get(`/deliverables/${delivId}/submissions`).then(r => r.data)
export const createSubmission = (delivId, teamId) => api.post(`/deliverables/${delivId}/submissions`, null, { params: { team_id: teamId } }).then(r => r.data)
export const updateSubmissionStatus = (subId, status) => api.patch(`/deliverables/submissions/${subId}/status`, null, { params: { new_status: status } }).then(r => r.data)
""")

# --- API: Judges ---
(SRC / "api" / "judges.js").write_text("""import api from './client'

export const createJudge = (userId) => api.post('/judges', null, { params: { user_id: userId } }).then(r => r.data)
export const createAssignment = (judgeId, teamId, compId) => api.post('/judges/assignments', null, { params: { judge_id: judgeId, team_id: teamId, competition_id: compId } }).then(r => r.data)
export const listEvaluations = (compId) => api.get(`/judges/competitions/${compId}/evaluations`).then(r => r.data)
export const createEvaluation = (judgeId, teamId, compId) => api.post('/judges/evaluations', null, { params: { judge_id: judgeId, team_id: teamId, competition_id: compId } }).then(r => r.data)
export const addScore = (evalId, criterionId, score, comment) => api.post(`/judges/evaluations/${evalId}/scores`, null, { params: { criterion_id: criterionId, score, comment } }).then(r => r.data)
export const listCriteria = () => api.get('/admin/evaluation-criteria').then(r => r.data)
export const createCriterion = (name, weight) => api.post('/admin/evaluation-criteria', null, { params: { name, weight } }).then(r => r.data)
""")

# --- Deliverables Page ---
(SRC / "pages" / "admin" / "Deliverables.jsx").write_text("""import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { listDeliverables, createDeliverable, listSubmissions } from '../../api/deliverables'
import { getCompetition } from '../../api/competitions'

export default function Deliverables() {
  const { compId } = useParams()
  const [comp, setComp] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [deadline, setDeadline] = useState('')
  const [msg, setMsg] = useState('')
  const [expandedDeliv, setExpandedDeliv] = useState(null)
  const [submissions, setSubmissions] = useState([])

  const load = () => {
    getCompetition(compId).then(setComp)
    listDeliverables(compId).then(setDeliverables)
  }
  useEffect(() => { load() }, [compId])

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await createDeliverable({ competition_id: parseInt(compId), name, description: desc, deadline: deadline || undefined })
      setName(''); setDesc(''); setDeadline('')
      setMsg('Deliverable created!')
      load()
    } catch (err) { setMsg(err.response?.data?.detail || 'Error') }
  }

  const toggleSubmissions = async (delivId) => {
    if (expandedDeliv === delivId) { setExpandedDeliv(null); return }
    const subs = await listSubmissions(delivId)
    setSubmissions(subs)
    setExpandedDeliv(delivId)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Link to={`/competitions/${compId}`} className="text-indigo-600 hover:underline">&larr; Back to Competition</Link>
      <h1 className="text-2xl font-bold mt-4 mb-2">Deliverables</h1>
      <p className="text-gray-500 mb-6">{comp?.name}</p>

      <form onSubmit={handleCreate} className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-lg font-semibold mb-4">Create Deliverable</h2>
        {msg && <div className="bg-blue-100 text-blue-700 p-2 rounded mb-3 text-sm">{msg}</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input type="text" placeholder="Name" value={name} onChange={e => setName(e.target.value)} className="border p-3 rounded" required />
          <input type="datetime-local" value={deadline} onChange={e => setDeadline(e.target.value)} className="border p-3 rounded" />
        </div>
        <textarea placeholder="Description" value={desc} onChange={e => setDesc(e.target.value)} className="w-full border p-3 rounded mt-4" rows="2" />
        <button type="submit" className="mt-4 bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700">Create</button>
      </form>

      <div className="space-y-4">
        {deliverables.map(d => (
          <div key={d.id} className="bg-white rounded-lg shadow p-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">{d.name}</h3>
                <p className="text-sm text-gray-500">{d.description || 'No description'}</p>
                {d.deadline && <p className="text-xs text-red-500 mt-1">Deadline: {new Date(d.deadline).toLocaleString()}</p>}
              </div>
              <button onClick={() => toggleSubmissions(d.id)} className="text-indigo-600 hover:underline text-sm">
                {expandedDeliv === d.id ? 'Hide' : 'View'} Submissions
              </button>
            </div>
            {expandedDeliv === d.id && (
              <div className="mt-4 border-t pt-4">
                {submissions.length === 0 ? <p className="text-gray-400 text-sm">No submissions yet</p> : (
                  <table className="w-full text-left text-sm">
                    <thead><tr><th className="p-2">ID</th><th className="p-2">Team</th><th className="p-2">Version</th><th className="p-2">Status</th></tr></thead>
                    <tbody>{submissions.map(s => (
                      <tr key={s.id} className="border-t"><td className="p-2">{s.id}</td><td className="p-2">{s.team_id}</td><td className="p-2">v{s.version}</td><td className="p-2"><span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">{s.status}</span></td></tr>
                    ))}</tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        ))}
        {deliverables.length === 0 && <p className="text-gray-400">No deliverables yet</p>}
      </div>
    </div>
  )
}
""")

# --- Judge Management Page ---
(SRC / "pages" / "admin" / "JudgeManagement.jsx").write_text("""import { useEffect, useState } from 'react'
import { createJudge, createAssignment, listCriteria, createCriterion } from '../../api/judges'
import { listUsers } from '../../api/admin'
import { listTeams } from '../../api/teams'
import { listCompetitions } from '../../api/competitions'

export default function JudgeManagement() {
  const [users, setUsers] = useState([])
  const [teams, setTeams] = useState([])
  const [comps, setComps] = useState([])
  const [criteria, setCriteria] = useState([])
  const [msg, setMsg] = useState('')

  const [judgeUserId, setJudgeUserId] = useState('')
  const [assignJudgeId, setAssignJudgeId] = useState('')
  const [assignTeamId, setAssignTeamId] = useState('')
  const [assignCompId, setAssignCompId] = useState('')
  const [critName, setCritName] = useState('')
  const [critWeight, setCritWeight] = useState('')

  useEffect(() => {
    listUsers().then(setUsers).catch(() => {})
    listTeams().then(setTeams).catch(() => {})
    listCompetitions().then(setComps).catch(() => {})
    listCriteria().then(setCriteria).catch(() => {})
  }, [])

  const handleCreateJudge = async () => {
    try { await createJudge(parseInt(judgeUserId)); setMsg('Judge created!'); setJudgeUserId('') }
    catch (err) { setMsg(err.response?.data?.detail || 'Error') }
  }

  const handleAssign = async () => {
    try { await createAssignment(parseInt(assignJudgeId), parseInt(assignTeamId), parseInt(assignCompId)); setMsg('Assignment created!') }
    catch (err) { setMsg(err.response?.data?.detail || 'Error') }
  }

  const handleCreateCriterion = async () => {
    try {
      await createCriterion(critName, parseFloat(critWeight))
      setCritName(''); setCritWeight('')
      setMsg('Criterion created!')
      listCriteria().then(setCriteria)
    } catch (err) { setMsg(err.response?.data?.detail || 'Error') }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Judge Management</h1>
      {msg && <div className="bg-blue-100 text-blue-700 p-3 rounded mb-6 text-sm">{msg}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Create Judge</h2>
          <select value={judgeUserId} onChange={e => setJudgeUserId(e.target.value)} className="w-full border p-3 rounded mb-3">
            <option value="">Select User</option>
            {users.filter(u => u.role === 'JUDGE').map(u => <option key={u.id} value={u.id}>{u.email}</option>)}
          </select>
          <button onClick={handleCreateJudge} className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 w-full">Create Judge</button>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Assign Judge to Team</h2>
          <input type="number" placeholder="Judge ID" value={assignJudgeId} onChange={e => setAssignJudgeId(e.target.value)} className="w-full border p-3 rounded mb-3" />
          <select value={assignTeamId} onChange={e => setAssignTeamId(e.target.value)} className="w-full border p-3 rounded mb-3">
            <option value="">Select Team</option>
            {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <select value={assignCompId} onChange={e => setAssignCompId(e.target.value)} className="w-full border p-3 rounded mb-3">
            <option value="">Select Competition</option>
            {comps.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <button onClick={handleAssign} className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 w-full">Assign</button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Evaluation Criteria</h2>
        <div className="flex gap-4 mb-4">
          <input type="text" placeholder="Criterion Name" value={critName} onChange={e => setCritName(e.target.value)} className="flex-1 border p-3 rounded" />
          <input type="number" step="0.1" placeholder="Weight" value={critWeight} onChange={e => setCritWeight(e.target.value)} className="w-24 border p-3 rounded" />
          <button onClick={handleCreateCriterion} className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">Add</button>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50"><tr><th className="p-2">ID</th><th className="p-2">Name</th><th className="p-2">Weight</th></tr></thead>
          <tbody>{criteria.map(c => (
            <tr key={c.id} className="border-t"><td className="p-2">{c.id}</td><td className="p-2">{c.name}</td><td className="p-2">{c.weight}</td></tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
""")

# --- Updated Competitions Detail with Deliverables link ---
(SRC / "pages" / "Competitions.jsx").write_text("""import { useEffect, useState } from 'react'
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
""")

# --- Competition Teams Page ---
(SRC / "pages" / "CompetitionTeams.jsx").write_text("""import { useEffect, useState } from 'react'
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
""")

# --- Updated App.jsx with all new routes ---
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
import Deliverables from './pages/admin/Deliverables'
import JudgeManagement from './pages/admin/JudgeManagement'
import TeamDetail from './pages/TeamDetail'
import CompetitionTeams from './pages/CompetitionTeams'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-6">Loading...</div>
  return user ? children : <Navigate to="/login" />
}

function AppRoutes() {
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/competitions" element={<PrivateRoute><AdminCompetitions /></PrivateRoute>} />
          <Route path="/competitions/:id" element={<PrivateRoute><CompetitionDetail /></PrivateRoute>} />
          <Route path="/competitions/:compId/deliverables" element={<PrivateRoute><Deliverables /></PrivateRoute>} />
          <Route path="/competitions/:compId/teams" element={<PrivateRoute><CompetitionTeams /></PrivateRoute>} />
          <Route path="/teams" element={<PrivateRoute><AdminTeams /></PrivateRoute>} />
          <Route path="/teams/:id" element={<PrivateRoute><TeamDetail /></PrivateRoute>} />
          <Route path="/users" element={<PrivateRoute><AdminUsers /></PrivateRoute>} />
          <Route path="/judges" element={<PrivateRoute><JudgeManagement /></PrivateRoute>} />
          <Route path="/audit-logs" element={<PrivateRoute><AuditLogs /></PrivateRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </div>
    </>
  )
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}
""")

# --- Updated Navbar ---
(SRC / "components" / "Navbar.jsx").write_text("""import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'ADMIN'

  return (
    <nav className="bg-indigo-600 text-white px-6 py-3 flex justify-between items-center shadow-lg">
      <Link to="/" className="text-xl font-bold tracking-tight">AI Youth Innovation 2026</Link>
      <div className="flex gap-3 items-center text-sm">
        {user ? (
          <>
            <Link to="/dashboard" className="hover:text-indigo-200 px-2 py-1">Dashboard</Link>
            <Link to="/competitions" className="hover:text-indigo-200 px-2 py-1">Competitions</Link>
            <Link to="/teams" className="hover:text-indigo-200 px-2 py-1">Teams</Link>
            {isAdmin && <Link to="/judges" className="hover:text-indigo-200 px-2 py-1">Judges</Link>}
            {isAdmin && <Link to="/users" className="hover:text-indigo-200 px-2 py-1">Users</Link>}
            {isAdmin && <Link to="/audit-logs" className="hover:text-indigo-200 px-2 py-1">Logs</Link>}
            <span className="text-indigo-200 ml-2">{user.email}</span>
            <button onClick={logout} className="bg-indigo-800 px-3 py-1 rounded hover:bg-indigo-900 ml-1">Logout</button>
          </>
        ) : (
          <Link to="/login" className="hover:text-indigo-200">Login</Link>
        )}
      </div>
    </nav>
  )
}
""")

print("All pages created!")
print("New: Deliverables, JudgeManagement, CompetitionTeams")
print("Updated: App.jsx, Navbar.jsx, Competitions.jsx")