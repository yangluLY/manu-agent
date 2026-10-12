import { Alert, Card, Collapse, Input, List, Typography } from 'antd'
import { useState } from 'react'
import { analyticsApi, getErrorMessage } from '../api'
import { BIChart } from '../components/BIChart'
import { BIDataTable } from '../components/BIDataTable'
import { BIPipelineSteps } from '../components/BIPipelineSteps'
import { PageTitle } from '../components/PageTitle'
import type { BIPipelineResult } from '../types/analytics'

const defaultQuestion = '查询报警次数最多的5台设备'

export function BIPage() {
  const [question, setQuestion] = useState(defaultQuestion)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<BIPipelineResult>()

  const runQuery = async () => {
    const normalized = question.trim()
    if (!normalized || loading) return

    setLoading(true)
    setError('')
    try {
      setResult(await analyticsApi.query(normalized))
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bi-page">
      <PageTitle
        title="智能 BI"
        description="自然语言 → SQL → 数据 → 分析 → ECharts，可追溯每一次只读查询。"
      />

      <Card size="small" className="section-card" title="自然语言查询">
        <Input.Search
          size="large"
          value={question}
          loading={loading}
          enterButton="生成分析与图表"
          placeholder="例如：查询报警次数最多的5台设备"
          onChange={(event) => setQuestion(event.target.value)}
          onSearch={() => void runQuery()}
        />
      </Card>

      <BIPipelineSteps loading={loading} completed={Boolean(result)} hasError={Boolean(error)} />

      {error ? <Alert showIcon type="error" message="BI 查询失败" description={error} /> : null}

      {result ? (
        <>
          <BIChart result={result} />

          <Card size="small" className="section-card" title="数据分析">
            <Typography.Paragraph>{result.analysis.summary}</Typography.Paragraph>
            {result.analysis.key_findings.length ? (
              <List
                size="small"
                header={<strong>关键发现</strong>}
                dataSource={result.analysis.key_findings}
                renderItem={(item) => <List.Item>{item}</List.Item>}
              />
            ) : null}
            {result.analysis.recommendations.length ? (
              <List
                size="small"
                header={<strong>建议</strong>}
                dataSource={result.analysis.recommendations}
                renderItem={(item) => <List.Item>{item}</List.Item>}
              />
            ) : null}
            {result.analysis.limitations.map((item) => (
              <Alert key={item} showIcon type="warning" message={item} />
            ))}
          </Card>

          <Card size="small" className="section-card" title="查询数据">
            <BIDataTable data={result.data} />
          </Card>

          <Collapse
            className="section-card"
            items={[
              {
                key: 'sql',
                label: `查看 SQL（纠错 ${result.retry_count} 次）`,
                children: (
                  <Typography.Paragraph copyable className="bi-sql">
                    {result.sql}
                  </Typography.Paragraph>
                ),
              },
            ]}
          />
        </>
      ) : null}
    </div>
  )
}
