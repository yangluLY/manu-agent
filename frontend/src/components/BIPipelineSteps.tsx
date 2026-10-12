import { Card, Steps } from 'antd'

const stages = [
  'Schema Discovery',
  'Text-to-SQL',
  'SQL Safety',
  'SQL Executor',
  'Retry / Correction',
  'Data Analyst',
  'Chart Generator',
]

interface BIPipelineStepsProps {
  loading: boolean
  completed: boolean
  hasError: boolean
}

export function BIPipelineSteps({ loading, completed, hasError }: BIPipelineStepsProps) {
  return (
    <Card size="small" className="section-card" title="V3 BI 执行链路">
      <Steps
        size="small"
        responsive={false}
        current={loading ? 1 : completed ? stages.length : 0}
        status={hasError ? 'error' : loading ? 'process' : 'finish'}
        items={stages.map((title, index) => ({
          title: `V3.${index + 1}`,
          description: title,
        }))}
      />
    </Card>
  )
}
