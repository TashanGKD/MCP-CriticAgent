'use client'

import { useState, useEffect } from 'react'
import IntegratedTestForm from '../components/IntegratedTestForm'

interface TestStatus {
  testMode: 'vercel' | 'github'
  status: string
  message?: string
  progress?: number
  runId?: string
  startTime?: number
}

interface TestResult {
  success: boolean
  testMode: 'vercel' | 'github'
  data?: any
  error?: string
  duration?: number
}

export default function Home() {
  const [isTestRunning, setIsTestRunning] = useState(false)
  const [testStatus, setTestStatus] = useState<TestStatus | null>(null)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null)

  // 清理定时器
  useEffect(() => {
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval)
      }
    }
  }, [statusCheckInterval])

  // GitHub Actions 状态轮询
  const pollGitHubStatus = async (runId: string) => {
    try {
      const response = await fetch(`/api/github-test-status?run_id=${runId}`)
      const data = await response.json()
      
      if (data.success) {
        // 更新状态
        setTestStatus(prev => ({
          ...prev!,
          status: data.status,
          message: data.message,
          progress: getProgressFromStatus(data.status, data.conclusion)
        }))

        // 如果完成，停止轮询并显示结果
        if (data.status === 'completed') {
          if (statusCheckInterval) {
            clearInterval(statusCheckInterval)
            setStatusCheckInterval(null)
          }

          setIsTestRunning(false)
          setTestStatus(null)
          
          setTestResult({
            success: data.conclusion === 'success',
            testMode: 'github',
            data: data.test_results || data,
            duration: Date.now() - (testStatus?.startTime || Date.now())
          })
        }
      }
    } catch (error) {
      console.error('状态轮询失败:', error)
    }
  }

  // 根据状态计算进度
  const getProgressFromStatus = (status: string, conclusion?: string) => {
    switch (status) {
      case 'queued': return 10
      case 'in_progress': return 60
      case 'completed': return conclusion === 'success' ? 100 : 95
      default: return 0
    }
  }

  // 开始测试
  const handleStartTest = async (url: string, testMode: 'vercel' | 'github', options: any) => {
    setIsTestRunning(true)
    setTestResult(null)
    setTestStatus({
      testMode,
      status: 'starting',
      message: '正在启动测试...',
      progress: 5,
      startTime: Date.now()
    })

    try {
      if (testMode === 'vercel') {
        // Vercel 快速测试
        setTestStatus(prev => ({
          ...prev!,
          status: 'running',
          message: '正在执行基础MCP测试...',
          progress: 50
        }))

        const response = await fetch('/api/test-mcp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, ...options })
        })

        const result = await response.json()
        
        setIsTestRunning(false)
        setTestStatus(null)
        setTestResult({
          success: result.success,
          testMode: 'vercel',
          data: result,
          duration: Date.now() - (testStatus?.startTime || Date.now())
        })

      } else if (testMode === 'github') {
        // GitHub Actions AI增强测试
        const runId = `api-test-${Date.now()}`
        
        setTestStatus(prev => ({
          ...prev!,
          status: 'triggering',
          message: '正在触发GitHub Actions...',
          progress: 15,
          runId
        }))

        const response = await fetch('/api/trigger-github-test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url,
            timeout: options.timeout,
            enable_ai: options.smart || true
          })
        })

        const triggerResult = await response.json()
        
        if (triggerResult.success) {
          setTestStatus(prev => ({
            ...prev!,
            status: 'queued',
            message: 'GitHub Actions已启动，等待执行...',
            progress: 25,
            runId: triggerResult.run_id
          }))

          // 开始状态轮询
          const interval = setInterval(() => {
            pollGitHubStatus(triggerResult.run_id)
          }, 10000) // 每10秒轮询一次

          setStatusCheckInterval(interval)
        } else {
          throw new Error(triggerResult.error || 'GitHub Actions启动失败')
        }
      }

    } catch (error) {
      setIsTestRunning(false)
      setTestStatus(null)
      setTestResult({
        success: false,
        testMode,
        error: error instanceof Error ? error.message : '测试启动失败',
        duration: Date.now() - (testStatus?.startTime || Date.now())
      })
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* 页头 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            MCP 工具测试平台
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            支持快速验证和AI增强深度测试的双模式MCP工具测试平台。
            选择适合您需求的测试模式，享受完全自动化的测试体验。
          </p>
        </div>

        {/* 功能特色展示 */}
        {!isTestRunning && !testResult && (
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                  <span className="text-2xl">⚡</span>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">Vercel 快速测试</h3>
                  <p className="text-sm text-gray-600">30秒内完成基础验证</p>
                </div>
              </div>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 连接性测试</li>
                <li>• 工具列表验证</li>
                <li>• 基础功能检查</li>
              </ul>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
                  <span className="text-2xl">🤖</span>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">GitHub Actions AI测试</h3>
                  <p className="text-sm text-gray-600">5-10分钟AI深度分析</p>
                </div>
              </div>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• AI智能分析</li>
                <li>• 性能基准测试</li>
                <li>• 详细优化建议</li>
              </ul>
            </div>
          </div>
        )}

        {/* 测试表单 */}
        <IntegratedTestForm
          onStartTest={handleStartTest}
          disabled={isTestRunning}
          currentStatus={testStatus || undefined}
        />

        {/* 测试结果显示 */}
        {testResult && (
          <div className="mt-8">
            <div className={`bg-white rounded-lg shadow-lg p-6 border-l-4 ${
              testResult.success ? 'border-green-500' : 'border-red-500'
            }`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-800">
                  {testResult.testMode === 'github' ? 'GitHub Actions' : 'Vercel'} 测试结果
                </h3>
                <div className="flex items-center space-x-4">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    testResult.success 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {testResult.success ? '成功' : '失败'}
                  </span>
                  {testResult.duration && (
                    <span className="text-sm text-gray-500">
                      耗时: {Math.round(testResult.duration / 1000)}秒
                    </span>
                  )}
                </div>
              </div>

              {testResult.success ? (
                <div className="space-y-4">
                  {testResult.data && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-800 mb-2">测试详情</h4>
                      <pre className="text-xs text-gray-600 overflow-auto">
                        {JSON.stringify(testResult.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-red-600">
                  <p className="font-medium">错误信息:</p>
                  <p className="text-sm">{testResult.error}</p>
                </div>
              )}

              <div className="mt-4 flex space-x-3">
                <button
                  onClick={() => setTestResult(null)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                >
                  运行新测试
                </button>
                {testResult.testMode === 'github' && testResult.data?.workflow_url && (
                  <a
                    href={testResult.data.workflow_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    查看详细日志
                  </a>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 底部说明 */}
        <div className="mt-12 text-center text-sm text-gray-500">
          <p>
            Powered by <strong>Next.js</strong> + <strong>Vercel</strong> + <strong>GitHub Actions</strong>
          </p>
          <p className="mt-1">
            支持完全自动化的双模式MCP工具测试
          </p>
        </div>
      </div>
    </div>
  )
}
