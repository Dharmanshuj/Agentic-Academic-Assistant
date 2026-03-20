"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // In Next.js, useRouter replaces react-router-dom's useNavigate hook!
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      router.replace("/login")
    } else {
      setIsAuthenticated(true)
    }
  }, [router])

  // Prevent the dashboard from flashing before the redirect happens
  if (!isAuthenticated) {
    return null // or a loading spinner
  }

  return <>{children}</>
}
