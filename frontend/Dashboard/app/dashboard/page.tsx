"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ProtectedRoute } from "@/components/protected-route"

// Simple frontend-only JWT parser to read token payloads
function parseJwt(token: string) {
  try {
    const base64Url = token.split(".")[1]
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/")
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    )
    return JSON.parse(jsonPayload)
  } catch (e) {
    return null
  }
}
// import { BrandBadge } from "@/components/polar/brand-badge"
import { ChatCard } from "@/components/polar/chat-card"
import { FooterLinks } from "@/components/polar/footer-links"

const DEFAULT_BACKGROUND = "/images/background.png"

export default function PolarLandingPage() {
  const router = useRouter()
  const [backgroundImage, setBackgroundImage] = useState(DEFAULT_BACKGROUND)
  const [userName, setUserName] = useState("Employee")

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (token) {
      // Decode the token and extract the name (which FastAPI stored in the 'sub' variable)
      const decoded = parseJwt(token)
      if (decoded?.sub) {
        setUserName(decoded.sub)
      }
    }
  }, [])

  const handleResetBackground = () => {
    setBackgroundImage(DEFAULT_BACKGROUND)
  }

  return (
    <ProtectedRoute>
      <main
      className="relative flex min-h-screen flex-col items-center justify-between bg-cover bg-center bg-no-repeat px-4 py-8"
      style={{
        backgroundImage: `url('${backgroundImage}')`,
      }}
    >
      {/* Gradient overlay for better contrast */}
      <div className="absolute inset-0 bg-linear-to-t from-black via-black/50 to-transparent" />

      {/* Logout Button */}
      <div className="absolute top-4 right-6 z-20">
        <button
          onClick={() => {
            localStorage.removeItem("access_token")
            router.replace("/login")
          }}
          className="px-4 py-2 text-sm font-medium text-white/70 border border-white/20 hover:text-white hover:bg-white/10 rounded-md transition-colors backdrop-blur-md"
        >
          Sign Out
        </button>
      </div>

      {/* Content */}
      <div className="relative z-10 flex w-full flex-col items-center pt-8">
        {/* <BrandBadge /> */}
      </div>

      <div className="relative z-10 flex w-full flex-col items-center">
        <ChatCard userName={userName} onBackgroundChange={setBackgroundImage} onResetBackground={handleResetBackground} />
      </div>

      <div className="relative z-10 pb-4">
        <FooterLinks />
      </div>
    </main>
    </ProtectedRoute>
  )
}
