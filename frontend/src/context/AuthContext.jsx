import { createContext, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { getCurrentUser } from '../api/auth'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('eventhub_access_token'))
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(Boolean(localStorage.getItem('eventhub_access_token')))
  const profileRequest = useRef(null)

  const logout = useCallback(() => {
    localStorage.removeItem('eventhub_access_token')
    setToken(null)
    setUser(null)
    setAuthLoading(false)
  }, [])

  const setSession = useCallback((nextToken, nextUser = null) => {
    localStorage.setItem('eventhub_access_token', nextToken)
    setUser(nextUser)
    setToken(nextToken)
    setAuthLoading(!nextUser)
  }, [])

  useEffect(() => {
    const clearSession = () => logout()
    window.addEventListener('eventhub:unauthorized', clearSession)
    return () => window.removeEventListener('eventhub:unauthorized', clearSession)
  }, [logout])

  useEffect(() => {
    if (!token) {
      setUser(null)
      setAuthLoading(false)
      return undefined
    }

    let active = true
    setAuthLoading(true)
    if (!profileRequest.current || profileRequest.current.token !== token) {
      profileRequest.current = { token, promise: getCurrentUser() }
    }
    profileRequest.current.promise
      .then((profile) => { if (active) setUser(profile) })
      .catch(() => { if (active) logout() })
      .finally(() => { if (active) setAuthLoading(false) })

    return () => { active = false }
  }, [token, logout])

  const value = useMemo(() => ({
    token, user, authLoading, setUser, setSession, logout,
  }), [token, user, authLoading, setSession, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
