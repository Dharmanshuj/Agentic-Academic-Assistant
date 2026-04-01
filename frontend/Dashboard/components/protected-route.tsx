"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // In Next.js, useRouter replaces react-router-dom's useNavigate hook!
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const checkAuthStatus = () => {
      const token = localStorage.getItem("access_token")

      const isTokenExpired = (token: string) => {
        try {
          const payloadBase64 = token.split(".")[1]
          const decodedPayload = JSON.parse(window.atob(payloadBase64))
          const exp = decodedPayload.exp
          const now = Math.floor(Date.now() / 1000)
          return exp < now
        } catch (e) {
          return true // If decoding fails, treat as expired
        }
      }

      if (!token || isTokenExpired(token)) {
        if (token) localStorage.removeItem("access_token") // Clean up expired token
        router.replace("/login")
      } else {
        setIsAuthenticated(true)
      }
    }

    // Run initial check
    checkAuthStatus()

    // Periodically check every 5 seconds to automatically log out if token expires
    const intervalId = setInterval(checkAuthStatus, 5000)

    return () => clearInterval(intervalId)
  }, [router])

  // Prevent the dashboard from flashing before the redirect happens
  if (!isAuthenticated) {
    return null // or a loading spinner
  }

  return <>{children}</>
}
