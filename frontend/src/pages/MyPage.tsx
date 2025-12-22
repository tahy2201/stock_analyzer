import { Button, Card, Descriptions, Form, Input, message, Modal } from 'antd'
import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { usersApi } from '../services/api'

const MyPage = () => {
  const { user, isLoading, refreshUser } = useAuth()
  const [displayNameModalOpen, setDisplayNameModalOpen] = useState(false)
  const [passwordModalOpen, setPasswordModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  if (isLoading) {
    return <div className="text-white">読み込み中...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  const handleDisplayNameUpdate = async (values: { display_name: string }) => {
    setSubmitting(true)
    try {
      await usersApi.updateProfile(values.display_name)
      message.success('表示名を更新しました')
      setDisplayNameModalOpen(false)
      await refreshUser()
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || '更新に失敗しました'
      message.error(errorMessage)
    } finally {
      setSubmitting(false)
    }
  }

  const handlePasswordChange = async (values: {
    current_password: string
    new_password: string
    new_password_confirm: string
  }) => {
    setSubmitting(true)
    try {
      await usersApi.changePassword(values.current_password, values.new_password)
      message.success('パスワードを変更しました')
      setPasswordModalOpen(false)
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || 'パスワード変更に失敗しました'
      message.error(errorMessage)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">マイページ</h1>

      <Card className="bg-gray-800 border-gray-700 mb-6">
        <Descriptions
          title={<span className="text-white">ユーザー情報</span>}
          column={1}
          bordered
        >
          <Descriptions.Item label="ログインID">{user.login_id}</Descriptions.Item>
          <Descriptions.Item label="表示名">
            <div className="flex items-center justify-between">
              <span>{user.display_name}</span>
              <Button size="small" onClick={() => setDisplayNameModalOpen(true)}>
                変更
              </Button>
            </div>
          </Descriptions.Item>
          <Descriptions.Item label="ロール">
            {user.role === 'admin' ? (
              <span className="text-blue-400">管理者</span>
            ) : (
              <span className="text-gray-400">一般ユーザー</span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="ステータス">
            {user.status === 'active' ? (
              <span className="text-green-400">有効</span>
            ) : (
              <span className="text-gray-400">{user.status}</span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="最終ログイン">
            {user.last_login_at ? new Date(user.last_login_at).toLocaleString('ja-JP') : '-'}
          </Descriptions.Item>
        </Descriptions>

        <div className="mt-4">
          <Button type="default" onClick={() => setPasswordModalOpen(true)}>
            パスワード変更
          </Button>
        </div>
      </Card>

      {/* 表示名変更モーダル */}
      <Modal
        title="表示名の変更"
        open={displayNameModalOpen}
        onCancel={() => setDisplayNameModalOpen(false)}
        footer={null}
      >
        <Form
          layout="vertical"
          onFinish={handleDisplayNameUpdate}
          initialValues={{ display_name: user.display_name }}
        >
          <Form.Item
            label="表示名"
            name="display_name"
            rules={[
              { required: true, message: '表示名を入力してください' },
              { max: 100, message: '100文字以内で入力してください' },
            ]}
          >
            <Input placeholder="表示名" />
          </Form.Item>
          <Form.Item>
            <div className="flex gap-2 justify-end">
              <Button onClick={() => setDisplayNameModalOpen(false)}>キャンセル</Button>
              <Button type="primary" htmlType="submit" loading={submitting}>
                更新
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>

      {/* パスワード変更モーダル */}
      <Modal
        title="パスワード変更"
        open={passwordModalOpen}
        onCancel={() => setPasswordModalOpen(false)}
        footer={null}
      >
        <Form layout="vertical" onFinish={handlePasswordChange}>
          <Form.Item
            label="現在のパスワード"
            name="current_password"
            rules={[{ required: true, message: '現在のパスワードを入力してください' }]}
          >
            <Input.Password placeholder="現在のパスワード" />
          </Form.Item>
          <Form.Item
            label="新しいパスワード"
            name="new_password"
            rules={[
              { required: true, message: '新しいパスワードを入力してください' },
              { min: 8, message: '8文字以上で入力してください' },
            ]}
          >
            <Input.Password placeholder="新しいパスワード（8文字以上）" />
          </Form.Item>
          <Form.Item
            label="新しいパスワード（確認）"
            name="new_password_confirm"
            dependencies={['new_password']}
            rules={[
              { required: true, message: 'パスワードを再入力してください' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('パスワードが一致しません'))
                },
              }),
            ]}
          >
            <Input.Password placeholder="新しいパスワード（確認）" />
          </Form.Item>
          <Form.Item>
            <div className="flex gap-2 justify-end">
              <Button onClick={() => setPasswordModalOpen(false)}>キャンセル</Button>
              <Button type="primary" htmlType="submit" loading={submitting}>
                変更
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MyPage
