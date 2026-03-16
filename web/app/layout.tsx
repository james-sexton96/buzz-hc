import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Geist_Mono, Lora } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
});

const mono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

const lora = Lora({
  variable: "--font-serif",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Buzz Healthcare Research",
  description: "Multi-agent pharma market research powered by AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${jakarta.variable} ${mono.variable} ${lora.variable} antialiased min-h-screen bg-background`}
      >
        <nav className="border-b border-border/60 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/80 sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-4 flex h-12 items-center gap-6">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-primary flex items-center justify-center">
                <span className="text-primary-foreground text-[10px] font-bold">Bz</span>
              </div>
              <span className="font-semibold text-sm tracking-tight">Buzz HC</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link
                href="/run"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Research
              </Link>
              <Link
                href="/sessions"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                History
              </Link>
            </div>
          </div>
        </nav>
        <div className="max-w-5xl mx-auto px-4 py-8">
          {children}
        </div>
      </body>
    </html>
  );
}
