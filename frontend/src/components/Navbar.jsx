import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { changePassword } from '../api/auth'

export default function Navbar() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const isTeamMember = user?.role === 'TEAM_MEMBER' || user?.role === 'TEAM_LEADER'
  const isJudge = user?.role === 'JUDGE'

  return (
    <nav className="bg-indigo-600 text-white px-6 py-3 flex justify-between items-center shadow-lg min-h-[72px]">
      <div className="flex items-center gap-4">
        <img src="/STI-Myanmar-College-Logo.jpg" alt="STI Logo" className="h-16 w-auto object-contain" />
        <Link to="/" className="text-xl font-bold tracking-tight">Myanmar Youth AI Innovation Competition 2026</Link>
      </div>
      <div className="flex gap-3 items-center text-sm">
        {user ? (
          <>
            <Link to="/dashboard" className="hover:text-indigo-200 px-2 py-1">Dashboard</Link>
            {isAdmin && <Link to="/competitions" className="hover:text-indigo-200 px-2 py-1">Competitions</Link>}
            {isAdmin && <Link to="/teams" className="hover:text-indigo-200 px-2 py-1">Teams</Link>}
            {isTeamMember && <Link to="/uploads" className="hover:text-indigo-200 px-2 py-1">My Uploads</Link>}
             {isAdmin && <Link to="/judges" className="hover:text-indigo-200 px-2 py-1">Judges</Link>}
             {isJudge && <Link to="/judge-dashboard" className="hover:text-indigo-200 px-2 py-1">Judge Dashboard</Link>}
            {isAdmin && <Link to="/users" className="hover:text-indigo-200 px-2 py-1">Users</Link>}
            {isAdmin && <Link to="/audit-logs" className="hover:text-indigo-200 px-2 py-1">Logs</Link>}
            <span className="text-indigo-200 ml-2">{user.email}</span>
            <button onClick={async () => {
              const current = prompt('Enter current password:')
              if (!current) return
              const newPass = prompt('Enter new password (min 6 chars):')
              if (!newPass || newPass.length < 6) {
                if (newPass) alert('Password must be at least 6 characters')
                return
              }
              try {
                await changePassword(current, newPass)
                alert('Password changed successfully')
              } catch (err) {
                alert(err.response?.data?.detail || 'Failed to change password')
              }
            }} className="text-indigo-200 hover:text-indigo-100 px-2 py-1 text-sm border border-indigo-400 rounded">Change PW</button>
            <button onClick={logout} className="bg-indigo-800 px-3 py-1 rounded hover:bg-indigo-900 ml-1">Logout</button>
          </>
        ) : (
          <Link to="/login" className="hover:text-indigo-200">Login</Link>
        )}
      </div>
    </nav>
  )
}
