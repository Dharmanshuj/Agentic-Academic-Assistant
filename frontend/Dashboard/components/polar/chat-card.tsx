"use client"

import { useState, useRef, useEffect } from "react"
import { SnowflakeIcon } from "@/components/icons/snowflake-icon"
import { ChatInput } from "./chat-input"
import { InputControls } from "./input-controls"
import { SpeakerIcon } from "@/components/icons/speaker-icon"
import { SuggestionBadges } from "./suggestion-badges"
import ReactMarkdown from "react-markdown"

interface ChatCardProps {
  userName?: string
  isAdmin?: boolean
  onBackgroundChange?: (imageUrl: string) => void
  onResetBackground?: () => void
}

type Message = { role: "user" | "assistant"; content: string }

export function ChatCard({ userName, isAdmin, onBackgroundChange, onResetBackground }: ChatCardProps) {
  const [inputValue, setInputValue] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Cleanup speech on unmount
  useEffect(() => {
    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  const handleSpeak = (text: string, index: number) => {
    if (!("speechSynthesis" in window)) {
      alert("Your browser does not support text-to-speech functionality.")
      return
    }

    // Toggle off if currently speaking the same message
    if (speakingIndex === index) {
      window.speechSynthesis.cancel()
      setSpeakingIndex(null)
      return
    }

    // Stop anything currently speaking
    window.speechSynthesis.cancel()

    // Strip basic markdown symbols for cleaner speech
    const cleanText = text.replace(/[*_#`\n]/g, " ").trim()
    const utterance = new SpeechSynthesisUtterance(cleanText)
    
    // Customize voice slightly if needed (optional)
    utterance.rate = 1.05
    utterance.pitch = 1.0
    
    utterance.onend = () => setSpeakingIndex(null)
    utterance.onerror = () => setSpeakingIndex(null)

    window.speechSynthesis.speak(utterance)
    setSpeakingIndex(index)
  }

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSuggestionSelect = (suggestion: { id: string; label: string }) => {
    handleSubmit(suggestion.label)
  }

  const handleSubmit = async (query: string) => {
    if (!query.trim() || isLoading) return

    setInputValue("")
    setIsLoading(true)

    // Add user message and assistant placeholder in one atomic update
    setMessages((prev) => [...prev, { role: "user", content: query }, { role: "assistant", content: "" }])

    try {
      const token = localStorage.getItem("access_token")
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

      // 3. Trigger SSE Stream
      const response = await fetch(`${apiUrl}/ask-me/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        throw new Error("Failed to fetch response from AI")
      }

      // 4. Parse Server-Sent Events
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let done = false
      let buffer = "" // Buffer to hold incomplete chunks

      while (!done) {
        if (!reader) break
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          buffer += decoder.decode(value, { stream: true })

          let newlineIndex
          // SSE messages end with \n\n. Process fully received messages.
          while ((newlineIndex = buffer.indexOf("\n\n")) >= 0) {
            const message = buffer.slice(0, newlineIndex)
            buffer = buffer.slice(newlineIndex + 2)

            if (message.startsWith("data: ")) {
              const dataStr = message.replace("data: ", "")
              try {
                const parsed = JSON.parse(dataStr)
                const text = parsed.text || ""

                // Append text to the current assistant message
                setMessages((prev) => {
                  if (prev.length === 0) return prev
                  const newMsgs = [...prev]
                  const lastMsg = { ...newMsgs[newMsgs.length - 1] }
                  if (lastMsg.role === "assistant") {
                    lastMsg.content += text
                    newMsgs[newMsgs.length - 1] = lastMsg
                  }
                  return newMsgs
                })
              } catch (e) {
                console.error("SSE JSON parse error:", e)
              }
            }
          }
        }

        if (done) {
          // final partial message flush in case the server omitted trailing delimiter
          const trimmed = buffer.trim()
          if (trimmed && trimmed.startsWith("data: ")) {
            const dataStr = trimmed.replace("data: ", "")
            try {
              const parsed = JSON.parse(dataStr)
              const text = parsed.text || ""
              if (text) {
                setMessages((prev) => {
                  if (prev.length === 0) return prev
                  const newMsgs = [...prev]
                  const lastMsg = { ...newMsgs[newMsgs.length - 1] }
                  if (lastMsg.role === "assistant") {
                    lastMsg.content += text
                    newMsgs[newMsgs.length - 1] = lastMsg
                  }
                  return newMsgs
                })
              }
            } catch (e) {
              console.error("SSE final buffer parse error:", e)
            }
          }
          buffer = ""
        }
      }
    } catch (error) {
      console.error("Chat error:", error)
      setMessages((prev) => {
        const newMsgs = [...prev]
        const lastMsg = newMsgs[newMsgs.length - 1]
        if (lastMsg?.role === "assistant" && !lastMsg.content) {
          lastMsg.content = "Sorry, I encountered an error connecting to the server."
          newMsgs[newMsgs.length - 1] = lastMsg
        }
        return newMsgs
      })
    } finally {
      setIsLoading(false)
      setMessages((prev) => {
        if (prev.length === 0) return prev
        const newMsgs = [...prev]
        const lastMsg = { ...newMsgs[newMsgs.length - 1] }
        if (lastMsg.role === "assistant" && lastMsg.content.trim() === "") {
          lastMsg.content = "No response received yet. Please try again."
          newMsgs[newMsgs.length - 1] = lastMsg
        }
        return newMsgs
      })
    }
  }

  return (
    <div className="w-full max-w-5xl rounded-2xl border border-transparent bg-transparent p-6 transition-all duration-300">
      <div className="flex flex-col gap-6 items-start w-full">
        {/* Header - Only show if no messages */}
        {messages.length === 0 && (
          <div className="flex flex-col gap-2 items-start w-full">
            <div className="flex items-center gap-2">
              <SnowflakeIcon className="h-5 w-5 text-sky-400" />
              <p className="text-sm text-white/80">Hello {userName}!</p>
            </div>
            <h1 className="text-2xl font-semibold text-white">What can I help you today?</h1>
          </div>
        )}

        {/* Chat Messages */}
        {messages.length > 0 && (
          <div className="flex w-full flex-col gap-4 max-h-[50vh] overflow-y-auto pr-2 pb-2 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/20 [&::-webkit-scrollbar-thumb]:rounded-full">
            {messages.map((m, i) => (
              <div key={i} className={`flex flex-col w-full ${m.role === "user" ? "items-end" : "items-start"}`}>
                {m.role === "assistant" && (
                  <div className="flex items-center gap-2 mb-1">
                    <SnowflakeIcon className="h-4 w-4 text-sky-400" />
                    <span className="text-sm text-white">Pulse AI</span>
                  </div>
                )}
                <div
                  className={`px-4 py-2.5 rounded-2xl max-w-[85%] whitespace-pre-wrap ${m.role === "user"
                    ? "bg-teal-600 text-white rounded-br-sm"
                    : "bg-black/80 text-white/90 rounded-bl-sm border border-white/10"
                    }`}
                >
                  {m.content ? (
                    m.role === "assistant" ? (
                      <div className="flex flex-col gap-2 relative group">
                        <ReactMarkdown
                          components={{
                            ul: ({ node, ...props }: any) => <ul className="list-disc pl-4 my-1" {...props} />,
                            ol: ({ node, ...props }: any) => <ol className="list-decimal pl-4 my-1" {...props} />,
                            li: ({ node, ...props }: any) => <li className="my-0.5" {...props} />,
                            p: ({ node, ...props }: any) => <p className="mb-2 last:mb-0" {...props} />,
                            strong: ({ node, ...props }: any) => <strong className="font-semibold text-white/95" {...props} />
                          }}
                        >
                          {m.content}
                        </ReactMarkdown>
                        {/* Read Aloud Button */}
                        <button
                          onClick={() => handleSpeak(m.content, i)}
                          className={`self-start flex items-center gap-1.5 px-3 py-1.5 mt-1 rounded-full text-xs font-medium transition-all duration-200 ${
                            speakingIndex === i
                              ? "bg-sky-500/20 text-sky-400 ring-1 ring-sky-500/50"
                              : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
                          }`}
                        >
                          <SpeakerIcon className="w-3.5 h-3.5" />
                          {speakingIndex === i ? "Stop Speaking" : "Listen"}
                        </button>
                      </div>
                    ) : (
                      m.content
                    )
                  ) : m.role === "assistant" && isLoading ? (
                    <span className="flex gap-1 items-center h-5">
                      <span className="w-1.5 h-1.5 bg-white/60 rounded-full animate-bounce" />
                      <span className="w-1.5 h-1.5 bg-white/60 rounded-full animate-bounce [animation-delay:0.2s]" />
                      <span className="w-1.5 h-1.5 bg-white/60 rounded-full animate-bounce [animation-delay:0.4s]" />
                    </span>
                  ) : null}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input section */}
        <div className="flex w-full flex-col gap-1">
          <ChatInput
            placeholder="Ask me anything..."
            value={inputValue}
            onChange={setInputValue}
            onSubmit={handleSubmit}
          />
          <InputControls onBackgroundChange={onBackgroundChange} onResetBackground={onResetBackground} />
        </div>

        {/* Suggestions - Only show if no messages */}
        {messages.length === 0 && (
          <SuggestionBadges suggestions={isAdmin ? ADMIN_SUGGESTIONS : DEFAULT_SUGGESTIONS} onSelect={handleSuggestionSelect} />
        )}
      </div>
    </div>
  )
}

const DEFAULT_SUGGESTIONS = [
  { id: "1", label: "What is my salary?" },
  { id: "2", label: "Show my last payslip" },
  { id: "3", label: "How much tax was deducted?" },
  { id: "4", label: "Breakdown of allowances" },
]

const ADMIN_SUGGESTIONS = [
  { id: "1", label: "Show data for all employees" },
  { id: "2", label: "What is the company leave policy?" },
  { id: "3", label: "Average net pay for all employees" },
  { id: "4", label: "Explain the handbook rules" },
]
