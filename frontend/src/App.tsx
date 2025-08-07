import { useState, useEffect } from 'react'
import axios from 'axios'
import Login from './components/Login'
import Chat from './components/Chat'
import Profile from './components/Profile'

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"
axios.defaults.baseURL = API_BASE

function App() {

  console.log('App component rendering')
  
  const [token, setToken] = useState<string>(
    () => localStorage.getItem("jwt") ?? ""
  )

  const [profileMode, setProfileMode] = useState(false)

  console.log('Current token:', token)

  useEffect(() => {
    const id = axios.interceptors.request.use(cfg => {
      if (token) cfg.headers.Authorization = `Bearer ${token}`
      return cfg
    })
    return () => axios.interceptors.request.eject(id)
  }, [token])

  const handleAuth = (newToken: string) => {
    localStorage.setItem("jwt", newToken)
    setToken(newToken)
  }

  const handleLogout = () => {
    localStorage.removeItem("jwt")
    setToken("")
  }

  return (
    <div className="app-container">
      {token ? (
        profileMode ? (
          <Profile onBack={() => setProfileMode(false)} />
        ) : (
          <>
            <button className="profile-btn" onClick={() => setProfileMode(true)} style={{position:'absolute',top:10,right:10}}>Profile</button>
            <Chat onLogout={handleLogout} token={token} />
          </>
        )
      ) : (
        <Login onAuth={handleAuth} />
      )}
    </div>
  )
}

export default App