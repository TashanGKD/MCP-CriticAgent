import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    // 获取环境变量
    const githubToken = process.env.HUB_TOKEN
    const githubRepo = process.env.GITHUB_REPOSITORY || 'gqy22/batch_mcp'
    
    if (!githubToken) {
      return NextResponse.json(
        { success: false, error: 'GitHub Token 未配置' },
        { status: 500 }
      )
    }
    
    // 解析请求体
    const body = await request.json()
    const {
      github_url = 'https://github.com/upstash/context7'
    } = body
    
    // 验证必要参数
    if (!github_url) {
      return NextResponse.json(
        { success: false, error: '缺少必要参数: github_url' },
        { status: 400 }
      )
    }
    
    // 生成唯一运行 ID
    const runId = `web-${Math.random().toString(36).substring(2, 10)}`
    
    // 准备 GitHub API 请求
    const headers = {
      'Authorization': `token ${githubToken}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'batch-mcp-frontend',
      'Content-Type': 'application/json'
    }
    
    // 构建工作流触发 URL（固定使用simple-mcp-test.yml）
    const dispatchUrl = `https://api.github.com/repos/${githubRepo}/actions/workflows/simple-mcp-test.yml/dispatches`
    
    // 准备工作流输入参数
    const workflowInputs = {
      github_url
    }
    
    const payload = {
      ref: 'main',
      inputs: workflowInputs
    }
    
    console.log('触发工作流:', { dispatchUrl, payload })
    
    // 触发工作流
    const response = await fetch(dispatchUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    })
    
    console.log('GitHub API 响应:', response.status, response.statusText)
    
    if (response.status === 204) {
      // 成功触发
      return NextResponse.json({
        success: true,
        message: 'MCP 工具测试已成功启动',
        run_id: runId,
        workflow_file: 'simple-mcp-test.yml',
        github_url: `https://github.com/${githubRepo}/actions`,
        inputs: workflowInputs,
        triggered_at: new Date().toISOString()
      })
    } else {
      // 触发失败
      const errorText = await response.text()
      console.error('工作流触发失败:', response.status, errorText)
      
      return NextResponse.json({
        success: false,
        error: `工作流触发失败: HTTP ${response.status}`,
        status_code: response.status,
        details: errorText
      }, { status: 400 })
    }
    
  } catch (error) {
    console.error('API 错误:', error)
    return NextResponse.json({
      success: false,
      error: `服务器内部错误: ${error instanceof Error ? error.message : String(error)}`
    }, { status: 500 })
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  })
}
