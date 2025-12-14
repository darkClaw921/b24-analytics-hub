import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import { User } from '../../types'

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    is_admin: false
  })

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const response = await api.get<User[]>('/admin/users')
      setUsers(response.data)
    } catch (error) {
      console.error('Error loading users:', error)
    }
  }

  const createUser = async () => {
    try {
      await api.post('/admin/users', formData)
      setShowForm(false)
      setFormData({ username: '', email: '', password: '', is_admin: false })
      loadUsers()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Ошибка создания пользователя')
    }
  }

  const deleteUser = async (id: number) => {
    if (!confirm('Удалить пользователя?')) return
    try {
      await api.delete(`/admin/users/${id}`)
      loadUsers()
    } catch (error) {
      alert('Ошибка удаления пользователя')
    }
  }

  return (
    <div className="user-management">
      <h2>Управление пользователями</h2>
      
      <button className="btn btn-primary" onClick={() => setShowForm(true)}>
        Добавить пользователя
      </button>

      {showForm && (
        <div className="user-form">
          <input
            type="text"
            placeholder="Имя пользователя"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          />
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
          <input
            type="password"
            placeholder="Пароль"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          />
          <label>
            <input
              type="checkbox"
              checked={formData.is_admin}
              onChange={(e) => setFormData({ ...formData, is_admin: e.target.checked })}
            />
            Администратор
          </label>
          <button className="btn btn-primary" onClick={createUser}>Создать</button>
          <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Отмена</button>
        </div>
      )}

      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Имя пользователя</th>
            <th>Email</th>
            <th>Админ</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.id}</td>
              <td>{user.username}</td>
              <td>{user.email}</td>
              <td>{user.is_admin ? 'Да' : 'Нет'}</td>
              <td>
                <button className="btn btn-danger" onClick={() => deleteUser(user.id)}>
                  Удалить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

