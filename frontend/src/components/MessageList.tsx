import { useEffect, useRef, useMemo } from 'react'
import MarkdownRenderer from './MarkdownRenderer'

interface Message {
  id?: string
  text: string
  type: 'user' | 'kyra' | 'error'
  category?: string
  sources?: string[]
  metadata?: {
    used_rag?: boolean
  }
}

interface MessageListProps {
  messages: Message[]
  loading: boolean
  onLinkClick: (url: string, title: string) => void
}

function MessageList({ messages, loading, onLinkClick }: MessageListProps) {
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const LoadingIndicator = () => (
    <div className="loading-dots">
      <div className="dot" style={{ animationDelay: '0ms' }}></div>
      <div className="dot" style={{ animationDelay: '150ms' }}></div>
      <div className="dot" style={{ animationDelay: '300ms' }}></div>
    </div>
  )

  const GreetingMessage = useMemo(() => (
    <div className="message-container kyra">
      <div className="message-content">
        <div className="message-header">
          <div className="avatar small">K</div>
          <span className="message-sender">Kyra</span>
        </div>
        <div className="message-bubble kyra">
          <p>Hey! How are you feeling today? 😊</p>
          <p>I'm here to help with any health questions you might have. What's on your mind?</p>
        </div>
      </div>
    </div>
  ), [])

  return (
    <div className="message-list">
      {/* Always show Kyra's greeting first */}
      {GreetingMessage}
      
      {/* Then show all the actual chat messages */}
      {messages.map((message, i) => (
        <div 
          key={message.id || i} 
          className={`message-container ${message.type}`}
        >
          <div className="message-content">
            {message.type !== 'user' && (
              <div className="message-header">
                <div className="avatar small">K</div>
                <span className="message-sender">
                  {message.type === 'error' ? 'Error' : 'Kyra'}
                </span>
              </div>
            )}
            <div className={`message-bubble ${message.type}`}>
              {message.type === 'kyra' ? (
                <div>
                  <MarkdownRenderer text={message.text} onLinkClick={onLinkClick} />
                  {message.sources && message.sources.length > 0 && (
                    <div className="sources-container">
                      <div className="sources-title">
                        {message.metadata?.used_rag ? 'NHS/Cancer Research Sources:' : 'General Medical Sources:'}
                      </div>
                      {message.sources.map((source, idx) => {
                        const isUrl = source.startsWith('http://') || source.startsWith('https://')
                        
                        if (isUrl) {
                          let displayText = source
                          try {
                            const url = new URL(source)
                            displayText = `${url.hostname}${url.pathname}`
                            if (displayText.length > 60) {
                              displayText = displayText.substring(0, 57) + '...'
                            }
                          } catch (e) {
                            displayText = source
                          }
                          
                          return (
                            <div key={idx} className="source-item">
                              <button
                                onClick={() => onLinkClick(source, displayText)}
                                className="source-link"
                              >
                                <svg className="source-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                                {displayText}
                              </button>
                            </div>
                          )
                        } else {
                          return (
                            <div key={idx} className="source-text">
                              • {source}
                            </div>
                          )
                        }
                      })}
                    </div>
                  )}
                </div>
              ) : (
                <p>{message.text}</p>
              )}
            </div>
          </div>
        </div>
      ))}
      
      {loading && (
        <div className="message-container kyra">
          <div className="message-content">
            <div className="message-header">
              <div className="avatar small">K</div>
              <span className="message-sender">Kyra</span>
            </div>
            <div className="message-bubble kyra">
              <LoadingIndicator />
            </div>
          </div>
        </div>
      )}
      
      <div ref={chatEndRef} />
    </div>
  )
}

export default MessageList