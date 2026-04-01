"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ProtectedRoute } from "@/components/protected-route"
import Link from "next/link"

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
  const [isAdmin, setIsAdmin] = useState(false)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (token) {
      // Decode the token and extract the name
      const decoded = parseJwt(token)
      if (decoded?.sub) {
        setUserName(decoded.sub)
      }
      if (decoded?.emp_id === "ADMIN") {
        setIsAdmin(true)
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

      {/* Admin Actions Button & Modal */}
      {isAdmin && (
        <>
          <div className="absolute top-4 left-6 z-20">
            <button
              onClick={() => setShowModal(true)}
              className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white/70 border border-white/20 hover:text-white hover:bg-white/10 rounded-md transition-colors backdrop-blur-md"
            >
              Update Details
            </button>
          </div>

          {showModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
              <div className="relative w-full max-w-sm rounded-2xl border border-white/10 bg-black/80 p-6 shadow-2xl">
                <button
                  onClick={() => setShowModal(false)}
                  className="absolute top-4 right-4 text-white/50 hover:text-white"
                >
                  ✕
                </button>
                <h3 className="mb-6 text-xl font-medium text-white">Select Action</h3>
                <div className="flex flex-col gap-3">
                  <Link
                    href="/dashboard/admin/update-attendance"
                    className="flex w-full items-center justify-between rounded-xl bg-white/5 p-4 text-left text-sm text-white/90 hover:bg-white/10 transition-colors border border-white/10"
                  >
                    <span>Update existing employee</span>
                    <span className="text-white/40">›</span>
                  </Link>
                  <Link
                    href="/dashboard/admin/register"
                    className="flex w-full items-center justify-between rounded-xl bg-white/5 p-4 text-left text-sm text-white/90 hover:bg-white/10 transition-colors border border-white/10"
                  >
                    <span>Register new employee</span>
                    <span className="text-white/40">›</span>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </>
      )}

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
        <ChatCard userName={userName} isAdmin={isAdmin} onBackgroundChange={setBackgroundImage} onResetBackground={handleResetBackground} />
      </div>

      <div className="relative z-10 pb-4">
        <FooterLinks />
      </div>
    </main>
    </ProtectedRoute>
  )
}
