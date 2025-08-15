'use client'

import GitHubActions from '../components/GitHubActions'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🧪 MCP 工具测试平台
          </h1>
          <p className="text-lg text-gray-600">
            自动化 MCP 工具完整测试，包含安装验证、功能测试和 AI 智能分析
          </p>
        </header>

        <div className="max-w-4xl mx-auto">
          <GitHubActions />
        </div>
      </div>
    </div>
  )
}
