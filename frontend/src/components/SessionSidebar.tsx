import { useState } from 'react'
import { chatApi } from '../api'

interface Session {
  id: string
  preview: string
  created_at: string
}

interface SessionSidebarProps {
  sessions: Session[]
  currentSessionId: string | null
  onSessionSelect: (sessionId: string) => void
  onNewSession: () => void
  onSessionsReload: () => void
}

function SessionSidebar({ 
  sessions, 
  currentSessionId, 
  onSessionSelect, 
  onNewSession, 
  onSessionsReload 
}: SessionSidebarProps) {
  const [showSessions, setShowSessions] = useState(false)

  const deleteSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    
    if (!confirm('Are you sure you want to delete this conversation? This cannot be undone.')) {
      return
    }
    
    try {
      await chatApi.deleteSession(sessionId)
      
      if (currentSessionId === sessionId) {
        // Instead of window.location.reload(), clear current session and reload sessions
        onSessionSelect(null)
        onSessionsReload()
      } else {
        onSessionsReload()
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert('Failed to delete session. Please try again.')
    }
  }

  const handleNewSession = () => {
    onNewSession()
    setShowSessions(false)
  }

  const handleSessionSelect = (sessionId: string) => {
    onSessionSelect(sessionId)
    setShowSessions(false)
  }

  return (
    <div className="session-sidebar">
      <button
        className="sessions-toggle"
        onClick={() => setShowSessions(!showSessions)}
      >
        <svg className="sessions-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        Sessions
      </button>
      
      {showSessions && (
        <div className="sessions-dropdown">
          <div className="sessions-content">
            <button
              className="new-session-button"
              onClick={handleNewSession}
            >
              + New Conversation
            </button>
            
            {sessions.length === 0 ? (
              <p className="no-sessions">
                No previous conversations
              </p>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  className={`session-item ${currentSessionId === session.id ? 'active' : ''}`}
                  onClick={() => handleSessionSelect(session.id)}
                >
                  <div className="session-info">
                    <div className="session-preview">
                      {session.preview}
                    </div>
                    <div className="session-date">
                      {new Date(session.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <button
                    className="delete-session-button"
                    onClick={(e) => deleteSession(session.id, e)}
                    title="Delete conversation"
                  >
                    <svg className="delete-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default SessionSidebar