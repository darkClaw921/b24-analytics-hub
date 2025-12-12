import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import UserManagement from './UserManagement'
import MCPServers from './MCPServers'
import ToolSettings from './ToolSettings'

export default function AdminPanel() {
  const navigate = useNavigate()

  return (
    <div className="admin-panel">
      <header className="admin-header">
        <h1>Админ-панель</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/')}>
          К чатам
        </button>
      </header>

      <nav className="admin-nav">
        <Link to="/admin/users" className="admin-nav-link">Пользователи</Link>
        <Link to="/admin/servers" className="admin-nav-link">MCP Серверы</Link>
        <Link to="/admin/tools" className="admin-nav-link">Инструменты</Link>
      </nav>

      <div className="admin-content">
        <Routes>
          <Route path="users" element={<UserManagement />} />
          <Route path="servers" element={<MCPServers />} />
          <Route path="tools" element={<ToolSettings />} />
          <Route path="*" element={<UserManagement />} />
        </Routes>
      </div>
    </div>
  )
}

