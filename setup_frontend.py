import pathlib, os

BASE = pathlib.Path(r"D:\AIYouthInnovation2026\frontend")
SRC = BASE / "src"

dirs = [
    SRC / "api",
    SRC / "components",
    SRC / "pages" / "admin",
    SRC / "pages" / "team",
    SRC / "pages" / "judge",
    SRC / "context",
    BASE / "public",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# package.json
(BASE / "package.json").write_text("""{
  "name": "ai-youth-innovation-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "vite": "^5.0.0"
  }
}
""")

# vite.config.js
(BASE / "vite.config.js").write_text("""import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
""")

# tailwind.config.js
(BASE / "tailwind.config.js").write_text("""/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: { extend: {} },
  plugins: [],
}
""")

# postcss.config.js
(BASE / "postcss.config.js").write_text("""export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
""")

# index.html
(BASE / "index.html").write_text("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Youth Innovation 2026</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
""")

# src/index.css
(SRC / "index.css").write_text("""@tailwind base;
@tailwind components;
@tailwind utilities;
""")

# src/main.jsx
(SRC / "main.jsx").write_text("""import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
""")

# src/api/client.js
(SRC / "api" / "client.js").write_text("""import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
""")

# src/api/auth.js
(SRC / "api" / "auth.js").write_text("""import api from './client'

export async function login(email, password) {
  const params = new URLSearchParams()
  params.append('username', email)
  params.append('password', password)
  const res = await api.post('/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  localStorage.setItem('token', res.data.access_token)
  return res.data
}

export async function getMe() {
  const res = await api.get('/auth/me')
  return res.data
}

export function logout() {
  localStorage.removeItem('token')
}
""")

# src/api/competitions.js
(SRC / "api" / "competitions.js").write_text("""import api from './client'

export const listCompetitions = () => api.get('/competitions/').then(r => r.data)
export const getCompetition = (id) => api.get(`/competitions/${id}`).then(r => r.data)
export const createCompetition = (data) => api.post('/competitions/', data).then(r => r.data)
export const deleteCompetition = (id) => api.delete(`/competitions/${id}`).then(r => r.data)
export const getLeaderboard = (id) => api.get(`/competitions/${id}/leaderboard`).then(r => r.data)
""")

# src/api/teams.js
(SRC / "api" / "teams.js").write_text("""import api from './client'

export const listTeams = (compId) => api.get('/teams', { params: { competition_id: compId } }).then(r => r.data)
export const getTeam = (id) => api.get(`/teams/${id}`).then(r => r.data)
export const createTeam = (data) => api.post('/teams', data).then(r => r.data)
export const deleteTeam = (id) => api.delete(`/teams/${id}`).then(r => r.data)
export const addMember = (teamId, userId, isLeader) => api.post(`/teams/${teamId}/members`, null, { params: { user_id: userId, is_leader: isLeader } }).then(r => r.data)
""")

# src/context/AuthContext.jsx
(SRC / "context" / "AuthContext.jsx").write_text("""import { createContext, useContext, useState, useEffect } from 'react'
import { getMe, logout as apiLogout } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      getMe().then(setUser).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const logout = () => { apiLogout(); setUser(null) }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
""")

# src/components/Navbar.jsx
(SRC / "components" / "Navbar.jsx").write_text("""import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  return (
    <nav className="bg-indigo-600 text-white px-6 py-3 flex justify-between items-center">
      <Link to="/" className="text-xl font-bold">AI Youth Innovation 2026</Link>
      <div className="flex gap-4 items-center">
        {user ? (
          <>
            <Link to="/dashboard" className="hover:underline">Dashboard</Link>
            <Link to="/competitions" className="hover:underline">Competitions</Link>
            <span className="text-indigo-200 text-sm">{user.email} ({user.role})</span>
            <button onClick={logout} className="bg-indigo-800 px-3 py-1 rounded hover:bg-indigo-900">Logout</button>
          </>
        ) : (
          <Link to="/login" className="hover:underline">Login</Link>
        )}
      </div>
    </nav>
  )
}
""")

# src/pages/Login.jsx
(SRC / "pages" / "Login.jsx").write_text("""import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { getMe } from '../api/auth'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { setUser } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      const me = await getMe()
      setUser(me)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-indigo-600">Login</h2>
        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="w-full border p-3 rounded mb-4" required />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="w-full border p-3 rounded mb-4" required />
        <button type="submit" className="w-full bg-indigo-600 text-white py-3 rounded hover:bg-indigo-700 font-semibold">Sign In</button>
      </form>
    </div>
  )
}
""")

# src/pages/Dashboard.jsx
(SRC / "pages" / "Dashboard.jsx").write_text("""import { useAuth } from '../context/AuthContext'
import { useEffect, useState } from 'react'
import { listCompetitions } from '../api/competitions'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const { user } = useAuth()
  const [competitions, setCompetitions] = useState([])

  useEffect(() => { listCompetitions().then(setCompetitions).catch(() => {}) }, [])

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
      <p className="text-gray-600 mb-6">Welcome, <span className="font-semibold">{user?.email}</span> ({user?.role})</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white p-6 rounded-lg shadow"><p className="text-3xl font-bold text-indigo-600">{competitions.length}</p><p className="text-gray-500">Competitions</p></div>
        <div className="bg-white p-6 rounded-lg shadow"><p className="text-3xl font-bold text-green-600">{user?.role}</p><p className="text-gray-500">Your Role</p></div>
        <div className="bg-white p-6 rounded-lg shadow"><Link to="/competitions" className="text-indigo-600 hover:underline font-semibold">View Competitions &rarr;</Link></div>
      </div>
      <h2 className="text-xl font-semibold mb-4">Competitions</h2>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50"><tr><th className="p-3">ID</th><th className="p-3">Name</th><th className="p-3">Category</th><th className="p-3">Actions</th></tr></thead>
          <tbody>{competitions.map(c => (
            <tr key={c.id} className="border-t"><td className="p-3">{c.id}</td><td className="p-3 font-medium">{c.name}</td><td className="p-3">{c.category}</td><td className="p-3"><Link to={`/competitions/${c.id}`} className="text-indigo-600 hover:underline">Details</Link></td></tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
""")

# src/pages/Competitions.jsx
(SRC / "pages" / "Competitions.jsx").write_text("""import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getCompetition, getLeaderboard } from '../api/competitions'

export function CompetitionDetail() {
  const { id } = useParams()
  const [comp, setComp] = useState(null)
  const [board, setBoard] = useState([])

  useEffect(() => {
    getCompetition(id).then(setComp)
    getLeaderboard(id).then(setBoard).catch(() => {})
  }, [id])

  if (!comp) return <div className="p-6">Loading...</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Link to="/dashboard" className="text-indigo-600 hover:underline">&larr; Back</Link>
      <h1 className="text-3xl font-bold mt-4 mb-2">{comp.name}</h1>
      <p className="text-gray-500 mb-6">{comp.category}</p>
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg shadow"><p className="text-2xl font-bold">{comp.teams_count}</p><p className="text-gray-500">Teams</p></div>
        <div className="bg-white p-4 rounded-lg shadow"><p className="text-2xl font-bold">{comp.deliverables_count}</p><p className="text-gray-500">Deliverables</p></div>
      </div>
      <h2 className="text-xl font-semibold mb-4">Leaderboard</h2>
      {board.length === 0 ? <p className="text-gray-400">No scores yet</p> : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50"><tr><th className="p-3">Rank</th><th className="p-3">Team</th><th className="p-3">Score</th></tr></thead>
            <tbody>{board.map(b => (
              <tr key={b.team_id} className="border-t"><td className="p-3 font-bold">{b.rank}</td><td className="p-3">{b.team_name}</td><td className="p-3">{b.total_score}</td></tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  )
}
""")

# src/App.jsx
(SRC / "App.jsx").write_text("""import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import { CompetitionDetail } from './pages/Competitions'

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
        <Route path="/competitions/:id" element={<PrivateRoute><CompetitionDetail /></PrivateRoute>} />
        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </>
  )
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}
""")

print("Frontend scaffolded at D:\\AIYouthInnovation2026\\frontend")
print("Files created: package.json, vite.config.js, tailwind, App, Login, Dashboard, Competitions, API clients, AuthContext, Navbar")