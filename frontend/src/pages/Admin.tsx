import { App, Button, Card, Input, Modal, Popconfirm, Select, Space, Table, Tabs, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { adminApi } from '../services/api'
import type { Invite, User } from '../types/auth'

const { Text, Paragraph } = Typography

const Admin = () => {
  const { notification } = App.useApp()
  const { user, isLoading } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [inviteModalOpen, setInviteModalOpen] = useState(false)
  const [inviteRole, setInviteRole] = useState<'user' | 'admin'>('user')
  const [createdInvite, setCreatedInvite] = useState<Invite | null>(null)
  const [resetPasswordModalOpen, setResetPasswordModalOpen] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [newPassword, setNewPassword] = useState('')

  const fetchUsers = async () => {
    setLoadingUsers(true)
    try {
      const data = await adminApi.listUsers()
      setUsers(data)
    } catch {
      notification.error({ message: 'Failed to fetch users' })
    } finally {
      setLoadingUsers(false)
    }
  }

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchUsers()
    }
  }, [user])

  if (isLoading) {
    return <div className="text-white">Loading...</div>
  }

  if (!user || user.role !== 'admin') {
    return <Navigate to="/" replace />
  }

  const handleCreateInvite = async () => {
    try {
      const invite = await adminApi.createInvite({ role: inviteRole })
      setCreatedInvite(invite)
      notification.success({ message: 'Invite created' })
      fetchUsers() // 仮ユーザーが作成されるのでリフレッシュ
    } catch {
      notification.error({ message: 'Failed to create invite' })
    }
  }

  const handleDeleteUser = async (userId: number) => {
    try {
      await adminApi.deleteUser(userId)
      notification.success({ message: 'User deleted' })
      fetchUsers()
    } catch {
      notification.error({ message: 'Failed to delete user' })
    }
  }

  const handleResetPassword = async () => {
    if (!selectedUserId || !newPassword) return
    try {
      await adminApi.resetPassword(selectedUserId, newPassword)
      notification.success({ message: 'Password reset' })
      setResetPasswordModalOpen(false)
      setSelectedUserId(null)
      setNewPassword('')
    } catch {
      notification.error({ message: 'Failed to reset password' })
    }
  }

  const getInviteUrl = (token: string) => {
    return `${window.location.origin}/register?token=${token}`
  }

  const columns: ColumnsType<User> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Login ID',
      dataIndex: 'login_id',
      key: 'login_id',
    },
    {
      title: 'Display Name',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      width: 80,
      render: (role: string) => (
        <span className={role === 'admin' ? 'text-blue-400' : 'text-gray-400'}>
          {role}
        </span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <span
          className={
            status === 'active'
              ? 'text-green-400'
              : status === 'pending'
                ? 'text-yellow-400'
                : 'text-red-400'
          }
        >
          {status}
        </span>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            onClick={() => {
              setSelectedUserId(record.id)
              setResetPasswordModalOpen(true)
            }}
          >
            Reset PW
          </Button>
          {record.id !== user.id && (
            <Popconfirm
              title="Delete user?"
              description="This action cannot be undone."
              onConfirm={() => handleDeleteUser(record.id)}
              okText="Delete"
              cancelText="Cancel"
            >
              <Button size="small" danger>
                Delete
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Admin</h1>

      <Tabs
        defaultActiveKey="users"
        items={[
          {
            key: 'users',
            label: 'Users',
            children: (
              <Card className="bg-gray-800 border-gray-700">
                <div className="mb-4">
                  <Button type="primary" onClick={() => setInviteModalOpen(true)}>
                    Create Invite
                  </Button>
                </div>
                <Table
                  columns={columns}
                  dataSource={users}
                  rowKey="id"
                  loading={loadingUsers}
                  pagination={false}
                  className="dark-table"
                />
              </Card>
            ),
          },
        ]}
      />

      {/* Invite Modal */}
      <Modal
        title="Create Invite"
        open={inviteModalOpen}
        onCancel={() => {
          setInviteModalOpen(false)
          setCreatedInvite(null)
        }}
        footer={
          createdInvite
            ? [
                <Button
                  key="close"
                  onClick={() => {
                    setInviteModalOpen(false)
                    setCreatedInvite(null)
                  }}
                >
                  Close
                </Button>,
              ]
            : [
                <Button key="cancel" onClick={() => setInviteModalOpen(false)}>
                  Cancel
                </Button>,
                <Button key="create" type="primary" onClick={handleCreateInvite}>
                  Create
                </Button>,
              ]
        }
      >
        {createdInvite ? (
          <div>
            <Paragraph className="mb-2">
              <Text strong>Invite URL:</Text>
            </Paragraph>
            <Paragraph
              copyable={{ text: getInviteUrl(createdInvite.token) }}
              className="bg-gray-100 p-2 rounded break-all"
            >
              {getInviteUrl(createdInvite.token)}
            </Paragraph>
            <Paragraph className="mt-4 text-gray-500">
              Expires at: {new Date(createdInvite.expires_at).toLocaleString()}
            </Paragraph>
          </div>
        ) : (
          <div>
            <label className="block mb-2">Role:</label>
            <Select
              value={inviteRole}
              onChange={setInviteRole}
              className="w-full"
              options={[
                { value: 'user', label: 'User' },
                { value: 'admin', label: 'Admin' },
              ]}
            />
          </div>
        )}
      </Modal>

      {/* Reset Password Modal */}
      <Modal
        title="Reset Password"
        open={resetPasswordModalOpen}
        onCancel={() => {
          setResetPasswordModalOpen(false)
          setSelectedUserId(null)
          setNewPassword('')
        }}
        onOk={handleResetPassword}
        okText="Reset"
        okButtonProps={{ disabled: newPassword.length < 8 }}
      >
        <div>
          <label className="block mb-2">New Password (min 8 chars):</label>
          <Input.Password
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="New password"
          />
        </div>
      </Modal>
    </div>
  )
}

export default Admin
