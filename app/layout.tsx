import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgriScope Earth — Global Agricultural Intelligence",
  description: "A Python-first global research console for flood exposure, crop stress, land change, irrigation, agricultural carbon, fire and heat.",
  icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
  other: { "codex-preview": "development" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
