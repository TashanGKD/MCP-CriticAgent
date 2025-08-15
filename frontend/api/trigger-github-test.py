#!/usr/bin/env python3
"""
Vercel API: 触发 GitHub Actions 测试（统一新版）

与 .github/workflows/mcp-api-service.yml 对齐：
- inputs: mcp_url, test_timeout, run_id, mode, enable_ai_analysis
- 返回 run_id 与用于轮询的状态端点 /api/github-test-status?run_id=...
"""

import json
import os
import uuid
import requests
from datetime import datetime


def _json_response(status: int, body: dict, cors: bool = True):
    headers = {'Content-Type': 'application/json'}
    if cors:
        headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        })
    return {
        'statusCode': status,
        'headers': headers,
        'body': json.dumps(body)
    }


def handler(request):
    # CORS preflight
    if request.method == 'OPTIONS':
        return _json_response(200, {'ok': True})

    if request.method != 'POST':
        return _json_response(405, {'error': 'Method not allowed'})

    try:
        # 解析请求体（兼容不同运行时）
        if hasattr(request, 'get_json'):
            data = request.get_json()
        else:
            data = json.loads(request.body.decode('utf-8'))

        mcp_url = data.get('url') or data.get('mcp_url')
        test_timeout = int(data.get('timeout') or data.get('test_timeout') or 600)
        enable_ai = data.get('enable_ai')
        if enable_ai is None:
            enable_ai = True

        if not mcp_url:
            return _json_response(400, {'success': False, 'error': 'URL is required (url or mcp_url)'})

        github_token = os.getenv('GITHUB_TOKEN')
        github_repo = os.getenv('GITHUB_REPOSITORY', 'gqy22/batch_mcp')
        if not github_token:
            return _json_response(500, {'success': False, 'error': 'GitHub token not configured'})

        run_id = f"api-test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"

        dispatch_url = f"https://api.github.com/repos/{github_repo}/actions/workflows/mcp-api-service.yml/dispatches"
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
        }
        payload = {
            'ref': 'main',
            'inputs': {
                'mcp_url': mcp_url,
                'test_timeout': str(test_timeout),
                'run_id': run_id,
                'mode': 'api',
                'enable_ai_analysis': 'true' if enable_ai else 'false',
            },
        }

        resp = requests.post(dispatch_url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 204:
            return _json_response(200, {
                'success': True,
                'message': 'GitHub Actions workflow triggered',
                'run_id': run_id,
                'github_repo': github_repo,
                'status_endpoint': f"/api/github-test-status?run_id={run_id}",
            })
        else:
            return _json_response(500, {
                'success': False,
                'error': f'GitHub API error: {resp.status_code}',
                'details': resp.text[:500],
            })
    except Exception as e:
        return _json_response(500, {'success': False, 'error': f'Internal error: {e}'})


def handler_vercel(request):
    return handler(request)
