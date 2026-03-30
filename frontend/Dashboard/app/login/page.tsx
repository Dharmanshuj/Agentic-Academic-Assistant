import { LoginForm } from "@/components/login-form"
import { DotPattern } from "@/components/ui/dot-pattern"

export default function LoginPage() {
  return (
    <DotPattern>
      <div className="flex min-h-svh flex-col items-center justify-center gap-6 p-6 md:p-10 text-black">
        <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl">
          <LoginForm />
        </div>
      </div>
    </DotPattern>
  )
}
