import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { AppProviders } from "./providers";

export const metadata: Metadata = {
  description: "人とのつながりを思い出し、育てるためのNetwork Compass",
  title: "Network Compass",
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ja">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
