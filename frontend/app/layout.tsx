import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Batch MCP Testing Platform',
  description: '动态 MCP 工具部署和测试框架',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body suppressHydrationWarning={true}>{children}</body>
    </html>
  )
}
