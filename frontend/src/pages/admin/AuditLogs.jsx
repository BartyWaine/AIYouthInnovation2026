import { useEffect, useState } from 'react'
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
