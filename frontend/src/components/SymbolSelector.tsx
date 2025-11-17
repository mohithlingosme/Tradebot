import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchSymbols } from '../services/api'

interface SymbolSelectorProps {
  value: string
  onChange: (symbol: string) => void
  placeholder?: string
  onKeyPress?: (e: React.KeyboardEvent) => void
}

function SymbolSelector({ value, onChange, placeholder = "Select symbol...", onKeyPress }: SymbolSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  const { data: symbols = [], isLoading } = useQuery({
    queryKey: ['symbols'],
    queryFn: fetchSymbols,
  })

  const filteredSymbols = symbols.filter(symbol =>
    symbol.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleSelect = (symbol: string) => {
    onChange(symbol)
    setIsOpen(false)
    setSearchTerm('')
  }

  return (
    <div className="symbol-selector">
      <div className="selector-input" onClick={() => setIsOpen(!isOpen)}>
        <input
          type="text"
          value={value || searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value)
            onChange('')
          }}
          onKeyPress={onKeyPress}
          placeholder={placeholder}
          readOnly={!isOpen}
        />
        <span className="dropdown-arrow">{isOpen ? '▲' : '▼'}</span>
      </div>

      {isOpen && (
        <div className="dropdown-menu">
          {isLoading ? (
            <div className="loading">Loading symbols...</div>
          ) : (
            filteredSymbols.slice(0, 10).map(symbol => (
              <div
                key={symbol}
                className="dropdown-item"
                onClick={() => handleSelect(symbol)}
              >
                {symbol}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default SymbolSelector
