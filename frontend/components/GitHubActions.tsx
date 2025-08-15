'use client'

import { useState } from 'react'

interface GitHubActionsProps {
  className?: string
}

interface WorkflowRun {
  id: number
  name: string
  status: string
  conclusion: string | null
  created_at: string
  html_url: string
  run_number: number
  head_commit?: {
    message: string
  }
}

interface TestResult {
  status: string
  summary: string
  details?: {
    tool_name?: string
    install_success?: boolean
    function_test?: boolean
    test_duration?: number
    ai_model?: string
    test_mode?: string
    start_time?: string
    end_time?: string
    total_tests?: number
    passed_tests?: number
    failed_tests?: number
    error_message?: string
  }
  report_url?: string
}

export default function GitHubActions({ className = '' }: GitHubActionsProps) {
  const [isTriggering, setIsTriggering] = useState(false)
  const [workflowRuns, setWorkflowRuns] = useState<WorkflowRun[]>([])
  const [lastRunId, setLastRunId] = useState<string>('')
  const [testResults, setTestResults] = useState<{[key: string]: TestResult}>({})
  const [triggerResult, setTriggerResult] = useState<{
    success: boolean
    message: string
    run_id?: string
  } | null>(null)

  const [formData, setFormData] = useState({
    github_url: ''
  })

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }))
  }

  const triggerWorkflow = async () => {
    setIsTriggering(true)
    setTriggerResult(null)

    try {
      const response = await fetch('/api/trigger-github-workflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (data.success) {
        setTriggerResult({
          success: true,
          message: 'MCP 工具测试已成功启动！',
          run_id: data.run_id
        })
        setLastRunId(data.run_id)
        
        // 3秒后自动刷新状态
        setTimeout(() => {
          fetchWorkflowStatus()
        }, 3000)
      } else {
        setTriggerResult({
          success: false,
          message: data.error || '触发失败'
        })
      }
    } catch (error) {
      setTriggerResult({
        success: false,
        message: '网络请求失败'
      })
    } finally {
      setIsTriggering(false)
    }
  }

  const fetchWorkflowStatus = async () => {
    try {
      const url = lastRunId 
        ? `/api/workflow-status?run_id=${lastRunId}&limit=5`
        : '/api/workflow-status?limit=5'
        
      const response = await fetch(url)
      const data = await response.json()

      if (data.success) {
        setWorkflowRuns(data.runs)
        
        // 为完成的工作流获取测试结果
        for (const run of data.runs) {
          if (run.status === 'completed' && run.conclusion === 'success') {
            await fetchTestResult(run.id)
          }
        }
      }
    } catch (error) {
      console.error('获取工作流状态失败:', error)
    }
  }

  const fetchTestResult = async (runId: number) => {
    try {
      // 尝试获取GitHub Pages上的结果
      const pageUrl = `https://gqy22.github.io/batch_mcp/test-results/${runId}.json`
      const response = await fetch(pageUrl)
      
      if (response.ok) {
        const result = await response.json()
        setTestResults(prev => ({
          ...prev,
          [runId]: {
            status: result.summary?.overall_success ? 'success' : 'failed',
            summary: `${result.tool_info?.name || '未知工具'} - 测试完成`,
            details: {
              tool_name: result.tool_info?.name || '未知工具',
              install_success: result.deployment_success,
              function_test: result.communication_success,
              test_duration: Math.round(result.test_duration_seconds || 0),
              ai_model: '无AI模型调用',
              test_mode: '标准MCP协议测试',
              start_time: result.test_time,
              end_time: result.test_time,
              total_tests: result.summary?.test_count || 0,
              passed_tests: result.summary?.passed_tests || 0,
              failed_tests: result.summary?.failed_tests || 0,
              error_message: result.error_messages?.join(', ') || null
            },
            report_url: `https://gqy22.github.io/batch_mcp/`
          }
        }))
      } else {
        // 如果无法获取实际结果，只显示基本状态
        setTestResults(prev => ({
          ...prev,
          [runId]: {
            status: 'completed',
            summary: '测试已完成，正在生成详细报告...',
            report_url: `https://gqy22.github.io/batch_mcp/`
          }
        }))
      }
    } catch (error) {
      console.error('获取测试结果失败:', error)
      // 如果获取失败，不显示任何模拟数据
      setTestResults(prev => ({
        ...prev,
        [runId]: {
          status: 'failed',
          summary: '无法获取测试结果，请查看GitHub Actions日志',
          report_url: `https://gqy22.github.io/batch_mcp/`
        }
      }))
    }
  }

  const getStatusBadge = (status: string, conclusion: string | null) => {
    if (status === 'completed') {
      if (conclusion === 'success') {
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
            测试成功
          </span>
        )
      } else if (conclusion === 'failure') {
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
            <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
            测试失败
          </span>
        )
      } else {
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-800 border border-gray-200">
            <span className="w-2 h-2 bg-gray-500 rounded-full mr-2"></span>
            已完成
          </span>
        )
      }
    } else if (status === 'in_progress') {
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
          <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></span>
          运行中
        </span>
      )
    } else {
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-200">
          <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
          排队中
        </span>
      )
    }
  }

  return (
    <div className={`space-y-8 ${className}`}>
      {/* 测试启动卡片 */}
      <div className="bg-white rounded-xl p-8 shadow-lg border border-gray-100">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-4">
            <span className="text-2xl">🧪</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            MCP 工具智能测试
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            自动化 MCP 工具完整测试，包含安装验证、功能测试和 AI 智能分析，生成详细的测试报告
          </p>
        </div>
        
        <div className="max-w-2xl mx-auto">
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              🎯 MCP 工具 GitHub 仓库地址
            </label>
            <input
              type="url"
              name="github_url"
              value={formData.github_url}
              onChange={handleInputChange}
              placeholder="https://github.com/username/mcp-tool"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white placeholder-gray-400 transition-all duration-200"
            />
            <p className="text-sm text-gray-500 mt-2">
              输入要测试的 MCP 工具的 GitHub 仓库 URL，我们将自动进行全面的兼容性测试
            </p>
          </div>

          <div className="flex justify-center space-x-4">
            <button
              onClick={triggerWorkflow}
              disabled={isTriggering}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-3 px-8 rounded-lg transition-all duration-200 flex items-center shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:hover:translate-y-0"
            >
              {isTriggering ? (
                <>
                  <div className="animate-spin mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                  测试进行中...
                </>
              ) : (
                <>
                  <span className="mr-3 text-lg">🚀</span>
                  开始智能测试
                </>
              )}
            </button>

            <button
              onClick={fetchWorkflowStatus}
              className="bg-white hover:bg-gray-50 border border-gray-300 text-gray-700 font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center hover:shadow-md"
            >
              <span className="mr-2">🔄</span>
              刷新状态
            </button>
          </div>

          {/* 触发结果消息 */}
          {triggerResult && (
            <div className={`mt-6 p-4 rounded-lg border ${
              triggerResult.success 
                ? 'bg-green-50 border-green-200 text-green-800' 
                : 'bg-red-50 border-red-200 text-red-800'
            }`}>
              <div className="flex items-center">
                <span className="mr-2 text-lg">
                  {triggerResult.success ? '✅' : '❌'}
                </span>
                <div>
                  <p className="font-medium">{triggerResult.message}</p>
                  {triggerResult.run_id && (
                    <p className="text-sm mt-1 opacity-75">运行 ID: {triggerResult.run_id}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 测试历史和结果 */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mr-3">
                <span className="text-white text-lg">📊</span>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">测试历史</h3>
                <p className="text-sm text-gray-500">最近的测试运行结果和详细信息</p>
              </div>
            </div>
            <a
              href="https://github.com/gqy22/batch_mcp/actions"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center"
            >
              <span className="mr-1">🔗</span>
              GitHub Actions
            </a>
          </div>
        </div>

        <div className="p-6">
          {workflowRuns.length > 0 ? (
            <div className="space-y-6">
              {workflowRuns.map((run) => (
                <div
                  key={run.id}
                  className="border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-center justify-between p-5 bg-gray-50">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4 mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-lg font-bold text-gray-700">#{run.run_number}</span>
                          <span className="text-gray-600">{run.name}</span>
                        </div>
                        {getStatusBadge(run.status, run.conclusion)}
                      </div>
                      <div className="text-sm text-gray-500 flex items-center">
                        <span className="mr-1">🕐</span>
                        {new Date(run.created_at).toLocaleString('zh-CN')}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {testResults[run.id] && (
                        <a
                          href={testResults[run.id].report_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center shadow-md hover:shadow-lg"
                        >
                          <span className="mr-2">📊</span>
                          查看报告
                        </a>
                      )}
                      <a
                        href={run.html_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-600 hover:text-gray-800 text-sm font-medium flex items-center"
                      >
                        <span className="mr-1">📋</span>
                        查看日志
                      </a>
                    </div>
                  </div>
                  
                  {/* 成功结果预览 */}
                  {testResults[run.id] && run.status === 'completed' && run.conclusion === 'success' && (
                    <div className="p-5 bg-gradient-to-r from-green-50 to-blue-50 border-t border-green-100">
                      <div className="flex items-center mb-4">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mr-3">
                          <span className="text-white text-sm">✓</span>
                        </div>
                        <h4 className="font-semibold text-green-800">测试成功完成</h4>
                      </div>
                      <p className="text-sm text-green-700 mb-4">
                        {testResults[run.id].summary}
                      </p>

                      {testResults[run.id].details && (
                      <div className="bg-white rounded-lg p-4 shadow-sm border">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* 基本信息 */}
                          <div className="space-y-3">
                            <h5 className="font-semibold text-gray-800 border-b pb-1">📋 基本信息</h5>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-600">测试工具:</span>
                                <span className="text-gray-800 font-medium">{testResults[run.id].details.tool_name || '未知'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">测试模式:</span>
                                <span className="text-gray-800">{testResults[run.id].details.test_mode || 'AI智能测试'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">使用模型:</span>
                                <span className="text-gray-800">{testResults[run.id].details.ai_model || 'GPT-4'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">运行时间:</span>
                                <span className="text-gray-800">{testResults[run.id].details.test_duration ? `${testResults[run.id].details.test_duration}秒` : '未知'}</span>
                              </div>
                            </div>
                          </div>

                          {/* 测试结果 */}
                          <div className="space-y-3">
                            <h5 className="font-semibold text-gray-800 border-b pb-1">🧪 测试结果</h5>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-600">安装状态:</span>
                                <span className={`font-medium ${testResults[run.id].details.install_success ? 'text-green-600' : 'text-red-600'}`}>
                                  {testResults[run.id].details.install_success ? '✅ 成功' : '❌ 失败'}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">功能测试:</span>
                                <span className={`font-medium ${testResults[run.id].details.function_test ? 'text-green-600' : 'text-red-600'}`}>
                                  {testResults[run.id].details.function_test ? '✅ 通过' : '❌ 失败'}
                                </span>
                              </div>
                              {testResults[run.id].details.total_tests && (
                                <div className="flex justify-between">
                                  <span className="text-gray-600">测试统计:</span>
                                  <span className="text-gray-800">
                                    {testResults[run.id].details.passed_tests || 0}/{testResults[run.id].details.total_tests || 0} 通过
                                  </span>
                                </div>
                              )}
                              {testResults[run.id].details.start_time && (
                                <div className="flex justify-between">
                                  <span className="text-gray-600">开始时间:</span>
                                  <span className="text-gray-800 text-xs">
                                    {new Date(testResults[run.id].details.start_time).toLocaleString('zh-CN')}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* 错误信息 */}
                        {testResults[run.id].details.error_message && (
                          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                            <h6 className="font-medium text-red-800 mb-1">❌ 错误信息</h6>
                            <p className="text-sm text-red-700">{testResults[run.id].details.error_message}</p>
                          </div>
                        )}
                      </div>
                    )}
                    </div>
                  )}
                
                {/* 失败状态显示 */}
                {run.status === 'completed' && run.conclusion === 'failure' && (
                  <div className="p-4 bg-red-50 border-t border-red-200">
                    <h4 className="font-medium text-red-800 mb-2 flex items-center">
                      <span className="mr-2">❌</span>
                      测试失败
                    </h4>
                    <p className="text-sm text-red-700">
                      测试过程中遇到错误，请查看详细日志了解具体原因。
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">
            暂无工作流运行记录，点击"刷新状态"获取最新信息
          </p>
        )}
      </div>
    </div>
    </div>
  )
}
