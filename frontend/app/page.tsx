
import Image from "next/image";
import Link from "next/link";
import BrandLogo from "../components/brand-logo";

const features = [
  {
    number: "01",
    icon: "⌖",
    title: "Driver Station Discovery",
    description:
      "Search charging stations by locality or city. Filter results by connector type, charger type, power, price and status. Find stations compatible with your registered vehicle.",
    href: "/stations",
    action: "Explore stations",
  },
  {
    number: "02",
    icon: "◷",
    title: "Availability & Preferences",
    description:
      "Check simulated charger availability, manage your charging preferences, save favourite stations and manage your registered vehicles.",
    href: "/stations",
    action: "Explore driver features",
  },
  {
    number: "03",
    icon: "⚡",
    title: "Owner Station Management",
    description:
      "View your stations, create and update station details, explore charger and connector information, and manage charger status and charging prices.",
    href: "/owner",
    action: "Explore management",
  },
  {
    number: "04",
    icon: "✦",
    title: "AI Assistant & Analytics",
    description:
      "Ask role-specific EV charging questions, access knowledge-grounded answers, use permitted AI actions and explore simulated operational and revenue metrics.",
    href: "/assistant",
    action: "Meet your assistant",
  },
];

const steps = [
  {
    number: "01",
    icon: "👤",
    title: "Create Your Account",
    description:
      "Register or sign in securely as an EV driver or charging station owner.",
  },
  {
    number: "02",
    icon: "⌖",
    title: "Access Your Workspace",
    description:
      "Explore the features and information available for your account role.",
  },
  {
    number: "03",
    icon: "✦",
    title: "Experience AI Assistance",
    description:
      "Ask questions, explore relevant information and use permitted assistant capabilities.",
  },
];

const benefits = [
  {
    icon: "🔐",
    title: "Secure Access",
    description:
      "Protected accounts, secure authentication and role-aware access to application features.",
  },
  {
    icon: "🛡️",
    title: "Privacy & Control",
    description:
      "Personal records and conversations remain restricted to their authenticated users.",
  },
  {
    icon: "✦",
    title: "Intelligent Assistance",
    description:
      "Role-specific knowledge retrieval and validated application actions through AI workflows.",
  },
];

const navClass =
  "group relative text-sm font-semibold text-slate-600 transition-colors duration-300 hover:text-blue-700 after:absolute after:-bottom-2 after:left-0 after:h-0.5 after:w-full after:origin-left after:scale-x-0 after:rounded-full after:bg-gradient-to-r after:from-blue-600 after:to-cyan-400 after:transition-transform after:duration-300 hover:after:scale-x-100";

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#F5F9FF] text-[#10294B]">

      {/* HEADER */}
      <header className="sticky top-0 z-50 border-b border-blue-100/80 bg-white/95 shadow-sm backdrop-blur-xl">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-10">

          <Link href="/" aria-label="ChargeMate AI home">
            <BrandLogo />
          </Link>

          <div className="hidden items-center gap-8 md:flex">
            <Link href="/" className={navClass}>
              Home
            </Link>

            <Link href="/stations" className={navClass}>
              Stations
            </Link>

            <a href="#features" className={navClass}>
              Features
            </a>

            <a href="#about" className={navClass}>
              About
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden rounded-xl px-4 py-2.5 text-sm font-bold text-[#17365D] transition-all duration-300 hover:bg-blue-50 hover:text-blue-700 sm:inline-flex"
            >
              Login
            </Link>

            <Link
              href="/register"
              className="rounded-xl bg-gradient-to-r from-blue-700 to-blue-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-blue-600/20 transition-all duration-300 hover:-translate-y-0.5 hover:from-blue-800 hover:to-cyan-600 hover:shadow-xl hover:shadow-blue-600/30"
            >
              Register <span className="ml-1">→</span>
            </Link>
          </div>
        </nav>
      </header>

      {/* HERO */}
      <section className="relative isolate min-h-[680px] overflow-hidden bg-[#10294B] sm:min-h-[720px]">

        <Image
          src="/images/charging-station.jpg"
          alt="Outdoor electric vehicle charging station"
          fill
          priority
          sizes="100vw"
          className="object-cover object-center"
        />

        {/* Natural image lighting with a reduced blue overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#07182F]/45 via-[#10294B]/15 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#07182F]/15 via-transparent to-transparent" />

        <div className="relative mx-auto flex min-h-[680px] max-w-7xl items-center px-6 py-20 sm:min-h-[720px] lg:px-10">

          <div className="max-w-2xl text-white">

            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-4 py-2 text-xs font-bold tracking-[0.18em] text-white shadow-lg backdrop-blur-md">
              <span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_12px_#22D3EE]" />
              THE FUTURE OF EV CHARGING
            </div>

            <h1 className="font-[family-name:var(--font-plus-jakarta)] text-5xl leading-[1.1] font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
              Your EV.
              <br />
              Your Station.
              <br />
              <span className="bg-gradient-to-r from-cyan-200 via-cyan-300 to-blue-300 bg-clip-text text-transparent">
                Your Charge.
              </span>
            </h1>

            <p className="mt-7 max-w-xl text-base leading-8 text-white/90 sm:text-lg">
              Discover charging stations, explore charger information and
              experience intelligent EV charging assistance with ChargeMate AI.
            </p>

            <div className="mt-9 flex flex-wrap gap-4">

              <Link
                href="/stations"
                className="group relative inline-flex items-center gap-3 overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-7 py-4 text-sm font-bold text-white shadow-xl shadow-blue-950/30 transition-all duration-300 hover:-translate-y-1 hover:from-blue-700 hover:to-cyan-600 hover:shadow-[0_0_30px_rgba(34,211,238,0.35)]"
              >
                <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
                <span className="relative">Find a Charging Station</span>
                <span className="relative transition-transform group-hover:translate-x-1">→</span>
              </Link>

              <a
                href="#features"
                className="group relative inline-flex items-center gap-3 overflow-hidden rounded-xl border border-white/50 bg-white/10 px-7 py-4 text-sm font-bold text-white backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-cyan-200 hover:bg-white/20 hover:shadow-[0_0_25px_rgba(34,211,238,0.3)]"
              >
                Explore Features
                <span className="transition-transform duration-300 group-hover:translate-x-1">→</span>
              </a>
            </div>

            <div className="mt-12 flex flex-wrap gap-x-9 gap-y-5 border-t border-white/25 pt-7">

              <div>
                <p className="text-2xl font-extrabold text-white">AI</p>
                <p className="mt-1 text-xs text-white/80">
                  Intelligent assistance
                </p>
              </div>

              <div>
                <p className="text-2xl font-extrabold text-white">EV</p>
                <p className="mt-1 text-xs text-white/80">
                  Smarter mobility
                </p>
              </div>

              <div>
                <p className="text-2xl font-extrabold text-white">24/7</p>
                <p className="mt-1 text-xs text-white/80">
                  Digital convenience
                </p>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="bg-white px-6 py-24 lg:px-10">
        <div className="mx-auto max-w-7xl">

          <div className="max-w-2xl">
            <p className="text-xs font-extrabold tracking-[0.22em] text-blue-700">
              YOUR CHARGING EXPERIENCE
            </p>

            <h2 className="mt-4 font-[family-name:var(--font-plus-jakarta)] text-3xl font-extrabold tracking-tight text-[#10294B] sm:text-4xl">
              Everything You Need.
              <span className="block bg-gradient-to-r from-blue-700 to-cyan-500 bg-clip-text text-transparent">
                One Smart Platform.
              </span>
            </h2>

            <p className="mt-5 max-w-xl leading-7 text-slate-500">
              Purpose-built tools for EV drivers and charging station owners,
              supported by intelligent AI assistance.
            </p>
          </div>

          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">

            {features.map((feature) => (
              <article
                key={feature.number}
                className="group relative isolate flex flex-col overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-br from-white via-white to-[#F0F7FF] p-7 shadow-[0_5px_25px_rgba(30,64,175,0.04)] transition-all duration-500 hover:-translate-y-3 hover:border-blue-300 hover:shadow-[0_25px_65px_rgba(37,99,235,0.16)]"
              >
                <div className="absolute left-0 top-0 h-1 w-full origin-left scale-x-0 bg-gradient-to-r from-blue-600 to-cyan-400 transition-transform duration-500 group-hover:scale-x-100" />

                <div className="flex items-center justify-between">

                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-100 to-cyan-50 text-3xl text-blue-700 shadow-inner transition-all duration-500 group-hover:rotate-6 group-hover:scale-110 group-hover:from-blue-600 group-hover:to-cyan-500 group-hover:text-white">
                    {feature.icon}
                  </div>

                  <span className="text-sm font-extrabold tracking-wider text-blue-200 transition-colors group-hover:text-blue-500">
                    {feature.number}
                  </span>
                </div>

                <h3 className="mt-7 text-lg font-extrabold text-[#17365D] transition-colors group-hover:text-blue-700">
                  {feature.title}
                </h3>

                <p className="mt-3 flex-1 text-sm leading-7 text-slate-500">
                  {feature.description}
                </p>

                <Link
                  href={feature.href}
                  className="mt-7 inline-flex items-center gap-2 text-sm font-bold text-blue-700 transition-all duration-300 group-hover:gap-4"
                >
                  {feature.action}
                  <span>→</span>
                </Link>
              </article>
            ))}

          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-gradient-to-b from-[#F5F9FF] to-white px-6 py-24 lg:px-10">
        <div className="mx-auto max-w-7xl">

          <div className="text-center">
            <p className="text-xs font-extrabold tracking-[0.22em] text-blue-700">
              SIMPLE BY DESIGN
            </p>

            <h2 className="mt-4 font-[family-name:var(--font-plus-jakarta)] text-3xl font-extrabold text-[#10294B] sm:text-4xl">
              Your ChargeMate AI Experience
            </h2>

            <p className="mx-auto mt-4 max-w-xl leading-7 text-slate-500">
              A straightforward experience designed around your account and
              the tools available to your role.
            </p>
          </div>

          <div className="mt-14 grid gap-6 rounded-[2rem] border border-blue-100 bg-white/80 p-5 shadow-[0_24px_70px_rgba(30,64,175,0.08)] backdrop-blur sm:p-8 md:grid-cols-3">

            {steps.map((step) => (
              <div
                key={step.number}
                className="group relative rounded-3xl border border-slate-100 bg-gradient-to-b from-white to-blue-50/70 p-8 text-center shadow-sm transition-all duration-300 hover:-translate-y-2 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-900/10"
              >
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-700 to-cyan-500 text-2xl text-white shadow-lg shadow-blue-600/20 transition-transform duration-300 group-hover:scale-110">
                  {step.icon}
                </div>

                <p className="mt-5 text-xs font-extrabold tracking-[0.2em] text-blue-500">
                  STEP {step.number}
                </p>

                <h3 className="mt-3 text-lg font-extrabold text-[#17365D]">
                  {step.title}
                </h3>

                <p className="mx-auto mt-3 max-w-xs text-sm leading-7 text-slate-500">
                  {step.description}
                </p>
              </div>
            ))}

          </div>
        </div>
      </section>

      {/* BENEFITS */}
      <section id="about" className="bg-white px-6 py-24 lg:px-10">
        <div className="mx-auto max-w-7xl">

          <div className="text-center">
            <p className="text-xs font-extrabold tracking-[0.22em] text-blue-700">
              BUILT WITH TRUST
            </p>

            <h2 className="mt-4 font-[family-name:var(--font-plus-jakarta)] text-3xl font-extrabold text-[#10294B] sm:text-4xl">
              Intelligent. Secure. Role-Aware.
            </h2>

            <p className="mx-auto mt-4 max-w-xl leading-7 text-slate-500">
              A dependable platform designed with secure access, user privacy
              and intelligent assistance at its core.
            </p>
          </div>

          <div className="mt-14 grid gap-6 md:grid-cols-3">

            {benefits.map((benefit) => (
              <div
                key={benefit.title}
                className="group relative overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-br from-white to-blue-50/70 p-9 text-center shadow-sm transition-all duration-500 hover:-translate-y-2 hover:border-blue-200 hover:shadow-[0_20px_55px_rgba(37,99,235,0.13)]"
              >
                <div className="absolute inset-x-0 top-0 h-1 origin-left scale-x-0 bg-gradient-to-r from-blue-600 to-cyan-400 transition-transform duration-500 group-hover:scale-x-100" />

                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-100 to-cyan-50 text-3xl shadow-inner transition-all duration-300 group-hover:scale-110 group-hover:from-blue-600 group-hover:to-cyan-500">
                  {benefit.icon}
                </div>

                <h3 className="mt-6 text-xl font-extrabold text-[#17365D] transition-colors group-hover:text-blue-700">
                  {benefit.title}
                </h3>

                <p className="mt-3 text-sm leading-7 text-slate-500">
                  {benefit.description}
                </p>
              </div>
            ))}

          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-20 lg:px-10">
        <div className="relative mx-auto max-w-7xl overflow-hidden rounded-[2rem] bg-gradient-to-br from-[#10294B] via-[#123C70] to-[#075985] px-8 py-16 text-center text-white shadow-2xl shadow-blue-950/15 sm:px-14">

          <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
          <div className="absolute -bottom-24 -left-20 h-72 w-72 rounded-full bg-blue-400/20 blur-3xl" />

          <div className="relative mx-auto max-w-2xl">

            <p className="text-xs font-extrabold tracking-[0.22em] text-cyan-300">
              YOUR JOURNEY STARTS HERE
            </p>

            <h2 className="mt-5 font-[family-name:var(--font-plus-jakarta)] text-3xl font-extrabold sm:text-4xl">
              Power Your Journey with ChargeMate AI
            </h2>

            <p className="mt-5 leading-8 text-blue-100/90">
              Discover a smarter way to explore EV charging information and
              manage your charging experience with intelligent assistance.
            </p>

            <div className="mt-9 flex flex-wrap justify-center gap-4">

              <div className="flex min-w-[230px] flex-col items-center gap-2">
                <Link
                  href="/register"
                  className="group inline-flex w-full items-center justify-center gap-3 rounded-xl border-2 border-cyan-200 bg-cyan-500 px-7 py-4 text-sm font-extrabold text-white shadow-[0_10px_30px_rgba(6,182,212,0.35)] transition-all duration-300 hover:-translate-y-1 hover:border-cyan-100 hover:bg-cyan-400 hover:shadow-[0_14px_35px_rgba(6,182,212,0.45)]"
                >
                  Create Your Account
                  <span className="transition-transform group-hover:translate-x-1">→</span>
                </Link>

                <span className="text-xs font-medium text-white/90">
                  New to ChargeMate AI?
                </span>
              </div>

              <div className="flex min-w-[230px] flex-col items-center gap-2">
                <Link
                  href="/login"
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl border-2 border-white/75 bg-[#10294B]/70 px-7 py-4 text-sm font-bold text-white shadow-lg backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-white hover:bg-[#173D68]"
                >
                  Already have an account? Login
                </Link>

                <span className="text-xs font-medium text-white/90">
                  Sign in to your existing account
                </span>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-blue-100 bg-white px-6 py-9 lg:px-10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 sm:flex-row">

          <BrandLogo compact />

          <p className="text-center text-xs text-slate-400">
            © 2026 ChargeMate AI. Intelligent EV charging.
          </p>

          <div className="flex gap-6 text-xs font-semibold text-slate-500">
            <Link href="/login" className="transition hover:text-blue-700">
              Login
            </Link>

            <Link href="/register" className="transition hover:text-blue-700">
              Register
            </Link>
          </div>

        </div>
      </footer>

    </main>
  );
}
