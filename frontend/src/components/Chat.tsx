import { useState, useEffect } from 'react'
import { chatApi } from '../api'
import SessionSidebar from './SessionSidebar'
import MessageList from './MessageList'
import SourceModal from './SourceModal'

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

interface Session {
  id: string
  preview: string
  created_at: string
}

interface ChatProps {
  onLogout: () => void
  token: string
}

function Chat({ onLogout, token }: ChatProps) {
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [location, setLocation] = useState("")
  const [loading, setLoading] = useState(false)
  const [loadingSession, setLoadingSession] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [showModal, setShowModal] = useState(false)
  const [modalUrl, setModalUrl] = useState("")
  const [modalTitle, setModalTitle] = useState("")
  // Category filter state removed

  // Load sessions only after login (when token is present)
  useEffect(() => {
    if (!token) return;
    loadSessionsAndLatest();
    // loadCategories removed
  }, [token])

  // loadCategories function removed

  const loadSessionsAndLatest = async () => {
    try {
      const data = await chatApi.getSessions()
      console.log(`[DEBUG] Loaded ${data.length} sessions`)
      setSessions(data)
      
      // Auto-load the most recent session if it exists
      if (data.length > 0 && !currentSessionId) {
        console.log(`[DEBUG] Auto-loading most recent session: ${data[0].id}`)
        await loadSessionMessages(data[0].id)
      }
    } catch (error) {
      console.error("Failed to load sessions:", error)
    }
  }

  // Change loadSessionMessages to accept string | null
  const loadSessionMessages = async (sessionId: string | null) => {
    if (!sessionId) {
      setCurrentSessionId(null)
      setMessages([])
      return
    }
    setLoadingSession(true)
    try {
      const apiMessages = await chatApi.getSessionMessages(sessionId)
      
      // Convert API messages to log format
      const convertedMessages: Message[] = apiMessages.map((msg: any) => ({
        text: msg.content,
        type: msg.role === 'user' ? 'user' : 'kyra',
        id: msg.id,
        category: msg.category,
        sources: msg.sources,
        metadata: msg.response_metadata
      }))
      
      setMessages(convertedMessages)
      setCurrentSessionId(sessionId)
    } catch (error) {
      console.error("Failed to load session messages:", error)
      setMessages([{text: "Failed to load conversation history.", type: 'error'}])
    } finally {
      setLoadingSession(false)
    }
  }

  const sendMessage = async () => {
    if (!message.trim()) return
    
    const userMessage = message
    setMessage("")
    setLoading(true)
    
    // Add user message immediately
    setMessages((prev) => [...prev, {text: userMessage, type: 'user'}])
    
    console.log(`[DEBUG] Sending message with session_id: ${currentSessionId}`)
    
    try {
      const data = await chatApi.sendMessage(userMessage, location, currentSessionId || undefined)
      
      console.log(`[DEBUG] Response session_id: ${data.session_id}`)
      
      // Update current session ID if it was a new conversation
      if (!currentSessionId) {
        console.log(`[DEBUG] Setting new session_id: ${data.session_id}`)
        setCurrentSessionId(data.session_id)
      }
      
      // Reload sessions to update previews
      const sessionsData = await chatApi.getSessions()
      setSessions(sessionsData)
      
      // Replace the entire message list with the conversation history from the API
      const convertedMessages: Message[] = data.messages.map((msg: any) => ({
        text: msg.content,
        type: msg.role === 'user' ? 'user' : 'kyra',
        id: msg.id,
        category: msg.category,
        sources: msg.sources,
        metadata: msg.response_metadata
      }))
      
      setMessages(convertedMessages)
      
    } catch (error: any) {
      setMessages((prev) => [...prev, {
        text: error.response?.data?.message || "Failed to send message", 
        type: 'error'
      }])
    } finally {
      setLoading(false)
    }
  }

  const startNewSession = () => {
    setCurrentSessionId(null)
    setMessages([])
  }

  const openModal = (url: string, title: string) => {
    setModalUrl(url)
    setModalTitle(title)
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setModalUrl("")
    setModalTitle("")
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) {
      sendMessage()
    }
  }

  // Remove filteredMessages logic, just use messages directly

  if (loadingSession) {
    return (
      <div className="chat-container">
        <div className="loading-session">
          <div className="loading-dots">
            <div className="dot" style={{ animationDelay: '0ms' }}></div>
            <div className="dot" style={{ animationDelay: '150ms' }}></div>
            <div className="dot" style={{ animationDelay: '300ms' }}></div>
          </div>
          <p>Loading conversation...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-left">
            <div className="avatar">K</div>
            <div>
              <h1 className="chat-title">Kyra</h1>
              <p className="chat-subtitle">
                {currentSessionId ? `Session #${currentSessionId}` : 'Health Assistant'}
              </p>
            </div>
          </div>
          <div className="header-right">
            <SessionSidebar 
              sessions={sessions}
              currentSessionId={currentSessionId}
              onSessionSelect={loadSessionMessages}
              onNewSession={startNewSession}
              onSessionsReload={loadSessionsAndLatest}
            />
            <button className="logout-button" onClick={onLogout}>
              Logout
            </button>
          </div>
        </div>

        <div className="chat-area">
          {/* Category filter UI removed */}
          <MessageList 
            messages={messages}
            loading={loading}
            onLinkClick={openModal}
          />
        </div>

        <div className="input-area">
          <div className="input-row">
            <input 
              className="message-input"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your health question..."
              disabled={loading}
            />
            <button 
              className={`send-button ${loading || !message.trim() ? 'disabled' : ''}`}
              onClick={sendMessage}
              disabled={loading || !message.trim()}
            >
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <SourceModal 
        isOpen={showModal}
        url={modalUrl}
        title={modalTitle}
        messages={messages}
        currentSessionId={currentSessionId}
        onClose={closeModal}
        onLinkClick={openModal}
      />
    </>
  )
}

export default Chat