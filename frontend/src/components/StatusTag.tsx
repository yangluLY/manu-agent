import { Tag } from 'antd'

export function StatusTag({
  value,
  map,
}: {
  value: string
  map: Record<string, { text: string; color: string }>
}) {
  const item = map[value] || { text: value || '未知', color: 'default' }
  return <Tag color={item.color}>{item.text}</Tag>
}
