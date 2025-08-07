interface MarkdownRendererProps {
    text: string
    onLinkClick?: (url: string, title: string) => void
  }
  
  function MarkdownRenderer({ text, onLinkClick }: MarkdownRendererProps) {
    const parseMarkdown = (text: string) => {
      // Escape HTML to prevent XSS
      const escapeHtml = (str: string) => {
        const div = document.createElement('div')
        div.textContent = str
        return div.innerHTML
      }
  
      // Handle code blocks (triple backticks)
      text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre class="code-block"><code>${escapeHtml(code.trim())}</code></pre>`
      })
  
      // Handle inline code (single backticks)
      text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  
      // Handle headers
      text = text.replace(/^### (.*?)$/gm, '<h3 class="md-h3">$1</h3>')
      text = text.replace(/^## (.*?)$/gm, '<h2 class="md-h2">$1</h2>')
      text = text.replace(/^# (.*?)$/gm, '<h1 class="md-h1">$1</h1>')
  
      // Handle bold text
      text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
      // Handle italic text
      text = text.replace(/(?<!\*)\*(?!\*)([^*]+)\*(?!\*)/g, '<em>$1</em>')
  
      // Handle links - convert to clickable buttons for modal
      text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url) => {
        const linkId = `link_${Math.random().toString(36).substr(2, 9)}`
        // Store the link handler in a global object
        window.linkHandlers = window.linkHandlers || {}
        window.linkHandlers[linkId] = () => onLinkClick && onLinkClick(url, linkText)
        
        return `<button onclick="window.linkHandlers['${linkId}']()" class="md-link">${linkText} <svg class="link-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg></button>`
      })
  
      // Handle numbered lists with bold titles
      text = text.replace(/^(\d+)\.\s+\*\*(.*?)\*\*:\s*([\s\S]*?)(?=\n\d+\.|\n\n|$)/gm, (match, num, title, content) => {
        const processedContent = content.replace(/^-\s+(.+)$/gm, '<li class="sub-bullet">$1</li>')
        const hasSubBullets = processedContent.includes('<li')
        
        if (hasSubBullets) {
          const wrappedSubBullets = processedContent.replace(/(<li[^>]*>.*<\/li>)/gs, '<ul class="sub-list">$1</ul>')
          return `<li class="numbered-item"><strong>${title}:</strong> ${wrappedSubBullets}</li>`
        } else {
          return `<li class="numbered-item"><strong>${title}:</strong> ${content.trim()}</li>`
        }
      })
  
      // Handle regular numbered lists
      text = text.replace(/^(\d+)\.\s+(.+)$/gm, '<li class="numbered-item">$2</li>')
  
      // Handle unordered lists  
      text = text.replace(/^[-*]\s+(.+)$/gm, '<li class="bullet-item">$1</li>')
      
      // Wrap consecutive numbered list items
      text = text.replace(/(<li class="numbered-item">[^<]*<\/li>(?:\s*<li class="numbered-item">[^<]*<\/li>)*)/g, '<ol class="numbered-list">$1</ol>')
      
      // Wrap consecutive unordered list items  
      text = text.replace(/(<li class="bullet-item">[^<]*<\/li>(?:\s*<li class="bullet-item">[^<]*<\/li>)*)/g, '<ul class="bullet-list">$1</ul>')
  
      // Handle blockquotes
      text = text.replace(/^>\s+(.+)$/gm, '<blockquote class="blockquote">$1</blockquote>')
  
      // Handle line breaks
      text = text.replace(/\n\n/g, '</p><p class="md-paragraph">')
      text = text.replace(/\n/g, '<br>')
      
      // Wrap in paragraph tags
      text = `<p class="md-paragraph">${text}</p>`
  
      // Clean up empty paragraphs
      text = text.replace(/<p class="md-paragraph"><\/p>/g, '')
      
      // Clean up paragraph tags around lists
      text = text.replace(/<p class="md-paragraph">(<[ou]l[^>]*>)/g, '$1')
      text = text.replace(/(<\/[ou]l>)<\/p>/g, '$1')
  
      return text
    }
  
    return (
      <div 
        className="markdown-content"
        dangerouslySetInnerHTML={{ 
          __html: parseMarkdown(text) 
        }} 
      />
    )
  }
  
  export default MarkdownRenderer