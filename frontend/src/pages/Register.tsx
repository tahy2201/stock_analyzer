import { Button, Form, Input, message, Result } from 'antd'
import { useState } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { authApi } from '../services/api'

interface RegisterFormData {
  login_id: string
  password: string
  password_confirm: string
  display_name: string
}

const Register = () => {
  const { isAuthenticated, isLoading, refreshUser } = useAuth()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [submitting, setSubmitting] = useState(false)
  const [registered, setRegistered] = useState(false)

  const handleSubmit = async (values: RegisterFormData) => {
    if (!token) return
    setSubmitting(true)
    try {
      await authApi.register({
        token,
        login_id: values.login_id,
        password: values.password,
        display_name: values.display_name || undefined,
      })
      message.success('登録が完了しました')
      setRegistered(true)
      await refreshUser()
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message || '登録に失敗しました')
      } else {
        message.error('登録に失敗しました')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-white">読み込み中...</div>
      </div>
    )
  }

  if (registered || isAuthenticated) {
    return <Navigate to="/" replace />
  }

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <Result
          status="error"
          title="招待トークンがありません"
          subTitle="招待リンクから再度アクセスしてください"
        />
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="w-full max-w-md p-8 bg-gray-800 rounded-lg shadow-xl">
        <h1 className="text-2xl font-bold text-white text-center mb-2">
          株式分析システム
        </h1>
        <p className="text-gray-400 text-center mb-8">新規ユーザー登録</p>
        <Form
          layout="vertical"
          onFinish={handleSubmit}
          requiredMark={false}
        >
          <Form.Item
            label={<span className="text-gray-300">ログインID</span>}
            name="login_id"
            rules={[
              { required: true, message: 'ログインIDを入力してください' },
              { min: 3, message: '3文字以上で入力してください' },
              { max: 50, message: '50文字以内で入力してください' },
            ]}
          >
            <Input size="large" placeholder="ログインID" />
          </Form.Item>
          <Form.Item
            label={<span className="text-gray-300">表示名</span>}
            name="display_name"
            rules={[{ max: 100, message: '100文字以内で入力してください' }]}
          >
            <Input size="large" placeholder="表示名（空欄の場合はログインIDが使用されます）" />
          </Form.Item>
          <Form.Item
            label={<span className="text-gray-300">パスワード</span>}
            name="password"
            rules={[
              { required: true, message: 'パスワードを入力してください' },
              { min: 8, message: '8文字以上で入力してください' },
            ]}
          >
            <Input.Password size="large" placeholder="パスワード（8文字以上）" />
          </Form.Item>
          <Form.Item
            label={<span className="text-gray-300">パスワード確認</span>}
            name="password_confirm"
            dependencies={['password']}
            rules={[
              { required: true, message: 'パスワードを再入力してください' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('パスワードが一致しません'))
                },
              }),
            ]}
          >
            <Input.Password size="large" placeholder="パスワード確認" />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              loading={submitting}
              className="w-full"
            >
              登録
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  )
}

export default Register
