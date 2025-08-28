import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Solution Agent',
  description: 'Multi-agent solution writing system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-background text-foreground">
        {children}
      </body>
    </html>
  )
}