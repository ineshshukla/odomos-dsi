"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import type { User, LoginCredentials, LoginResponse } from '@/lib/types'
import { API_CONFIG, STORAGE_KEYS } from '@/lib/config'

interface RegisterData {
  email: string
  password: string
  full_name: string
  organization: string
  role: 'clinic_admin' | 'gcf_coordinator' | 'super_admin'
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  getAccessToken: () => string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = () => {
      try {
        const userData = localStorage.getItem(STORAGE_KEYS.USER_DATA)
        const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
        
        if (userData && accessToken) {
          setUser(JSON.parse(userData))
        }
      } catch (error) {
        console.error('Error loading user data:', error)
        // Clear invalid data
        localStorage.removeItem(STORAGE_KEYS.USER_DATA)
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
      } finally {
        setIsLoading(false)
      }
    }

    loadUser()
  }, [])

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_CONFIG.AUTH_SERVICE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Login failed')
      }

      const data: LoginResponse = await response.json()
      
      // Store tokens and user data
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.token.access_token)
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.token.refresh_token)
      localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(data.user))
      
      setUser(data.user)

      // Redirect based on role
      if (data.user.role === 'clinic_admin') {
        router.push('/clinic-portal')
      } else if (data.user.role === 'gcf_coordinator') {
        router.push('/gcf-dashboard')
      } else if (data.user.role === 'super_admin') {
        router.push('/super-admin')
      }
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (data: RegisterData) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_CONFIG.AUTH_SERVICE}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Registration failed')
      }

      // Registration successful - don't auto-login, let user manually login
      const result = await response.json()
      return result
    } catch (error) {
      console.error('Registration error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
      
      if (accessToken) {
        // Call logout endpoint
        await fetch(`${API_CONFIG.AUTH_SERVICE}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear local storage
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.USER_DATA)
      
      setUser(null)
      router.push('/')
    }
  }

  const refreshToken = async () => {
    const refreshTokenValue = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
    
    if (!refreshTokenValue) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await fetch(`${API_CONFIG.AUTH_SERVICE}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token)
      
      return data.access_token
    } catch (error) {
      console.error('Token refresh error:', error)
      // If refresh fails, logout
      await logout()
      throw error
    }
  }

  const getAccessToken = () => {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        register,
        logout,
        refreshToken,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
