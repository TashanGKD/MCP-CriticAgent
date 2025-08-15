import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
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
    
    // 获取查询参数
    const { searchParams } = new URL(request.url)
    const runId = searchParams.get('run_id')
    const limit = parseInt(searchParams.get('limit') || '5')
    
    // 准备 GitHub API 请求
    const headers = {
      'Authorization': `token ${githubToken}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'batch-mcp-frontend'
    }
    
    // 获取最近的工作流运行
    const runsUrl = `https://api.github.com/repos/${githubRepo}/actions/runs?per_page=${limit}`
    
    console.log('查询工作流状态:', runsUrl)
    
    const response = await fetch(runsUrl, { headers })
    
    if (response.ok) {
      const runsData = await response.json()
      const runs = []
      
      for (const run of runsData.workflow_runs || []) {
        const runInfo: any = {
          id: run.id,
          name: run.name,
          status: run.status,
          conclusion: run.conclusion,
          created_at: run.created_at,
          updated_at: run.updated_at,
          html_url: run.html_url,
          head_branch: run.head_branch,
          head_sha: run.head_sha?.substring(0, 7),
          run_number: run.run_number
        }
        
        // 如果指定了 run_id，检查是否匹配
        if (runId) {
          // 检查 run_id 是否在运行的 head_commit_message 或其他地方
          const commitMessage = run.head_commit?.message || ''
          if (commitMessage.includes(runId)) {
            runInfo.matched = true
          }
        }
        
        runs.push(runInfo)
      }
      
      return NextResponse.json({
        success: true,
        runs,
        total_count: runsData.total_count || 0,
        github_actions_url: `https://github.com/${githubRepo}/actions`,
        queried_at: new Date().toISOString()
      })
    } else {
      const errorText = await response.text()
      console.error('获取工作流状态失败:', response.status, errorText)
      
      return NextResponse.json({
        success: false,
        error: `获取工作流运行失败: HTTP ${response.status}`,
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
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  })
}
