import { useEffect, useState } from 'react'
import { listUsers, createUser } from '../../api/admin'
import { resetPassword } from '../../api/auth'

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
         <thead className="bg-gray-50"><tr><th className="p-3">ID</th><th className="p-3">Email</th><th className="p-3">Role</th><th className="p-3">Actions</th></tr></thead>
         <tbody>{users.map(u => (
           <tr key={u.id} className="border-t hover:bg-gray-50">
             <td className="p-3">{u.id}</td>
             <td className="p-3">{u.email}</td>
             <td className="p-3"><span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">{u.role}</span></td>
             <td className="p-3">
               <button onClick={async () => {
                 if (window.confirm(`Reset password for ${u.email} to default123?`)) {
                   try {
                     await resetPassword(u.id)
                     alert(`Password reset for ${u.email}. New password: default123`)
                   } catch (err) {
                     alert(err.response?.data?.detail || 'Reset failed')
                   }
                 }
               }} className="text-red-600 hover:text-red-800 text-xs px-2 py-1 border border-red-200 rounded">Reset PW</button>
             </td>
           </tr>
         ))}</tbody>
        </table>
      </div>
    </div>
  )
}
