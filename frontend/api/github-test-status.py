#!/usr/bin/env python3
"""
Vercel API: GitHub Actions 测试状态查询

查询GitHub Actions workflow的执行状态和结果
"""

import json
import os
import time
from typing import Dict, Any, Optional

def get_github_pages_result(run_id: str) -> Optional[Dict[str, Any]]:
    """从GitHub Pages获取测试结果（按 run_id）"""
    try:
        import urllib.request
        import urllib.error
        
        # 构造GitHub Pages URL（与 workflow 输出一致）
        repo_owner = os.getenv('GITHUB_REPOSITORY', 'gqy20/batch_mcp').split('/')[0]
        repo_name = os.getenv('GITHUB_REPOSITORY', 'gqy20/batch_mcp').split('/')[1]
        pages_url = f"https://{repo_owner}.github.io/{repo_name}/test-results/{run_id}.json"
        
        # 发起HTTP请求
        request = urllib.request.Request(pages_url)
        request.add_header('User-Agent', 'Batch-MCP-Client/1.0')
        
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data
        
        return None
        
    except (urllib.error.URLError, json.JSONDecodeError, Exception):
        return None

def get_workflow_status_simple(run_id: str) -> Dict[str, Any]:
    """简化的状态查询（不依赖requests库）"""
    # 首先尝试从GitHub Pages获取结果
    pages_result = get_github_pages_result(run_id)
    
    if pages_result:
        return {
            'status': 'completed',
            'source': 'github_pages',
            'result': pages_result,
            'run_id': run_id
        }
    
    # 如果没有找到结果，返回进行中状态
    return {
        'status': 'running',
        'message': 'Test is still running or results not yet available',
        'run_id': run_id,
        'help': 'Please check GitHub Actions page for detailed progress'
    }

def handler(request):
    """处理状态查询请求"""
    
    # CORS支持
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    if request.method != 'GET':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # 获取查询参数（兼容旧的 session_id 与新的 run_id）
        run_id = None
        args = getattr(request, 'args', {}) or {}
        run_id = args.get('run_id') or args.get('session_id')
        
        # 兼容不同的请求对象格式
        if not run_id and hasattr(request, 'query'):
            run_id = request.query.get('run_id') or request.query.get('session_id')
        
        if not run_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'run_id parameter is required',
                    'usage': 'GET /api/github-test-status?run_id=<your-run-id>'
                })
            }
        
        # 查询测试状态
        status_result = get_workflow_status_simple(run_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache'
            },
            'body': json.dumps({
                'success': True,
                'run_id': run_id,
                'timestamp': time.time(),
                'data': status_result
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e),
                'run_id': run_id if 'run_id' in locals() else None
            })
        }

# Vercel兼容性
default = handler
