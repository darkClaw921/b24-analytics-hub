import { api } from './api'
import type { Dashboard, DashboardListItem, Chart, ChartType, ChartExecuteResponse } from '../types'

export const dashboardsService = {
  // Dashboard methods
  async getDashboards(): Promise<DashboardListItem[]> {
    const response = await api.get<DashboardListItem[]>('/dashboards')
    return response.data
  },

  async getDashboard(id: number): Promise<Dashboard> {
    const response = await api.get<Dashboard>(`/dashboards/${id}`)
    return response.data
  },

  async createDashboard(title: string, description?: string): Promise<Dashboard> {
    const response = await api.post<Dashboard>('/dashboards', {
      title,
      description,
    })
    return response.data
  },

  async updateDashboard(
    id: number,
    title?: string,
    description?: string
  ): Promise<Dashboard> {
    const response = await api.put<Dashboard>(`/dashboards/${id}`, {
      title,
      description,
    })
    return response.data
  },

  async deleteDashboard(id: number): Promise<void> {
    await api.delete(`/dashboards/${id}`)
  },

  // Chart methods
  async createChart(
    dashboardId: number,
    chartData: {
      title: string
      chart_type: ChartType
      python_code: string
      position_x?: number
      position_y?: number
      width?: number
      height?: number
      config?: Record<string, any>
    }
  ): Promise<Chart> {
    const response = await api.post<Chart>(`/dashboards/${dashboardId}/charts`, chartData)
    return response.data
  },

  async updateChart(
    chartId: number,
    chartData: {
      title?: string
      chart_type?: ChartType
      python_code?: string
      position_x?: number
      position_y?: number
      width?: number
      height?: number
      config?: Record<string, any>
    }
  ): Promise<Chart> {
    const response = await api.put<Chart>(`/dashboards/charts/${chartId}`, chartData)
    return response.data
  },

  async deleteChart(chartId: number): Promise<void> {
    await api.delete(`/dashboards/charts/${chartId}`)
  },

  async executeChart(chartId: number): Promise<ChartExecuteResponse> {
    const response = await api.post<ChartExecuteResponse>(`/dashboards/charts/${chartId}/execute`)
    return response.data
  },
}

