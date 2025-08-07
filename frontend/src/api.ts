import axios from 'axios'

// Since axios is configured globally in App.tsx, we can use it directly
export async function apiRequest(endpoint: string, options: any = {}) {
  try {
    const response = await axios({
      url: endpoint,
      method: options.method || 'GET',
      data: options.body ? JSON.parse(options.body) : undefined,
      ...options
    })
    return response.data
  } catch (error: any) {
    // Match the original error format
    throw { response: { data: error.response?.data } }
  }
}

// Auth API calls
export const authApi = {
  login: (email: string, password: string) =>
    apiRequest("/auth/login", {
      method: "POST",
      data: { email, password }
    }),

  register: (data: any) =>
    apiRequest("/auth/register", {
      method: "POST",
      data
    }),

  getMe: () =>
    apiRequest("/auth/me"),

  updateMe: (data: any) =>
    apiRequest("/auth/me", {
      method: "PUT",
      data
    })
}

// Chat API calls - token handled by axios interceptor
export const chatApi = {
  sendMessage: (message: string, location?: string, sessionId?: string) =>
    apiRequest("/chat", {
      method: "POST",
      data: { 
        message, 
        location,
        session_id: sessionId
      }
    }),

  getSessions: () =>
    apiRequest("/chat/sessions"),

  getSessionMessages: (sessionId: string) =>
    apiRequest(`/chat/session/${sessionId}`),

  deleteSession: (sessionId: string) =>
    apiRequest(`/chat/session/${sessionId}`, {
      method: 'DELETE'
    }),

  getCategories: () =>
    apiRequest("/chat/categories")
}