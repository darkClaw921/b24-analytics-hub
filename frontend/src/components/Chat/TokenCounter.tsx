interface TokenCounterProps {
  totalTokens: number
}

export default function TokenCounter({ totalTokens }: TokenCounterProps) {
  const maxTokens = 128000 // GPT-4 Turbo context window
  const percentage = (totalTokens / maxTokens) * 100

  return (
    <div className="token-counter">
      <div className="token-info">
        <span className="token-label">Токены:</span>
        <span className="token-value">{totalTokens.toLocaleString()} / {maxTokens.toLocaleString()}</span>
      </div>
      <div className="token-bar">
        <div 
          className="token-bar-fill"
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}

