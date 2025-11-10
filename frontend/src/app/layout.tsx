import type { Metadata } from "next";
import { Lexend } from "next/font/google";
import "./globals.css";

const lexend = Lexend({
  subsets: ["latin"],
  variable: "--font-display",
});

export const metadata: Metadata = {
  title: "EduManage - Curriculum Management",
  description: "EduManage: Visually manage and organize ideas within your curriculum.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet" />
      </head>
      <body className={`${lexend.variable} font-display bg-background-light dark:bg-background-dark`}>
        {children}
      </body>
    </html>
  );
}
