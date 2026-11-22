import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MarketScope | Stock Market Data Analyzer",
  description: "An educational market analysis and strategy research dashboard.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
