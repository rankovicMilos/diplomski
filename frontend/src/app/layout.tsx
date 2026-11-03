import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css"
import Header from "../components/Header/Header";
import Navigation from "../components/Navigation/Navigation";
import { NuqsAdapter } from "nuqs/adapters/next";
import ThemeWrapper from "../components/ThemeWrapper/ThemeWrapper";
import { Suspense } from "react";
import QueryClientProvider from "../components/Providers/QueryClientProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Analiza sektorskog rizika",
  description: "Analiza sektora i kreditnog rizika uz pomoć veštačke inteligencije (diplomski rad)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="sr-Latn" className="[scrollbar-gutter:stable]">
      <NuqsAdapter>
        <ThemeWrapper>
          <body
            className={`${geistSans.variable} ${geistMono.variable} antialiased flex flex-col min-h-screen`}
          >
            <Header />
            <main className="flex justify-center px-16 flex-1 overflow-visible">
              <QueryClientProvider>
                <div className="lg:max-w-[1600px] flex gap-10 justify-space-between grow flex-1 grow-1 bg-white-100">
                  <Suspense>
                    <Navigation />
                  </Suspense>
                  <div className="w-full h-full py-8 px-4">
                    {children}
                  </div>
                </div>
              </QueryClientProvider>
            </main>
          </body>
        </ThemeWrapper>
      </NuqsAdapter>
    </html>
  );
}
