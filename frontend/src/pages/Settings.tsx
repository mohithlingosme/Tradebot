import { useState, useEffect } from 'react'
import '../styles/Settings.css'

interface UserProfile {
  username: string
  email: string
  firstName?: string
  lastName?: string
  phone?: string
  notificationEnabled: boolean
  emailNotifications: boolean
}

function Settings() {
  const username = localStorage.getItem('username') || 'user'
  
  const [profile, setProfile] = useState<UserProfile>({
    username,
    email: `${username}@example.com`,
    notificationEnabled: true,
    emailNotifications: true
  })
  
  const [apiUrl, setApiUrl] = useState('http://localhost:8000')
  const [theme, setTheme] = useState('light')
  const [refreshInterval, setRefreshInterval] = useState(60)
  const [defaultInterval, setDefaultInterval] = useState('1d')
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'security'>('profile')

  useEffect(() => {
    // Load settings from localStorage
    const savedApiUrl = localStorage.getItem('apiUrl')
    const savedTheme = localStorage.getItem('theme')
    const savedRefreshInterval = localStorage.getItem('refreshInterval')
    const savedDefaultInterval = localStorage.getItem('defaultInterval')
    
    if (savedApiUrl) setApiUrl(savedApiUrl)
    if (savedTheme) setTheme(savedTheme)
    if (savedRefreshInterval) setRefreshInterval(Number(savedRefreshInterval))
    if (savedDefaultInterval) setDefaultInterval(savedDefaultInterval)
  }, [])

  const saveSettings = () => {
    // Save settings to local storage
    localStorage.setItem('apiUrl', apiUrl)
    localStorage.setItem('theme', theme)
    localStorage.setItem('refreshInterval', refreshInterval.toString())
    localStorage.setItem('defaultInterval', defaultInterval)
    alert('Settings saved!')
  }

  const saveProfile = () => {
    // Save profile (in production, send to backend)
    localStorage.setItem('userProfile', JSON.stringify(profile))
    alert('Profile updated!')
  }

  const handleProfileChange = (field: keyof UserProfile, value: string | boolean) => {
    setProfile(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="settings">
      <div className="settings-header">
        <h1>Settings</h1>
        <div className="settings-tabs">
          <button
            className={activeTab === 'profile' ? 'active' : ''}
            onClick={() => setActiveTab('profile')}
          >
            Profile
          </button>
          <button
            className={activeTab === 'preferences' ? 'active' : ''}
            onClick={() => setActiveTab('preferences')}
          >
            Preferences
          </button>
          <button
            className={activeTab === 'security' ? 'active' : ''}
            onClick={() => setActiveTab('security')}
          >
            Security
          </button>
        </div>
      </div>

      <div className="settings-content">
        {activeTab === 'profile' && (
          <div className="profile-section">
            <h2>Profile Information</h2>
            
            <div className="profile-form">
              <div className="form-group">
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  type="text"
                  value={profile.username}
                  onChange={(e) => handleProfileChange('username', e.target.value)}
                  disabled
                  className="disabled"
                />
                <small>Username cannot be changed</small>
              </div>

              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={profile.email}
                  onChange={(e) => handleProfileChange('email', e.target.value)}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="firstName">First Name</label>
                  <input
                    id="firstName"
                    type="text"
                    value={profile.firstName || ''}
                    onChange={(e) => handleProfileChange('firstName', e.target.value)}
                    placeholder="Enter first name"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="lastName">Last Name</label>
                  <input
                    id="lastName"
                    type="text"
                    value={profile.lastName || ''}
                    onChange={(e) => handleProfileChange('lastName', e.target.value)}
                    placeholder="Enter last name"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="phone">Phone Number</label>
                <input
                  id="phone"
                  type="tel"
                  value={profile.phone || ''}
                  onChange={(e) => handleProfileChange('phone', e.target.value)}
                  placeholder="Enter phone number"
                />
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={profile.notificationEnabled}
                    onChange={(e) => handleProfileChange('notificationEnabled', e.target.checked)}
                  />
                  Enable notifications
                </label>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={profile.emailNotifications}
                    onChange={(e) => handleProfileChange('emailNotifications', e.target.checked)}
                  />
                  Email notifications
                </label>
              </div>

              <button onClick={saveProfile} className="save-button">
                Save Profile
              </button>
            </div>
          </div>
        )}

        {activeTab === 'preferences' && (
          <div className="preferences-section">
            <h2>Preferences</h2>

            <div className="form-group">
              <label htmlFor="apiUrl">Backend API URL:</label>
              <input
                id="apiUrl"
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://localhost:8000"
              />
            </div>

            <div className="form-group">
              <label htmlFor="theme">Theme:</label>
              <select
                id="theme"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto (System)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="refreshInterval">Chart Refresh Interval (seconds):</label>
              <input
                id="refreshInterval"
                type="number"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                min="10"
                max="300"
              />
            </div>

            <div className="form-group">
              <label htmlFor="defaultInterval">Default Chart Interval:</label>
              <select
                id="defaultInterval"
                value={defaultInterval}
                onChange={(e) => setDefaultInterval(e.target.value)}
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="30m">30 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
                <option value="1wk">1 Week</option>
                <option value="1mo">1 Month</option>
              </select>
            </div>

            <button onClick={saveSettings} className="save-button">
              Save Preferences
            </button>
          </div>
        )}

        {activeTab === 'security' && (
          <div className="security-section">
            <h2>Security Settings</h2>

            <div className="security-info">
              <div className="info-item">
                <h3>Password</h3>
                <p>Change your account password</p>
                <button className="secondary-button">Change Password</button>
              </div>

              <div className="info-item">
                <h3>Two-Factor Authentication</h3>
                <p>Add an extra layer of security to your account</p>
                <button className="secondary-button">Enable 2FA</button>
              </div>

              <div className="info-item">
                <h3>Active Sessions</h3>
                <p>Manage your active login sessions</p>
                <button className="secondary-button">View Sessions</button>
              </div>

              <div className="info-item">
                <h3>API Keys</h3>
                <p>Manage your API keys for programmatic access</p>
                <button className="secondary-button">Manage API Keys</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Settings
