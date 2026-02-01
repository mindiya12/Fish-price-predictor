import "./globals.css";
import { Inter, Poppins } from "next/font/google";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const poppins = Poppins({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-poppins",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${poppins.variable}`}>
      <body className="min-h-screen bg-brand-background font-[var(--font-inter)] text-slate-900 overflow-x-hidden">
        <Navbar />
        <main className="mx-auto w-full max-w-6xl px-4 py-6">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
