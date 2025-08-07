import { useState } from 'react'
import { authApi } from '../api'

interface LoginProps {
  onAuth: (token: string) => void
}

function Login({ onAuth }: LoginProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isSignUp, setIsSignUp] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  // New user data fields
  const [fullName, setFullName] = useState("")
  const [dateOfBirth, setDateOfBirth] = useState("")
  const [gender, setGender] = useState("")
  const [sex, setSex] = useState("")
  const [country, setCountry] = useState("")
  const [address, setAddress] = useState("")
  const [ethnicGroup, setEthnicGroup] = useState("")
  const [longTermConditions, setLongTermConditions] = useState("")
  const [medications, setMedications] = useState("")
  const [consent, setConsent] = useState(false)

  const handleLogin = async () => {
    if (!email || !password) {
      setError("Please fill in all fields")
      return
    }
    
    setLoading(true)
    setError("")
    
    try {
      const data = await authApi.login(email, password)
      onAuth(data.access_token)
    } catch (error: any) {
      setError(error.response?.data?.message || "Login failed")
    } finally {
      setLoading(false)
    }
  }

  const handleSignUp = async () => {
    if (!email || !password || !confirmPassword) {
      setError("Please fill in all fields")
      return
    }
    
    if (password !== confirmPassword) {
      setError("Passwords don't match")
      return
    }
    
    if (password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }
    
    if (!country) {
      setError("Country is required")
      return
    }
    
    if (!consent) {
      setError("You must consent to data storage to register")
      return
    }
    
    setLoading(true)
    setError("")
    
    try {
      await authApi.register({
        email,
        password,
        full_name: fullName,
        date_of_birth: dateOfBirth,
        gender,
        sex,
        country,
        address,
        ethnic_group: ethnicGroup,
        long_term_conditions: longTermConditions,
        medications,
        consent_to_data_storage: consent
      })
      setError("")
      alert("Account created successfully! Please log in.")
      setIsSignUp(false)
      setPassword("")
      setConfirmPassword("")
    } catch (error: any) {
      setError(error.response?.data?.message || "Registration failed")
    } finally {
      setLoading(false)
    }
  }

  const toggleMode = () => {
    setIsSignUp(!isSignUp)
    setError("")
    setPassword("")
    setConfirmPassword("")
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">Kyra Health Assistant</h1>
        <p className="login-subtitle">
          {isSignUp ? "Create your account to get started" : "Sign in to continue"}
        </p>

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        <div className="login-form">
          <input 
            className="form-input"
            placeholder="Email address" 
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
          />
          <input 
            className="form-input"
            type="password" 
            placeholder="Password"
            value={password} 
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
          {isSignUp && (
            <>
              <input 
                className="form-input"
                type="password" 
                placeholder="Confirm Password"
                value={confirmPassword} 
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
              />
              <input
                className="form-input"
                type="text"
                placeholder="Full Name"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                disabled={loading}
              />
              <input
                className="form-input"
                type="date"
                placeholder="Date of Birth"
                value={dateOfBirth}
                onChange={e => setDateOfBirth(e.target.value)}
                disabled={loading}
              />
              <select
                className="form-input"
                value={gender}
                onChange={e => setGender(e.target.value)}
                disabled={loading}
              >
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Non-binary">Non-binary</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
              <select
                className="form-input"
                value={sex}
                onChange={e => setSex(e.target.value)}
                disabled={loading}
              >
                <option value="">Select Sex</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
              <input
                className="form-input"
                type="text"
                placeholder="Country (required)"
                value={country}
                onChange={e => setCountry(e.target.value)}
                disabled={loading}
                required
              />
              <input
                className="form-input"
                type="text"
                placeholder="Full Address (optional)"
                value={address}
                onChange={e => setAddress(e.target.value)}
                disabled={loading}
              />
              <select
                className="form-input"
                value={ethnicGroup}
                onChange={e => setEthnicGroup(e.target.value)}
                disabled={loading}
              >
                <option value="">Select Ethnic Group</option>
                <option value="White">White</option>
                <option value="Black">Black</option>
                <option value="Asian">Asian</option>
                <option value="Mixed">Mixed</option>
                <option value="Other">Other</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
              <textarea
                className="form-input"
                placeholder="Long-term Medical Conditions"
                value={longTermConditions}
                onChange={e => setLongTermConditions(e.target.value)}
                disabled={loading}
              />
              <textarea
                className="form-input"
                placeholder="Medications"
                value={medications}
                onChange={e => setMedications(e.target.value)}
                disabled={loading}
              />
              <label style={{ display: 'flex', alignItems: 'center', marginTop: 8 }}>
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={e => setConsent(e.target.checked)}
                  disabled={loading}
                  style={{ marginRight: 8 }}
                />
                I consent to the storage of my data as described above
              </label>
            </>
          )}
          <button 
            className={`form-button ${loading ? 'loading' : ''}`}
            onClick={isSignUp ? handleSignUp : handleLogin}
            disabled={loading}
          >
            {loading ? "Processing..." : (isSignUp ? "Create Account" : "Sign In")}
          </button>
        </div>

        <button 
          className="toggle-button"
          onClick={toggleMode}
          disabled={loading}
        >
          {isSignUp ? "Already have an account? Sign in" : "Don't have an account? Create one"}
        </button>
      </div>
    </div>
  )
}

export default Login