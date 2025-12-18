import { Routes, Route, NavLink, useNavigate, useLocation } from 'react-router-dom'
import UserManagement from './UserManagement'
import MCPServers from './MCPServers'
import ToolSettings from './ToolSettings'

export default function AdminPanel() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className="admin-panel">
      <header className="admin-header">
        <h1>Админ-панель</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/')}>
          К чатам
        </button>
      </header>

      <nav className="admin-nav">
        <NavLink 
          to="/admin/users" 
          className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
        >
          Пользователи
        </NavLink>
        <NavLink 
          to="/admin/servers" 
          className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
        >
          MCP Серверы
        </NavLink>
        <NavLink 
          to="/admin/tools" 
          className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
        >
          Инструменты
        </NavLink>
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

