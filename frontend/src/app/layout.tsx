import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Providers } from "./providers";
import { AppShell } from "@/components/AppShell";
import { SkipLink } from "@/components/ui/Accessible";
import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages } from 'next-intl/server';

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

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} antialiased text-white`}
      >
        <SkipLink targetId="main-content" />
        <ErrorBoundary>
          <NextIntlClientProvider messages={messages}>
            <Providers>
              <AppShell>
                <main id="main-content">
                  {children}
                </main>
              </AppShell>
            </Providers>
          </NextIntlClientProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
