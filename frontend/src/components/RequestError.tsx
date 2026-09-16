import { Alert, Button } from 'antd'

export function RequestError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <Alert
      showIcon
      type="error"
      message="数据加载失败"
      description={message}
      action={
        <Button size="small" danger onClick={onRetry}>
          重试
        </Button>
      }
    />
  )
}
