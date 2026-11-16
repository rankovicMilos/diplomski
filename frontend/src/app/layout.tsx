import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css"
import Header from "../components/Header/Header";
import { NuqsAdapter } from "nuqs/adapters/next";
import ThemeWrapper from "../components/ThemeWrapper/ThemeWrapper";
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
            <main className="flex justify-center px-4 md:px-8 flex-1 overflow-visible">
              <QueryClientProvider>
                <div className="w-full max-w-[1200px] min-w-0 py-8">
                  {children}
                </div>
              </QueryClientProvider>
            </main>
          </body>
        </ThemeWrapper>
      </NuqsAdapter>
    </html>
  );
}
