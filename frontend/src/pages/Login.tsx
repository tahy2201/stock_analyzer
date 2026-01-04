import { App, Button, Form, Input } from 'antd'
import type { AxiosError } from 'axios'
import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface LoginFormData {
  login_id: string
  password: string
}

const Login = () => {
  const { notification } = App.useApp()
  const { isAuthenticated, isLoading, login } = useAuth()
  const [submitting, setSubmitting] = useState(false)
  const location = useLocation()
  const from = (location.state as { from?: string })?.from || '/'

  const handleSubmit = async (values: LoginFormData) => {
    setSubmitting(true)
    try {
      await login(values.login_id, values.password)
      notification.success({
        message: 'ログイン成功',
        description: 'ログインしました',
        placement: 'topRight',
      })
    } catch (error) {
      // Axiosエラーレスポンスから詳細メッセージを取得
      const axiosError = error as AxiosError<{ detail?: string }>
      const errorMessage =
        axiosError.response?.data?.detail ||
        axiosError.message ||
        'ログインに失敗しました。IDまたはパスワードを確認してください。'

      notification.error({
        message: 'ログイン失敗',
        description: errorMessage,
        placement: 'topRight',
        duration: 5,
      })
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

  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="w-full max-w-md p-8 bg-gray-800 rounded-lg shadow-xl">
        <h1 className="text-2xl font-bold text-white text-center mb-8">
          株式分析システム
        </h1>
        <Form layout="vertical" onFinish={handleSubmit} requiredMark={false}>
          <Form.Item
            label={<span className="text-gray-300">ログインID</span>}
            name="login_id"
            rules={[
              { required: true, message: 'ログインIDを入力してください' },
            ]}
          >
            <Input size="large" placeholder="ログインID" />
          </Form.Item>
          <Form.Item
            label={<span className="text-gray-300">パスワード</span>}
            name="password"
            rules={[
              { required: true, message: 'パスワードを入力してください' },
            ]}
          >
            <Input.Password size="large" placeholder="パスワード" />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              loading={submitting}
              className="w-full"
            >
              ログイン
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  )
}

export default Login
