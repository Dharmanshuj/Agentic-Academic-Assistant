"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { GalleryVerticalEnd, Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function LoginForm({ className, ...props }: React.ComponentPropsWithoutRef<"div">) {
  const router = useRouter()
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
    // TODO: Replace with real authentication call to your backend
    // 1. Get the form data
    const formData = new FormData(e.currentTarget)
    // FastAPI's OAuth2PasswordRequestForm specifically requires the field to be named "username"
    const username = formData.get("empno") as string
    const password = formData.get("password") as string

    try {
      // 2. Fetch from your backend endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ username, password }),
      })

      // 3. Handle the response
      if (!response.ok) {
        // FastAPI usually sends {"detail": "Error message"}
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail || "Invalid employee number or password.")
      }
      const data = await response.json()
      console.log("Login successful:", data)

      // Save the JWT token to authenticate API calls in the dashboard
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token)
      }

      setErrorMsg(null) // Clear any previous errors

      // Use replace instead of push so the user can't click "Back" to return to login
      router.replace("/dashboard")
    }
    catch (error: any) {
      console.error("Error logging in:", error)
      setErrorMsg(error.message)
      setIsLoading(false)
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <form onSubmit={handleSubmit}>
        <div className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-2">
            <a href="#" className="flex flex-col items-center gap-2 font-medium">
              <div className="flex h-8 w-8 items-center justify-center rounded-md">
                <GalleryVerticalEnd className="size-6" />
              </div>
              <span className="sr-only">NIT Jalandhar</span>
            </a>
            <h1 className="text-xl font-bold">Welcome to NIT Jalandhar</h1>
            {/* <div className="text-center text-sm">
              Don&apos;t have an account?{" "}
              <a href="#" className="underline underline-offset-4">
                Sign up
              </a>
            </div> */}
          </div>
          <div className="flex flex-col gap-6">
            {errorMsg && (
              <div className="text-sm font-medium text-destructive text-center bg-destructive/10 p-3 rounded-md">
                {errorMsg}
              </div>
            )}
            <div className="grid gap-2">
              <Label htmlFor="empno">Roll Number</Label>
              <Input id="empno" name="empno" type="text" placeholder="21103001" required />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center">
                <Label htmlFor="password">Password</Label>
              </div>
              <Input id="password" name="password" type="password" required />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Please wait
                </>
              ) : (
                "Login"
              )}
            </Button>
          </div>
        </div>
      </form>
      <div className="text-balance text-center text-xs text-muted-foreground [&_a]:underline [&_a]:underline-offset-4 hover:[&_a]:text-primary">
        By clicking continue, you agree to our <a href="https://www.nitj.ac.in" target="_blank" rel="noopener noreferrer">Terms of Service</a> and <a href="https://www.nitj.ac.in" target="_blank" rel="noopener noreferrer">Privacy Policy</a>.
      </div>
    </div>
  )
}
