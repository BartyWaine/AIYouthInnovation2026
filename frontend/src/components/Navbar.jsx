import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { changePassword } from '../api/auth'

export default function Navbar() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const isTeamMember = user?.role === 'TEAM_MEMBER' || user?.role === 'TEAM_LEADER'
  const isJudge = user?.role === 'JUDGE' || user?.role === 'HEAD_JUDGE'
  const isHeadJudge = user?.role === 'HEAD_JUDGE'

  const [showPwForm, setShowPwForm] = useState(false)
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [pwMsg, setPwMsg] = useState('')

  const handlePwChange = async (e) => {
    e.preventDefault()
    if (newPw.length < 6) {
      setPwMsg('Password must be at least 6 characters')
      return
    }
    try {
      await changePassword(currentPw, newPw)
      setPwMsg('Password changed successfully')
      setCurrentPw('')
      setNewPw('')
      setShowPwForm(false)
    } catch (err) {
      setPwMsg(err.response?.data?.detail || 'Failed to change password')
    }
  }

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
             {isHeadJudge && <Link to="/head-judge-dashboard" className="hover:text-indigo-200 px-2 py-1 font-semibold">Head Judge</Link>}
            {isAdmin && <Link to="/users" className="hover:text-indigo-200 px-2 py-1">Users</Link>}
            {isAdmin && <Link to="/audit-logs" className="hover:text-indigo-200 px-2 py-1">Logs</Link>}
            <span className="text-indigo-200 ml-2">{user.email}</span>
            {!showPwForm ? (
              <button onClick={() => setShowPwForm(true)} className="text-indigo-200 hover:text-indigo-100 px-2 py-1 text-sm border border-indigo-400 rounded">Change PW</button>
            ) : (
              <form onSubmit={handlePwChange} className="flex flex-col gap-1 bg-indigo-800 p-2 rounded absolute right-6 top-[72px] shadow-lg z-50">
                {pwMsg && <div className="text-xs text-yellow-300">{pwMsg}</div>}
                <input type="password" placeholder="Current password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} className="text-black text-xs px-2 py-1 rounded" required />
                <input type="password" placeholder="New password (min 6 chars)" value={newPw} onChange={e => setNewPw(e.target.value)} className="text-black text-xs px-2 py-1 rounded" required />
                <div className="flex gap-1">
                  <button type="submit" className="bg-indigo-600 text-white text-xs px-2 py-1 rounded hover:bg-indigo-500">Save</button>
                  <button type="button" onClick={() => { setShowPwForm(false); setPwMsg(''); setCurrentPw(''); setNewPw('') }} className="bg-gray-600 text-white text-xs px-2 py-1 rounded hover:bg-gray-500">Cancel</button>
                </div>
              </form>
            )}
            <button onClick={logout} className="bg-indigo-800 px-3 py-1 rounded hover:bg-indigo-900 ml-1">Logout</button>
          </>
        ) : (
          <Link to="/login" className="hover:text-indigo-200">Login</Link>
        )}
      </div>
    </nav>
  )
}
