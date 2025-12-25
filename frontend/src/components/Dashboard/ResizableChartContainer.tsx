import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Chart } from '../../types'
import { dashboardsService } from '../../services/dashboards'

interface ResizableChartContainerProps {
  chart: Chart
  children: React.ReactNode
  onResize?: (width: number, height: number) => void
  onMove?: (positionX: number, positionY: number) => void
  gridCellSize?: number // Размер одной ячейки grid в пикселях
}

type ResizeDirection = 'n' | 's' | 'e' | 'w' | 'ne' | 'nw' | 'se' | 'sw'

const ResizableChartContainer: React.FC<ResizableChartContainerProps> = ({
  chart,
  children,
  onResize,
  onMove,
  gridCellSize = 100,
}) => {
  const [isResizing, setIsResizing] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [resizeDirection, setResizeDirection] = useState<ResizeDirection | null>(null)
  const [currentSize, setCurrentSize] = useState({ width: chart.width, height: chart.height })
  const [currentPosition, setCurrentPosition] = useState({ x: chart.position_x, y: chart.position_y })
  const containerRef = useRef<HTMLDivElement>(null)
  const gridContainerRef = useRef<HTMLDivElement | null>(null)
  const startPosRef = useRef({ 
    x: 0, 
    y: 0, 
    width: 0, 
    height: 0, 
    gridX: 0, 
    gridY: 0,
    startPositionX: 0,
    startPositionY: 0
  })
  const currentSizeRef = useRef({ width: chart.width, height: chart.height })
  const currentPositionRef = useRef({ x: chart.position_x, y: chart.position_y })
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const moveDebounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Синхронизируем размер и позицию при изменении chart извне
  // Но только если мы не изменяем размер в данный момент
  useEffect(() => {
    if (!isResizing) {
      const newSize = { width: chart.width, height: chart.height }
      const newPosition = { x: chart.position_x, y: chart.position_y }
      setCurrentSize(newSize)
      setCurrentPosition(newPosition)
      currentSizeRef.current = newSize
      currentPositionRef.current = newPosition
    }
  }, [chart.width, chart.height, chart.position_x, chart.position_y, isResizing])

  // Получаем ссылку на grid контейнер
  useEffect(() => {
    if (containerRef.current) {
      const gridContainer = containerRef.current.closest('.dashboard-charts-grid') as HTMLDivElement
      gridContainerRef.current = gridContainer
    }
  }, [])

  const handleDragStart = useCallback(
    (e: React.MouseEvent) => {
      // Проверяем, что клик не на кнопке или resize handle
      const target = e.target as HTMLElement
      if (
        target.closest('.btn-icon') ||
        target.closest('.btn-refresh') ||
        target.closest('.resize-handle') ||
        target.closest('.chart-actions') ||
        target.tagName === 'BUTTON'
      ) {
        return
      }

      e.preventDefault()
      e.stopPropagation()

      if (!containerRef.current || !gridContainerRef.current) return

      setIsDragging(true)
      document.body.style.cursor = 'move'
      document.body.style.userSelect = 'none'

      const containerRect = containerRef.current.getBoundingClientRect()
      const gridRect = gridContainerRef.current.getBoundingClientRect()

      // Вычисляем начальную позицию в grid координатах (100px ячейка + 20px gap)
      const cellWithGap = gridCellSize + 20
      const gridX = Math.round((containerRect.left - gridRect.left - 40) / cellWithGap) // 40px padding
      const gridY = Math.round((containerRect.top - gridRect.top - 20) / cellWithGap) // 20px padding

      startPosRef.current = {
        x: e.clientX,
        y: e.clientY,
        width: currentSize.width,
        height: currentSize.height,
        gridX: Math.max(0, gridX),
        gridY: Math.max(0, gridY),
      }
    },
    [currentSize, gridCellSize]
  )

  const handleDragMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current || !gridContainerRef.current) return

      const gridRect = gridContainerRef.current.getBoundingClientRect()
      const deltaX = e.clientX - startPosRef.current.x
      const deltaY = e.clientY - startPosRef.current.y

      // Вычисляем новую позицию в grid координатах (100px ячейка + 20px gap)
      const cellWithGap = gridCellSize + 20
      const startPixelX = startPosRef.current.gridX * cellWithGap + 40 // 40px padding
      const startPixelY = startPosRef.current.gridY * cellWithGap + 20 // 20px padding
      
      const newPixelX = startPixelX + deltaX
      const newPixelY = startPixelY + deltaY
      
      const newGridX = Math.max(0, Math.round((newPixelX - 40) / cellWithGap))
      const newGridY = Math.max(0, Math.round((newPixelY - 20) / cellWithGap))

      const newPosition = {
        x: newGridX * gridCellSize,
        y: newGridY * gridCellSize,
      }

      setCurrentPosition(newPosition)
      currentPositionRef.current = newPosition
    },
    [isDragging, gridCellSize]
  )

  const handleDragEnd = useCallback(async () => {
    if (!isDragging) return

    setIsDragging(false)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''

    // Отменяем предыдущий debounce
    if (moveDebounceTimerRef.current) {
      clearTimeout(moveDebounceTimerRef.current)
    }

    // Сохраняем изменения с небольшой задержкой
    const positionToSave = currentPositionRef.current
    moveDebounceTimerRef.current = setTimeout(async () => {
      try {
        await dashboardsService.updateChart(chart.id, {
          position_x: positionToSave.x,
          position_y: positionToSave.y,
        })
        onMove?.(positionToSave.x, positionToSave.y)
      } catch (error) {
        console.error('Error updating chart position:', error)
        // Откатываем изменения при ошибке
        const rollbackPosition = { x: chart.position_x, y: chart.position_y }
        setCurrentPosition(rollbackPosition)
        currentPositionRef.current = rollbackPosition
      }
    }, 300)
  }, [isDragging, chart.id, onMove, chart.position_x, chart.position_y])

  const handleMouseDown = useCallback(
    (e: React.MouseEvent, direction: ResizeDirection) => {
      e.preventDefault()
      e.stopPropagation()
      
      if (!containerRef.current) return

      setIsResizing(true)
      setResizeDirection(direction)
      
      const rect = containerRef.current.getBoundingClientRect()
      startPosRef.current = {
        ...startPosRef.current,
        x: e.clientX,
        y: e.clientY,
        width: currentSizeRef.current.width,
        height: currentSizeRef.current.height,
        startPositionX: currentPositionRef.current.x,
        startPositionY: currentPositionRef.current.y,
      }
    },
    []
  )

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isResizing || !resizeDirection || !containerRef.current) return

      const deltaX = e.clientX - startPosRef.current.x
      const deltaY = e.clientY - startPosRef.current.y

      // Используем начальные значения из startPosRef
      // Важно: всегда используем сохраненные начальные значения, чтобы не влиять на другие чарты
      const startWidth = startPosRef.current.width
      const startHeight = startPosRef.current.height
      const startPositionX = startPosRef.current.startPositionX !== undefined 
        ? startPosRef.current.startPositionX 
        : currentPositionRef.current.x
      const startPositionY = startPosRef.current.startPositionY !== undefined 
        ? startPosRef.current.startPositionY 
        : currentPositionRef.current.y

      let newWidth = startWidth
      let newHeight = startHeight
      let newPositionX = startPositionX
      let newPositionY = startPositionY

      // Вычисляем новый размер в зависимости от направления
      if (resizeDirection.includes('e')) {
        newWidth = Math.max(gridCellSize, startWidth + deltaX)
      }
      if (resizeDirection.includes('w')) {
        const widthChange = startWidth - deltaX
        if (widthChange >= gridCellSize) {
          newWidth = widthChange
          newPositionX = startPositionX + deltaX
        } else {
          newWidth = gridCellSize
          newPositionX = startPositionX + (startWidth - gridCellSize)
        }
      }
      if (resizeDirection.includes('s')) {
        // При изменении через нижний край только увеличиваем высоту, позицию не меняем
        newHeight = Math.max(gridCellSize, startHeight + deltaY)
      }
      if (resizeDirection.includes('n')) {
        // При изменении через верхний край уменьшаем высоту и перемещаем вверх
        // Важно: используем начальную позицию, чтобы не влиять на другие чарты
        const heightChange = startHeight - deltaY
        if (heightChange >= gridCellSize) {
          newHeight = heightChange
          // Вычисляем новую позицию: сдвигаем вверх на величину уменьшения высоты
          // deltaY положительный когда тянем вверх, поэтому добавляем его к позиции
          newPositionY = startPositionY + deltaY
        } else {
          // Минимальная высота - одна ячейка
          newHeight = gridCellSize
          // Позиция сдвигается на разницу между начальной высотой и минимальной
          newPositionY = startPositionY + (startHeight - gridCellSize)
        }
        // Убеждаемся, что позиция не становится отрицательной
        newPositionY = Math.max(0, newPositionY)
      }

      // Округляем до размера grid ячейки
      newWidth = Math.round(newWidth / gridCellSize) * gridCellSize
      newHeight = Math.round(newHeight / gridCellSize) * gridCellSize
      
      // Округляем позицию до размера grid ячейки
      newPositionX = Math.round(newPositionX / gridCellSize) * gridCellSize
      newPositionY = Math.round(newPositionY / gridCellSize) * gridCellSize

      const newSize = { width: Math.max(gridCellSize, newWidth), height: Math.max(gridCellSize, newHeight) }
      const newPosition = { x: Math.max(0, newPositionX), y: Math.max(0, newPositionY) }
      
      setCurrentSize(newSize)
      currentSizeRef.current = newSize
      
      // Обновляем позицию только если изменилась (для w и n направлений)
      if (resizeDirection.includes('w') || resizeDirection.includes('n')) {
        setCurrentPosition(newPosition)
        currentPositionRef.current = newPosition
      }
    },
    [isResizing, resizeDirection, gridCellSize]
  )

  const handleMouseUp = useCallback(async () => {
    if (!isResizing) return

    const direction = resizeDirection
    setIsResizing(false)
    setResizeDirection(null)

    // Отменяем предыдущий debounce
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Сохраняем изменения с небольшой задержкой
    const sizeToSave = currentSizeRef.current
    const positionToSave = currentPositionRef.current
    
    debounceTimerRef.current = setTimeout(async () => {
      try {
        const updateData: { width?: number; height?: number; position_x?: number; position_y?: number } = {
          width: sizeToSave.width,
          height: sizeToSave.height,
        }
        
        // Если изменяли размер через w или n, также обновляем позицию
        if (direction?.includes('w') || direction?.includes('n')) {
          updateData.position_x = positionToSave.x
          updateData.position_y = positionToSave.y
        }
        
        const updatedChart = await dashboardsService.updateChart(chart.id, updateData)
        
        // Обновляем локальное состояние на основе ответа сервера
        if (updatedChart) {
          const serverSize = { width: updatedChart.width, height: updatedChart.height }
          const serverPosition = { x: updatedChart.position_x, y: updatedChart.position_y }
          
          setCurrentSize(serverSize)
          currentSizeRef.current = serverSize
          
          if (direction?.includes('w') || direction?.includes('n')) {
            setCurrentPosition(serverPosition)
            currentPositionRef.current = serverPosition
          }
        }
        
        onResize?.(sizeToSave.width, sizeToSave.height)
        
        // Если позиция изменилась, вызываем onMove
        if (direction?.includes('w') || direction?.includes('n')) {
          onMove?.(positionToSave.x, positionToSave.y)
        }
      } catch (error) {
        console.error('Error updating chart size:', error)
        // Откатываем изменения при ошибке
        const rollbackSize = { width: chart.width, height: chart.height }
        const rollbackPosition = { x: chart.position_x, y: chart.position_y }
        setCurrentSize(rollbackSize)
        setCurrentPosition(rollbackPosition)
        currentSizeRef.current = rollbackSize
        currentPositionRef.current = rollbackPosition
      }
    }, 300)
  }, [isResizing, resizeDirection, chart.id, onResize, onMove, chart.width, chart.height, chart.position_x, chart.position_y])

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = getCursorForDirection(resizeDirection!)
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      if (isResizing) {
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
    }
  }, [isResizing, handleMouseMove, handleMouseUp, resizeDirection])

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleDragMove)
      document.addEventListener('mouseup', handleDragEnd)
    }

    return () => {
      document.removeEventListener('mousemove', handleDragMove)
      document.removeEventListener('mouseup', handleDragEnd)
    }
  }, [isDragging, handleDragMove, handleDragEnd])

  const getCursorForDirection = (direction: ResizeDirection): string => {
    const cursors: Record<ResizeDirection, string> = {
      n: 'n-resize',
      s: 's-resize',
      e: 'e-resize',
      w: 'w-resize',
      ne: 'ne-resize',
      nw: 'nw-resize',
      se: 'se-resize',
      sw: 'sw-resize',
    }
    return cursors[direction]
  }

  const renderResizeHandle = (direction: ResizeDirection, className: string) => (
    <div
      className={`resize-handle resize-handle-${direction} ${className}`}
      onMouseDown={(e) => handleMouseDown(e, direction)}
    />
  )

  const gridColumnSpan = Math.max(1, Math.ceil(currentSize.width / gridCellSize))
  const gridRowSpan = Math.max(1, Math.ceil(currentSize.height / gridCellSize))
  const gridColumnStart = Math.max(1, Math.floor(currentPosition.x / gridCellSize) + 1)
  const gridRowStart = Math.max(1, Math.floor(currentPosition.y / gridCellSize) + 1)

  // Клонируем children и добавляем обработчик drag на chart-header
  const childrenWithDrag = React.Children.map(children, (child) => {
    if (React.isValidElement(child)) {
      // Если это chart-header, добавляем обработчик drag
      if (child.props.className === 'chart-header') {
        return React.cloneElement(child as React.ReactElement, {
          onMouseDown: handleDragStart,
          style: { 
            ...child.props.style, 
            cursor: isDragging ? 'move' : 'grab',
            userSelect: 'none',
          },
        })
      }
    }
    return child
  })

  return (
    <div
      ref={containerRef}
      className={`chart-container resizable ${isDragging ? 'dragging' : ''}`}
      style={{
        gridColumn: `${gridColumnStart} / span ${gridColumnSpan}`,
        gridRow: `${gridRowStart} / span ${gridRowSpan}`,
        position: 'relative',
        opacity: isDragging ? 0.8 : 1,
        zIndex: isDragging ? 1000 : 1,
      }}
    >
      {childrenWithDrag}
      
      {/* Угловые handles */}
      {renderResizeHandle('nw', 'resize-handle-corner')}
      {renderResizeHandle('ne', 'resize-handle-corner')}
      {renderResizeHandle('sw', 'resize-handle-corner')}
      {renderResizeHandle('se', 'resize-handle-corner')}
      
      {/* Боковые handles */}
      {renderResizeHandle('n', 'resize-handle-edge')}
      {renderResizeHandle('s', 'resize-handle-edge')}
      {renderResizeHandle('e', 'resize-handle-edge')}
      {renderResizeHandle('w', 'resize-handle-edge')}
    </div>
  )
}

export default ResizableChartContainer

