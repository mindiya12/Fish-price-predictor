import "./globals.css";
import { Inter } from "next/font/google";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata = {
  title: "FishPrice.LK — AI-Powered Fish Price Forecast",
  description: "Get 3-day AI-powered fish price predictions for Balaya at the Peliyagoda market. Updated daily with CBSL data, weather, and fuel prices.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
      </head>
      <body style={{ minHeight: '100vh', background: '#070B14', color: '#EDF4FF', overflowX: 'hidden' }}>
        <Navbar />
        <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1.5rem' }}>
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
