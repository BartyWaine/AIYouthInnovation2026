import { useEffect, useState } from 'react'
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
