import { useEffect, useState } from 'react'
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
