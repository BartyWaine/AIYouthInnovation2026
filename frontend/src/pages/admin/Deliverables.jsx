import { useEffect, useState } from 'react'
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
                      <tr key={s.id} className="border-t"><td className="p-2">{s.id}</td><td className="p-2">{s.team_name || s.team_id}</td><td className="p-2">v{s.version}</td><td className="p-2"><span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">{s.status}</span></td></tr>
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
