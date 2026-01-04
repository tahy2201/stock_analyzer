/**
 * API共通エラー型定義
 */

export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: Record<string, unknown>
}

export class ApiException extends Error {
  public readonly status?: number
  public readonly code?: string
  public readonly details?: Record<string, unknown>

  constructor(error: ApiError) {
    super(error.message)
    this.name = 'ApiException'
    this.status = error.status
    this.code = error.code
    this.details = error.details
  }

  static fromAxiosError(error: unknown): ApiException {
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as {
        response?: {
          status?: number
          data?: {
            detail?: string
            message?: string
            code?: string
          }
        }
        message?: string
      }

      const status = axiosError.response?.status
      const data = axiosError.response?.data
      const message =
        data?.detail || data?.message || axiosError.message || 'Unknown error'
      const code = data?.code

      return new ApiException({
        message,
        status,
        code,
        details: data as Record<string, unknown>,
      })
    }

    if (error instanceof Error) {
      return new ApiException({
        message: error.message,
      })
    }

    return new ApiException({
      message: 'Unknown error occurred',
    })
  }
}
