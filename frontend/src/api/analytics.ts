import type { BIPipelineResult } from '../types/analytics'
import { http } from './client'

export const analyticsApi = {
  async query(question: string): Promise<BIPipelineResult> {
    const { data } = await http.post<BIPipelineResult>(
      '/api/v1/agent/bi/query',
      { question },
      { timeout: 180_000 },
    )
    return data
  },
}
