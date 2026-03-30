"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { MicIcon } from "@/components/icons/mic-icon"

interface ChatInputProps {
  placeholder?: string
  value?: string
  onChange?: (value: string) => void
  onSubmit?: (value: string) => void
}

export function ChatInput({
  placeholder = "Ask me anything...",
  value: externalValue,
  onChange: externalOnChange,
  onSubmit,
}: ChatInputProps) {
  const value = externalValue ?? ""
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    // Initialize SpeechRecognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = true // Keep listening until manually stopped
      recognitionRef.current.interimResults = true // Enable live transcription
      recognitionRef.current.lang = "en-US"

      recognitionRef.current.onresult = (event: any) => {
        let transcript = ""

        // Accumulate all final and interim results from the current listening session
        for (let i = 0; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript
        }

        // Just update the input field, do not auto-submit
        externalOnChange?.(transcript.trim())
      }

      recognitionRef.current.onerror = (event: any) => {
        console.error("Speech recognition error", event.error)
        setIsListening(false)
      }

      recognitionRef.current.onend = () => {
        // Only set to false when it genuinely ends
        setIsListening(false)
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    }
  }, [externalOnChange])

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      
      // Auto-submit whatever is currently in the prompt window
      if (value.trim() && onSubmit) {
        onSubmit(value)
        externalOnChange?.("")
      }
    } else {
      recognitionRef.current?.start()
      setIsListening(true)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim() && onSubmit) {
      onSubmit(value)
      externalOnChange?.("")
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full relative flex items-center gap-2">
      <div className="relative w-full flex-grow">
        <input
          type="text"
          value={value}
          onChange={(e) => externalOnChange?.(e.target.value)}
          placeholder={isListening ? "Listening..." : placeholder}
          className="w-full border-0 bg-white/10 px-4 py-3 pb-3 pr-12 text-white placeholder:text-white/50 backdrop-blur-sm focus:outline-none focus:ring-1 focus:ring-white/30 rounded-full"
          disabled={isListening}
        />
        
        {/* Magic Microphone Button inside/overlaying the right side of the input */}
        <button
          type="button"
          onClick={() => {
            if (!recognitionRef.current) {
               alert("Your browser does not support voice recognition. Please try Chrome or Edge.");
               return;
            }
            toggleListening();
          }}
          className={`absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full transition-all duration-300 ${
            isListening 
              ? "bg-red-500/20 text-red-500 animate-pulse hover:bg-red-500/30" 
              : "text-white/50 hover:bg-white/10 hover:text-white"
          }`}
          title={isListening ? "Stop listening" : "Use microphone"}
        >
          <MicIcon className="h-5 w-5" />
        </button>
      </div>
    </form>
  )
}
