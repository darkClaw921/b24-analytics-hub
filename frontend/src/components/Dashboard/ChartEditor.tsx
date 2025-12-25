import { useState, useEffect } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { dashboardsService } from '../../services/dashboards'
import { Chart, ChartType } from '../../types'
import { ChartWrapper } from '../Charts/ChartWrapper'

interface ChartEditorProps {
  dashboardId: number
  chartId?: number
  onClose: () => void
  onSave: () => void
}

const DEFAULT_CODE_LINE = `import json

# Генерация данных для линейного чарта
labels = ["Jan", "Feb", "Mar", "Apr", "May"]
data = [100, 200, 150, 300, 250]

result = {
    "labels": labels,
    "datasets": [{
        "label": "Sales",
        "data": data,
        "backgroundColor": "#3b82f6"
    }]
}

print(json.dumps(result))`

const DEFAULT_CODE_BAR = `import json

# Генерация данных для столбчатого чарта
labels = ["Jan", "Feb", "Mar", "Apr", "May"]
data = [100, 200, 150, 300, 250]

result = {
    "labels": labels,
    "datasets": [{
        "label": "Sales",
        "data": data,
        "backgroundColor": "#3b82f6"
    }]
}

print(json.dumps(result))`

const DEFAULT_CODE_PIE = `import json

# Генерация данных для кругового чарта
labels = ["Jan", "Feb", "Mar", "Apr", "May"]
data = [100, 200, 150, 300, 250]

result = {
    "labels": labels,
    "datasets": [{
        "label": "Sales",
        "data": data,
        "backgroundColor": "#3b82f6"
    }]
}

print(json.dumps(result))`

const getDefaultCode = (chartType: ChartType): string => {
  switch (chartType) {
    case 'bar':
      return DEFAULT_CODE_BAR
    case 'pie':
      return DEFAULT_CODE_PIE
    case 'line':
    default:
      return DEFAULT_CODE_LINE
  }
}

export default function ChartEditor({ dashboardId, chartId, onClose, onSave }: ChartEditorProps) {
  const [title, setTitle] = useState('')
  const [chartType, setChartType] = useState<ChartType>('line')
  const [pythonCode, setPythonCode] = useState(getDefaultCode('line'))
  const [positionX, setPositionX] = useState(0)
  const [positionY, setPositionY] = useState(0)
  const [width, setWidth] = useState(400)
  const [height, setHeight] = useState(300)
  const [loading, setLoading] = useState(false)
  const [previewData, setPreviewData] = useState<any>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [isCodeManuallyEdited, setIsCodeManuallyEdited] = useState(false)

  useEffect(() => {
    if (chartId) {
      loadChart()
    }
  }, [chartId])

  // Обновляем код при изменении типа чарта, если код не был изменен вручную
  useEffect(() => {
    if (!isCodeManuallyEdited && !chartId) {
      setPythonCode(getDefaultCode(chartType))
      setPreviewData(null)
      setPreviewError(null)
    }
  }, [chartType, isCodeManuallyEdited, chartId])

  const loadChart = async () => {
    if (!chartId) return
    
    try {
      const dashboard = await dashboardsService.getDashboard(dashboardId)
      const chart = dashboard.charts.find(c => c.id === chartId)
      if (chart) {
        setTitle(chart.title)
        setChartType(chart.chart_type)
        setPythonCode(chart.python_code)
        setPositionX(chart.position_x)
        setPositionY(chart.position_y)
        setWidth(chart.width)
        setHeight(chart.height)
        setIsCodeManuallyEdited(true) // Код загружен из существующего чарта, не обновляем автоматически
      }
    } catch (error) {
      console.error('Error loading chart:', error)
    }
  }

  const handlePreview = async () => {
    setPreviewError(null)
    setLoading(true)
    
    try {
      // Создаем временный чарт для превью
      const tempChart = chartId 
        ? await dashboardsService.updateChart(chartId, { python_code: pythonCode })
        : await dashboardsService.createChart(dashboardId, {
            title: 'Preview',
            chart_type: chartType,
            python_code: pythonCode,
          })
      
      const result = await dashboardsService.executeChart(tempChart.id)
      
      if (result.success && result.data) {
        setPreviewData(result.data)
      } else {
        setPreviewError(result.error || 'Ошибка выполнения кода')
      }
      
      // Удаляем временный чарт если это был новый
      if (!chartId) {
        await dashboardsService.deleteChart(tempChart.id)
      }
    } catch (error: any) {
      setPreviewError(error.response?.data?.detail || 'Ошибка при выполнении кода')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!title.trim()) {
      alert('Введите название чарта')
      return
    }

    if (!pythonCode.trim()) {
      alert('Введите Python код')
      return
    }

    try {
      if (chartId) {
        await dashboardsService.updateChart(chartId, {
          title,
          chart_type: chartType,
          python_code: pythonCode,
          position_x: positionX,
          position_y: positionY,
          width,
          height,
        })
      } else {
        await dashboardsService.createChart(dashboardId, {
          title,
          chart_type: chartType,
          python_code: pythonCode,
          position_x: positionX,
          position_y: positionY,
          width,
          height,
        })
      }
      onSave()
    } catch (error) {
      console.error('Error saving chart:', error)
      alert('Ошибка при сохранении чарта')
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{chartId ? 'Редактировать чарт' : 'Создать чарт'}</h2>
          <button className="btn-icon" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>Название чарта</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Название чарта"
            />
          </div>

          <div className="form-group">
            <label>Тип чарта</label>
            <select 
              value={chartType} 
              onChange={(e) => {
                const newType = e.target.value as ChartType
                setChartType(newType)
                // Если код не был изменен вручную, обновляем его
                if (!isCodeManuallyEdited && !chartId) {
                  setPythonCode(getDefaultCode(newType))
                  setPreviewData(null)
                  setPreviewError(null)
                }
              }}
            >
              <option value="line">Линейный</option>
              <option value="bar">Столбчатый</option>
              <option value="pie">Круговой</option>
            </select>
          </div>

          <div className="form-group">
            <label>Python код</label>
            <div className="code-editor-wrapper">
              <CodeMirror
                value={pythonCode}
                onChange={(value) => {
                  setPythonCode(value)
                  setIsCodeManuallyEdited(true) // Отмечаем, что код был изменен вручную
                }}
                height="300px"
                extensions={[python()]}
                theme={oneDark}
                basicSetup={{
                  lineNumbers: true,
                  foldGutter: true,
                  dropCursor: false,
                  allowMultipleSelections: false,
                  indentOnInput: true,
                  bracketMatching: true,
                  closeBrackets: true,
                  autocompletion: true,
                  highlightSelectionMatches: true,
                }}
              />
            </div>
            <small>
              Код должен выводить JSON через print() или устанавливать переменную result.
              Формат: {"{"}"labels": ["Label1", "Label2"], "datasets": [{"{"}"label": "Data", "data": [1, 2], "backgroundColor": "#3b82f6"{"}"}]{"}"}
            </small>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Позиция X</label>
              <input
                type="number"
                value={positionX}
                onChange={(e) => setPositionX(parseInt(e.target.value) || 0)}
              />
            </div>
            <div className="form-group">
              <label>Позиция Y</label>
              <input
                type="number"
                value={positionY}
                onChange={(e) => setPositionY(parseInt(e.target.value) || 0)}
              />
            </div>
            <div className="form-group">
              <label>Ширина</label>
              <input
                type="number"
                value={width}
                onChange={(e) => setWidth(parseInt(e.target.value) || 400)}
              />
            </div>
            <div className="form-group">
              <label>Высота</label>
              <input
                type="number"
                value={height}
                onChange={(e) => setHeight(parseInt(e.target.value) || 300)}
              />
            </div>
          </div>

          <div className="form-actions">
            <button className="btn btn-secondary" onClick={handlePreview} disabled={loading}>
              {loading ? 'Выполнение...' : 'Превью'}
            </button>
          </div>

          {previewError && (
            <div className="error-message">
              <strong>Ошибка:</strong> {previewError}
            </div>
          )}

          {previewData && (
            <div className="preview-section">
              <h3>Превью</h3>
              <div style={{ width: '100%', height: '300px' }}>
                <ChartWrapper type={chartType} data={previewData} />
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Отмена
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            Сохранить
          </button>
        </div>
      </div>
    </div>
  )
}

