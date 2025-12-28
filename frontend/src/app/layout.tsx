import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Providers } from "./providers";
import { BottomNav } from "@/components/BottomNav";
import { SkipLink } from "@/components/ui/Accessible";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Komission | 바이럴 콘텐츠 인텔리전스",
  description: "하이브리드 AI 기반 밈 진화 및 커머스 플랫폼",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} antialiased text-white`}
      >
        <SkipLink targetId="main-content" />
        <ErrorBoundary>
          <Providers>
            <main id="main-content">
              {children}
            </main>
            <BottomNav />
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  );
}
