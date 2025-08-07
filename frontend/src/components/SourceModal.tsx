import MessageList from './MessageList'

interface Message {
  id?: string
  text: string
  type: 'user' | 'kyra' | 'error'
  sources?: string[]
  metadata?: {
    used_rag?: boolean
  }
}

interface SourceModalProps {
  isOpen: boolean
  url: string
  title: string
  messages: Message[]
  currentSessionId: string | null
  onClose: () => void
  onLinkClick: (url: string, title: string) => void
}

function SourceModal({ 
  isOpen, 
  url, 
  title, 
  messages, 
  currentSessionId, 
  onClose, 
  onLinkClick 
}: SourceModalProps) {
  if (!isOpen) return null

  // Pre-detect commonly blocked domains
  const blockedDomains = [
    'nhs.uk', 
    'mayoclinic.org', 
    'webmd.com',
    'healthline.com',
    'medicalnewstoday.com',
    'facebook.com',
    'twitter.com',
    'youtube.com'
  ]
  
  const isLikelyBlocked = blockedDomains.some(domain => {
    try {
      const urlHost = new URL(url).hostname.replace('www.', '')
      const matches = urlHost.includes(domain.replace('www.', ''))
      if (matches) {
        console.log(`Detected blocked domain: ${domain} in ${urlHost}`)
      }
      return matches
    } catch {
      const matches = url.includes(domain)
      if (matches) {
        console.log(`Detected blocked domain: ${domain} in ${url}`)
      }
      return matches
    }
  })

  console.log(`URL ${url} - isLikelyBlocked: ${isLikelyBlocked}`)

  const cleanTitle = () => {
    if (!title || title === url) {
      try {
        const urlObj = new URL(url)
        const hostname = urlObj.hostname.replace('www.', '')
        const pathSegments = urlObj.pathname.split('/').filter(Boolean)
        
        if (hostname.includes('nhs.uk')) {
          return pathSegments.length > 0 ? 
            pathSegments[pathSegments.length - 1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
            'NHS Information'
        } else if (hostname.includes('mayoclinic.org')) {
          return pathSegments.length > 0 ? 
            pathSegments[pathSegments.length - 1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
            'Mayo Clinic Information'
        } else {
          return hostname
        }
      } catch (e) {
        return 'Medical Information'
      }
    }
    return title
  }

  const recentMessages = messages.slice(-3)

  return (
    <div className="modal-overlay">
      {/* Chat side - compressed */}
      <div className="modal-chat-side">
        <div className="modal-chat-container">
          <div className="modal-chat-header">
            <div className="chat-header-left">
              <div className="avatar">K</div>
              <div>
                <h1 className="chat-title">Kyra</h1>
                <p className="chat-subtitle">
                  {currentSessionId ? `Session #${currentSessionId}` : 'Health Assistant'}
                </p>
              </div>
            </div>
            <button className="modal-close-button" onClick={onClose}>
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div className="modal-chat-content">
            {recentMessages.map((message, i) => (
              <div key={message.id || i} className={`modal-message ${message.type}`}>
                <div className="modal-message-content">
                  {message.type !== 'user' && (
                    <div className="modal-message-header">
                      <div className="avatar small">K</div>
                      <span className="modal-message-sender">Kyra</span>
                    </div>
                  )}
                  <div className={`modal-message-bubble ${message.type}`}>
                    {message.type === 'kyra' ? (
                      <div>{message.text.substring(0, 300)}{message.text.length > 300 ? '...' : ''}</div>
                    ) : (
                      <p>{message.text}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {messages.length > 3 && (
              <div className="more-messages-indicator">
                ... and {messages.length - 3} more messages
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Source content side */}
      <div className="modal-source-side">
        {/* Header with clean title */}
        <div className="modal-source-header">
          <div>
            <h3 className="modal-source-title">
              {cleanTitle()}
            </h3>
            <p className="modal-source-url">
              {new URL(url).hostname}
            </p>
          </div>
          <button className="modal-close-button" onClick={onClose}>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Content area with fallback */}
        <div className="modal-iframe-container">
          {isLikelyBlocked ? (
            // Skip iframe for known blocked sites
            <div className="iframe-fallback" style={{ display: 'flex' }}>
              <div className="fallback-icon">🔒</div>
              <h3 className="fallback-title">Content Blocked</h3>
              <p className="fallback-text">This site prevents embedding for security reasons.</p>
              <button
                onClick={() => window.open(url, '_blank')}
                className="fallback-button"
              >
                Open in New Tab
              </button>
            </div>
          ) : (
            <>
              <iframe
                src={url}
                className="modal-iframe"
                title={cleanTitle()}
                sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-top-navigation"
                onLoad={(e) => {
                  // Better error detection
                  const iframe = e.target as HTMLIFrameElement
                  try {
                    // If we can't access contentDocument, it's likely blocked
                    const doc = iframe.contentDocument
                    if (!doc) {
                      // Show fallback after a brief delay
                      setTimeout(() => {
                        const fallback = document.getElementById(`fallback-${url.replace(/[^a-zA-Z0-9]/g, '')}`)
                        if (fallback) {
                          fallback.style.display = 'flex'
                          iframe.style.display = 'none'
                        }
                      }, 1000)
                    }
                  } catch (e) {
                    // Cross-origin error - definitely blocked
                    setTimeout(() => {
                      const fallback = document.getElementById(`fallback-${url.replace(/[^a-zA-Z0-9]/g, '')}`)
                      if (fallback) {
                        fallback.style.display = 'flex'
                        iframe.style.display = 'none'
                      }
                    }, 500)
                  }
                }}
              />
              
              {/* Enhanced fallback content */}
              <div 
                className="iframe-fallback" 
                id={`fallback-${url.replace(/[^a-zA-Z0-9]/g, '')}`}
                style={{ display: 'none' }}
              >
                <div className="fallback-icon">🔒</div>
                <h3 className="fallback-title">Content Blocked</h3>
                <p className="fallback-text">
                  {url.includes('nhs.uk') ? 'NHS.uk prevents embedding for security.' :
                   url.includes('mayoclinic.org') ? 'Mayo Clinic prevents embedding for security.' :
                   'This site prevents embedding for security reasons.'}
                </p>
                <button
                  onClick={() => window.open(url, '_blank')}
                  className="fallback-button"
                >
                  Open in New Tab
                </button>
                <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
                  Don't worry - this is normal for medical sites to protect patient privacy.
                </p>
              </div>
            </>
          )}
        </div>
        
        {/* Footer */}
        <div className="modal-source-footer">
          <div className="source-url-display">
            Source: {url}
          </div>
          <button
            onClick={() => window.open(url, '_blank')}
            className="open-external-button"
          >
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Open in New Tab
          </button>
        </div>
      </div>
    </div>
  )
}

export default SourceModal