import { useEffect, useState } from 'react'
import { authApi } from '../api'

interface ProfileProps {
  onBack: () => void
}

const initialState = {
  full_name: '',
  date_of_birth: '',
  gender: '',
  sex: '',
  country: '',
  address: '',
  ethnic_group: '',
  long_term_conditions: '',
  medications: '',
  consent_to_data_storage: false,
  password: '',
}

export default function Profile({ onBack }: ProfileProps) {
  const [form, setForm] = useState<any>(initialState)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    setLoading(true)
    authApi.getMe()
      .then(data => {
        setForm((f: any) => ({ ...f, ...data }))
      })
      .catch(() => setError('Failed to load profile'))
      .finally(() => setLoading(false))
  }, [])

  const handleChange = (e: any) => {
    const { name, value, type, checked } = e.target
    setForm((f: any) => ({
      ...f,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')
    const payload = { ...form }
    if (!payload.password) delete payload.password
    try {
      await authApi.updateMe(payload)
      setSuccess('Profile updated!')
      setForm((f: any) => ({ ...f, password: '' }))
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Update failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="profile-container">
      <button onClick={onBack} style={{marginBottom:16}}>Back</button>
      <h2>Edit Profile</h2>
      {error && <div className="error-msg">{error}</div>}
      {success && <div className="success-msg">{success}</div>}
      <form onSubmit={handleSubmit} className="profile-form">
        <input
          className="form-input"
          type="text"
          name="full_name"
          placeholder="Full Name"
          value={form.full_name || ''}
          onChange={handleChange}
          disabled={loading}
        />
        <input
          className="form-input"
          type="date"
          name="date_of_birth"
          placeholder="Date of Birth"
          value={form.date_of_birth || ''}
          onChange={handleChange}
          disabled={loading}
        />
        <select
          className="form-input"
          name="gender"
          value={form.gender || ''}
          onChange={handleChange}
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
          name="sex"
          value={form.sex || ''}
          onChange={handleChange}
          disabled={loading}
        >
          <option value="">Select Sex</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
        </select>
        <input
          className="form-input"
          type="text"
          name="country"
          placeholder="Country"
          value={form.country || ''}
          onChange={handleChange}
          disabled={loading}
        />
        <input
          className="form-input"
          type="text"
          name="address"
          placeholder="Full Address"
          value={form.address || ''}
          onChange={handleChange}
          disabled={loading}
        />
        <select
          className="form-input"
          name="ethnic_group"
          value={form.ethnic_group || ''}
          onChange={handleChange}
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
          name="long_term_conditions"
          placeholder="Long-term Medical Conditions"
          value={form.long_term_conditions || ''}
          onChange={handleChange}
          disabled={loading}
        />
        <textarea
          className="form-input"
          name="medications"
          placeholder="Medications"
          value={form.medications || ''}
          onChange={handleChange}
          disabled={loading}
        />
        <label style={{marginTop:8}}>
          <input
            type="checkbox"
            name="consent_to_data_storage"
            checked={!!form.consent_to_data_storage}
            onChange={handleChange}
            disabled={loading}
          />
          Consent to data storage
        </label>
        <input
          className="form-input"
          type="password"
          name="password"
          placeholder="New Password (leave blank to keep current)"
          value={form.password || ''}
          onChange={handleChange}
          disabled={loading}
        />
        <button className="form-btn" type="submit" disabled={loading} style={{marginTop:16}}>
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </form>
    </div>
  )
} 