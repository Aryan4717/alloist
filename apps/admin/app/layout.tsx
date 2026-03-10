import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/AuthProvider";
import { Nav } from "@/components/Nav";
import { RequireOrg } from "@/components/RequireOrg";
import { QuickstartOverlay } from "@/components/QuickstartOverlay";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Alloist Admin",
  description: "Admin console for policies, tokens, and evidence",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <AuthProvider>
          <div className="min-h-screen bg-background">
            <Nav />
            <main className="mx-auto max-w-6xl px-4 py-8">
              <RequireOrg>{children}</RequireOrg>
            </main>
            <QuickstartOverlay />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
