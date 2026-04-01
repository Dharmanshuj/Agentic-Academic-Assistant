"use client"
 
import { useState, useRef, useEffect } from "react"
import { SnowflakeIcon } from "@/components/icons/snowflake-icon"
import { ChatInput } from "./chat-input"
import { InputControls } from "./input-controls"
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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const currentlySpeakingRef = useRef<string | null>(null)
 
  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])
 
  const handleSuggestionSelect = (suggestion: { id: string; label: string }) => {
    handleSubmit(suggestion.label, false)
  }
 
  const handleReadAloud = (text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return
   
    const isSpeakingThisExactText = window.speechSynthesis.speaking && currentlySpeakingRef.current === text
   
    window.speechSynthesis.cancel() // Stop any current speech
   
    // If they clicked the button for the text that is currently speaking, we just stop and exit.
    if (isSpeakingThisExactText) {
      currentlySpeakingRef.current = null
      return
    }
   
    currentlySpeakingRef.current = text
    // Strip basic markdown syntax so it reads cleaner
    const cleanText = text.replace(/[*#_~`\[\]>]/g, "")
    const utterance = new SpeechSynthesisUtterance(cleanText)
   
    utterance.onend = () => {
      if (currentlySpeakingRef.current === text) {
        currentlySpeakingRef.current = null
      }
    }
   
    window.speechSynthesis.speak(utterance)
  }
 
  const handleSubmit = async (query: string, isVoice: boolean = false) => {
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
      let fullAssistantMessage = "" // Track the full message to read it aloud if needed
      let typingPromise = Promise.resolve()
 
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
               
                if (text) {
                  fullAssistantMessage += text
                }
 
                // Append text to the current assistant message character by character
                typingPromise = typingPromise.then(async () => {
                  for (let i = 0; i < text.length; i++) {
                    await new Promise(resolve => setTimeout(resolve, 10))
                    setMessages((prev) => {
                      if (prev.length === 0) return prev
                      const newMsgs = [...prev]
                      const lastMsg = { ...newMsgs[newMsgs.length - 1] }
                      if (lastMsg.role === "assistant") {
                        lastMsg.content += text[i]
                        newMsgs[newMsgs.length - 1] = lastMsg
                      }
                      return newMsgs
                    })
                  }
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
                fullAssistantMessage += text
                typingPromise = typingPromise.then(async () => {
                  for (let i = 0; i < text.length; i++) {
                    await new Promise(resolve => setTimeout(resolve, 10))
                    setMessages((prev) => {
                      if (prev.length === 0) return prev
                      const newMsgs = [...prev]
                      const lastMsg = { ...newMsgs[newMsgs.length - 1] }
                      if (lastMsg.role === "assistant") {
                        lastMsg.content += text[i]
                        newMsgs[newMsgs.length - 1] = lastMsg
                      }
                      return newMsgs
                    })
                  }
                })
              }
            } catch (e) {
              console.error("SSE final buffer parse error:", e)
            }
          }
          buffer = ""
        }
      }
     
      // If voice generated this query, read the result aloud automatically
      if (isVoice && fullAssistantMessage.trim()) {
        handleReadAloud(fullAssistantMessage)
      }
     
      // Wait for all text to finish typing before ending the "loading" state
      await typingPromise
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
                  <div className="flex items-center gap-3 mb-1 ml-1">
                    <div className="flex items-center gap-2">
                      <SnowflakeIcon className="h-4 w-4 text-sky-400" />
                      <span className="text-sm text-white">Pulse AI</span>
                    </div>
                    {m.content && (
                      <button
                        onClick={() => handleReadAloud(m.content)}
                        className="text-white hover:text-white/80 transition-colors"
                        title="Read aloud"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
                      </button>
                    )}
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
                      <ReactMarkdown
                        components={{
                          ul: ({ node, ...props }: any) => <ul className="list-disc pl-4 my-1" {...props} />,
                          ol: ({ node, ...props }: any) => <ol className="list-decimal pl-4 my-1" {...props} />,
                          li: ({ node, ...props }: any) => <li className="my-0.5" {...props} />,
                          p: ({ node, ...props }: any) => <p className="mb-2 last:mb-0" {...props} />,
                          strong: ({ node, ...props }: any) => <strong className="font-semibold text-white/95" {...props} />
                        }}
                      >
                        {m.content + (isLoading && m.role === "assistant" && i === messages.length - 1 ? " ▍" : "")}
                      </ReactMarkdown>
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