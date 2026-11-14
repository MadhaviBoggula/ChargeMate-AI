

"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import BrandLogo from "../../components/brand-logo";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setMessage("");
    setIsLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email.trim(),
            password,
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Login failed. Please check your details.",
        );
      }

      if (!data.access_token) {
        throw new Error("The server did not return an access token.");
      }

      // Keep the token for this browser session.
      sessionStorage.setItem(
        "chargemate_access_token",
        data.access_token,
      );

      router.push("/stations");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to connect. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#F5F9FF] px-5 py-12 text-[#10294B]">
      {/* Background decoration */}
      <div className="pointer-events-none absolute -left-40 -top-40 h-96 w-96 rounded-full bg-blue-200/40 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-32 h-96 w-96 rounded-full bg-cyan-200/40 blur-3xl" />

      <div className="relative z-10 w-full max-w-[460px]">
        <section className="overflow-hidden rounded-[30px] border border-white/80 bg-white/95 p-7 shadow-[0_25px_80px_rgba(16,41,75,0.12)] backdrop-blur-xl sm:p-10">

          {/* Brand logo */}
          <div className="mb-8 flex justify-center">
            <Link href="/" aria-label="ChargeMate AI home">
              <BrandLogo />
            </Link>
          </div>

          {/* Heading */}
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex w-fit items-center gap-2 rounded-full border border-cyan-100 bg-cyan-50 px-4 py-2">
              <span className="h-2 w-2 rounded-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.7)]" />
              <span className="text-[11px] font-bold tracking-[0.16em] text-cyan-800">
                YOUR SMART CHARGING SPACE
              </span>
            </div>

            <h1 className="font-[family-name:var(--font-plus-jakarta)] text-3xl font-extrabold tracking-tight text-[#10294B] sm:text-4xl">
              Welcome Back
            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-500">
              Sign in to your account and continue your journey with
              <span className="font-semibold text-blue-700">
                {" "}ChargeMate AI.
              </span>
            </p>
          </div>

          {/* Login form */}
          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Email */}
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="block text-sm font-bold text-[#17365D]"
              >
                Email Address
              </label>

              <div className="relative">
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email address"
                  autoComplete="email"
                  required
                  value={email}
                  disabled={isLoading}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setMessage("");
                  }}
                  className="w-full rounded-xl border border-slate-200 bg-[#FAFCFF] px-4 py-3.5 text-sm text-[#10294B] outline-none transition-all duration-300 placeholder:text-slate-400 hover:border-blue-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 disabled:opacity-60"
                />
              </div>
            </div>

            {/* Password with eye button */}
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="block text-sm font-bold text-[#17365D]"
              >
                Password
              </label>

              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                  value={password}
                  disabled={isLoading}
                  onChange={(event) => {
                    setPassword(event.target.value);
                    setMessage("");
                  }}
                  className="w-full rounded-xl border border-slate-200 bg-[#FAFCFF] px-4 py-3.5 pr-14 text-sm text-[#10294B] outline-none transition-all duration-300 placeholder:text-slate-400 hover:border-blue-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 disabled:opacity-60"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                  disabled={isLoading}
                  className="absolute right-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-400 transition-all duration-200 hover:bg-blue-50 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  {showPassword ? (
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      className="h-5 w-5"
                      aria-hidden="true"
                    >
                      <path d="M3 3l18 18" />
                      <path d="M10.6 10.6a2 2 0 002.8 2.8" />
                      <path d="M9.9 5.2A11.5 11.5 0 0112 5c5.5 0 9 7 9 7a16 16 0 01-3.2 3.9" />
                      <path d="M6.2 6.2C3.9 7.8 3 12 3 12s3.5 7 9 7a10 10 0 004.1-.9" />
                    </svg>
                  ) : (
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      className="h-5 w-5"
                      aria-hidden="true"
                    >
                      <path d="M2.5 12s3.5-7 9.5-7 9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>

              <p className="text-xs text-slate-400">
                Enter the password associated with your account.
              </p>
            </div>

            {/* API error message */}
            {message && (
              <div
                role="alert"
                className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm leading-5 text-red-700"
              >
                {message}
              </div>
            )}

            {/* Sign in button */}
            <button
              type="submit"
              disabled={isLoading}
              className="group relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-blue-700 via-blue-600 to-cyan-600 px-5 py-4 text-sm font-bold text-white shadow-lg shadow-blue-600/25 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-blue-600/35 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-500/25 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-70"
            >
              <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
              <span className="relative">
                {isLoading ? "Signing In..." : "Sign In to ChargeMate"}
              </span>
              <span className="relative transition-transform duration-300 group-hover:translate-x-1">
                {isLoading ? "..." : "→"}
              </span>
            </button>
          </form>

          {/* Register link */}
          <div className="mt-8 text-center">
            <p className="text-sm text-slate-500">
              Don't have an account?
            </p>

            <Link
              href="/register"
              className="group relative mt-2 inline-flex items-center gap-1 text-sm font-bold text-blue-700 transition-all duration-300 hover:scale-[1.03] hover:text-cyan-700"
            >
              <span>Create an Account</span>
              <span className="transition-transform duration-300 group-hover:translate-x-1">
                →
              </span>
              <span className="absolute -bottom-1 left-0 h-0.5 w-full origin-left scale-x-0 rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 transition-transform duration-300 group-hover:scale-x-100" />
            </Link>
          </div>

          {/* Back to home */}
          <div className="mt-7 border-t border-slate-100 pt-6 text-center">
            <Link
              href="/"
              className="group inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition-all duration-300 hover:font-bold hover:text-blue-700"
            >
              <span className="transition-transform duration-300 group-hover:-translate-x-1">
                ←
              </span>
              <span>Back to Home</span>
            </Link>
          </div>
        </section>

        <p className="mt-6 text-center text-xs font-medium tracking-wide text-slate-400">
          © 2026 ChargeMate AI. Intelligent EV charging.
        </p>
      </div>
    </main>
  );
}
