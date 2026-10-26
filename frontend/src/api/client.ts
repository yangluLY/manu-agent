
import axios, {
  AxiosError,
  type InternalAxiosRequestConfig,
} from 'axios'

export interface ApiErrorBody {
  detail?:
    | string
    | Array<{
        loc?: Array<string | number>
        msg?: string
      }>
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 12_000,
  headers: {
    Accept: 'application/json',
  },
})

export const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL || ''
).replace(/\/$/, '')

// JWT 获取函数，由 AuthProvider 在运行时注入
type AccessTokenGetter = () => string | null

let accessTokenGetter: AccessTokenGetter = () => null

export function setAccessTokenGetter(
  getter: AccessTokenGetter,
) {
  accessTokenGetter = getter
}

// 每个普通 Axios API 请求自动携带 JWT
http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = accessTokenGetter()

    if (token) {
      config.headers.set(
        'Authorization',
        `Bearer ${token}`,
      )
    }

    return config
  },
)

// 401 统一通知 React 清理登录状态
type UnauthorizedHandler = () => void

let unauthorizedHandler: UnauthorizedHandler | null = null

export function setUnauthorizedHandler(
  handler: UnauthorizedHandler | null,
) {
  unauthorizedHandler = handler
}

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const requestUrl = error.config?.url || ''

      const isLoginRequest =
        requestUrl.endsWith('/auth/login')

      if (
        error.response?.status === 401 &&
        !isLoginRequest
      ) {
        unauthorizedHandler?.()
      }
    }

    return Promise.reject(error)
  },
)

export function getErrorMessage(
  error: unknown,
): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const axiosError = error as AxiosError<ApiErrorBody>
    const detail = axiosError.response?.data?.detail

    if (typeof detail === 'string') {
      return detail
    }

    if (Array.isArray(detail)) {
      return detail
        .map(
          (item) =>
            `${item.loc?.slice(1).join('.') || '请求参数'}：${
              item.msg || '格式错误'
            }`,
        )
        .join('；')
    }

    if (axiosError.code === 'ECONNABORTED') {
      return '请求超时，请检查 FastAPI 服务状态'
    }

    if (!axiosError.response) {
      return '无法连接 FastAPI，请确认后端已在 8000 端口启动'
    }

    return `请求失败（HTTP ${axiosError.response.status}）`
  }

  return error instanceof Error
    ? error.message
    : '发生未知错误'
}
