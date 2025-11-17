import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import '../styles/AIAssistant.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface PromptTemplate {
  name: string
  prompt: string
  description: string
}

const PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    name: 'Market Analysis',
    prompt: 'Analyze the current market conditions for {symbol}. Provide key insights and trading signals.',
    description: 'Get AI-powered market analysis'
  },
  {
    name: 'Portfolio Advice',
    prompt: 'Review my portfolio and provide optimization advice: {portfolio_data}',
    description: 'Get portfolio optimization suggestions'
  },
  {
    name: 'Risk Assessment',
    prompt: 'Assess the risk level of investing in {symbol} given current market conditions.',
    description: 'Evaluate investment risk'
  },
  {
    name: 'Trading Strategy',
    prompt: 'Suggest a trading strategy for {symbol} based on technical indicators and market trends.',
    description: 'Get personalized trading strategy'
  }
]

export default function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Add welcome message
    setMessages([{
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI trading assistant. How can I help you today? You can ask me about market analysis, portfolio advice, or use one of the prompt templates below.',
      timestamp: new Date()
    }])
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.post(
        `${API_BASE_URL}/ai/prompt`,
        {
          prompt: userMessage.content,
          context: {},
          max_tokens: 500,
          temperature: 0.7
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response || 'I apologize, but I couldn\'t process your request.',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: error.response?.data?.detail || 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const useTemplate = (template: PromptTemplate) => {
    setSelectedTemplate(template)
    setInput(template.prompt)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const analyzeMarket = async (symbol: string) => {
    if (!symbol) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: `Analyze ${symbol}`,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.post(
        `${API_BASE_URL}/ai/analyze-market`,
        {
          symbol,
          market_data: {}
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.analysis || 'Analysis not available.',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Market analysis feature is not available. Please configure OpenAI API key.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ai-assistant">
      <div className="ai-header">
        <h1>AI Trading Assistant</h1>
        <p className="subtitle">Get AI-powered insights for your trading decisions</p>
      </div>

      <div className="prompt-templates">
        <h3>Quick Actions</h3>
        <div className="templates-grid">
          {PROMPT_TEMPLATES.map((template) => (
            <button
              key={template.name}
              className={`template-button ${selectedTemplate?.name === template.name ? 'selected' : ''}`}
              onClick={() => useTemplate(template)}
            >
              <div className="template-name">{template.name}</div>
              <div className="template-desc">{template.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="chat-container">
        <div className="messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-content">
                <div className="message-text">{message.content}</div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="loading-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <div className="quick-actions">
            <span>Quick analyze: </span>
            {['AAPL', 'GOOGL', 'MSFT', 'TSLA'].map((symbol) => (
              <button
                key={symbol}
                className="quick-button"
                onClick={() => analyzeMarket(symbol)}
                disabled={loading}
              >
                {symbol}
              </button>
            ))}
          </div>
          <div className="input-container">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about trading, markets, or your portfolio..."
              rows={3}
              className="message-input"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="send-button"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

