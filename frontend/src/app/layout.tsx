import type { Metadata, Viewport } from "next";
import { Atkinson_Hyperlegible } from "next/font/google";
import Link from "next/link";
import { Header } from "@/components/Header";
import { ServiceWorker } from "@/components/ServiceWorker";
import "./globals.css";

// Designed for low-vision readers: 1, l and I, and 0 and O, cannot be mistaken. Two weights, self-hosted.
const atkinson = Atkinson_Hyperlegible({
  weight: ["400", "700"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-atkinson",
});

export const metadata: Metadata = {
  title: "VeraVote: evidence you can inspect",
  description:
    "Independent election evidence for Nigerian polling-unit results. Hackathon demo with simulated data.",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F3F5F3" },
    { media: "(prefers-color-scheme: dark)", color: "#0F1628" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={atkinson.variable}>
      <body className="min-h-screen flex flex-col antialiased font-sans text-base">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-3 focus:bg-sheet">
          Skip to content
        </a>
        <Header />
        <main id="main" className="flex-1 mx-auto w-full max-w-5xl px-4 py-8 sm:py-10">
          {children}
        </main>
        <footer className="border-t-2 border-ink text-sm">
          <div className="mx-auto max-w-5xl px-4 py-5 flex flex-col sm:flex-row gap-3 sm:justify-between">
            <p className="max-w-measure text-ink-soft">
              VeraVote checks where evidence came from and whether records agree. It does not certify results or
              declare winners.
            </p>
            <Link href="/about" className="underline font-bold">
              How we check evidence
            </Link>
          </div>
        </footer>
        <ServiceWorker />
      </body>
    </html>
  );
}
