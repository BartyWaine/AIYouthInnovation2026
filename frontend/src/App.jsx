import { Routes, Route, Navigate } from 'react-router-dom'
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
import TeamUploads from './pages/TeamUploads'
import JudgeDashboard from './pages/JudgeDashboard'
import HeadJudgeDashboard from './pages/HeadJudgeDashboard'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-6">Loading...</div>
  return user ? children : <Navigate to="/login" />
}

function RoleRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-6">Loading...</div>
  if (!user) return <Navigate to="/login" />
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" />
  }
  return children
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
          <Route path="/competitions/:compId/deliverables" element={<RoleRoute allowedRoles={['ADMIN']}><Deliverables /></RoleRoute>} />
          <Route path="/competitions/:compId/teams" element={<PrivateRoute><CompetitionTeams /></PrivateRoute>} />
          <Route path="/teams" element={<PrivateRoute><AdminTeams /></PrivateRoute>} />
          <Route path="/teams/:id" element={<PrivateRoute><TeamDetail /></PrivateRoute>} />
          <Route path="/uploads" element={<PrivateRoute><TeamUploads /></PrivateRoute>} />
          <Route path="/judge-dashboard" element={<RoleRoute allowedRoles={['JUDGE', 'HEAD_JUDGE']}><JudgeDashboard /></RoleRoute>} />
          <Route path="/head-judge-dashboard" element={<RoleRoute allowedRoles={['HEAD_JUDGE']}><HeadJudgeDashboard /></RoleRoute>} />
          <Route path="/users" element={<RoleRoute allowedRoles={['ADMIN']}><AdminUsers /></RoleRoute>} />
          <Route path="/judges" element={<RoleRoute allowedRoles={['ADMIN']}><JudgeManagement /></RoleRoute>} />
          <Route path="/audit-logs" element={<RoleRoute allowedRoles={['ADMIN', 'HEAD_JUDGE']}><AuditLogs /></RoleRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </div>
    </>
  )
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}
