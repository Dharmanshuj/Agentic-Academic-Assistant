import type React from "react"
import type { Metadata } from "next"
import { Plus_Jakarta_Sans } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { Toaster } from "sonner"
import "./globals.css"

const plusJakartaSans = {
  className: 'font-sans'
}

export const metadata: Metadata = {
  title: "Pulse AI - AI Powered Chatbot",
  description: "Intelligent AI assistant for NIT Jalandhar students",
  generator: "NITJ",
  icons: {
    icon: "/convertico-nitjlogo_32x32.png",
    apple: "/convertico-nitjlogo_128x128.png",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans antialiased ${plusJakartaSans.className}`}>
        {children}
        <Toaster />
        <Analytics />
      </body>
    </html>
  )
}
