import { useContext, useState } from 'react'
import { AuthContext } from '../context/AuthContext'
import { updateMyProfile } from '../api/auth'
import './ProfilePage.css'

function messageFor(error) {
  const detail = error.response?.data?.detail
  return Array.isArray(detail) ? detail.map((item) => item.msg).join(' ') : detail || 'Please try again.'
}

export default function ProfilePage() {
  const { user, setUser } = useContext(AuthContext)
  const [profile, setProfile] = useState({ name: user?.name || '', email: user?.email || '' })
  const [password, setPassword] = useState({ current_password: '', new_password: '' })
  const [profileState, setProfileState] = useState({ busy: false, error: '', success: '' })
  const [passwordState, setPasswordState] = useState({ busy: false, error: '', success: '' })

  async function saveProfile(event) {
    event.preventDefault()
    setProfileState({ busy: true, error: '', success: '' })
    try {
      const updated = await updateMyProfile({ name: profile.name.trim(), email: profile.email.trim() })
      setUser(updated)
      setProfile({ name: updated.name, email: updated.email })
      setProfileState({ busy: false, error: '', success: 'Your profile has been updated.' })
    } catch (error) {
      setProfileState({ busy: false, error: messageFor(error), success: '' })
    }
  }

  async function changePassword(event) {
    event.preventDefault()
    setPasswordState({ busy: true, error: '', success: '' })
    try {
      await updateMyProfile(password)
      setPassword({ current_password: '', new_password: '' })
      setPasswordState({ busy: false, error: '', success: 'Your password has been changed.' })
    } catch (error) {
      setPasswordState({ busy: false, error: messageFor(error), success: '' })
    }
  }

  return <main className="content profile-page">
    <div className="eyebrow muted">YOUR EVENTHUB ACCOUNT</div>
    <header className="profile-heading"><div><h1>Your <em>profile.</em></h1><p>Update the details connected to your EventHub account.</p></div><span className="profile-role">{user?.role}</span></header>
    <div className="profile-panels">
      <section className="profile-panel"><div className="eyebrow muted">ACCOUNT DETAILS</div><h2>Personal information</h2><form onSubmit={saveProfile}>
        <label>Name<input required minLength="2" maxLength="100" autoComplete="name" value={profile.name} onChange={(event) => setProfile({ ...profile, name: event.target.value })}/></label>
        <label>Email address<input required type="email" autoComplete="email" value={profile.email} onChange={(event) => setProfile({ ...profile, email: event.target.value })}/></label>
        {profileState.error && <p className="profile-message profile-error" role="alert">{profileState.error}</p>}
        {profileState.success && <p className="profile-message profile-success" role="status">{profileState.success}</p>}
        <button className="profile-submit" disabled={profileState.busy}>{profileState.busy ? 'Saving…' : 'Save profile'}</button>
      </form></section>
      <section className="profile-panel"><div className="eyebrow muted">SECURITY</div><h2>Change password</h2><p className="profile-description">Confirm your current password before choosing a new one.</p><form onSubmit={changePassword}>
        <label>Current password<input required type="password" autoComplete="current-password" minLength="1" maxLength="128" value={password.current_password} onChange={(event) => setPassword({ ...password, current_password: event.target.value })}/></label>
        <label>New password<input required type="password" autoComplete="new-password" minLength="8" maxLength="128" value={password.new_password} onChange={(event) => setPassword({ ...password, new_password: event.target.value })}/></label>
        {passwordState.error && <p className="profile-message profile-error" role="alert">{passwordState.error}</p>}
        {passwordState.success && <p className="profile-message profile-success" role="status">{passwordState.success}</p>}
        <button className="profile-submit" disabled={passwordState.busy}>{passwordState.busy ? 'Updating…' : 'Change password'}</button>
      </form></section>
    </div>
    <footer className="page-footer"><span>GOOD PLANS. GOOD PEOPLE.</span><span>MADE FOR SHOWING UP <b>✦</b></span></footer>
  </main>
}
