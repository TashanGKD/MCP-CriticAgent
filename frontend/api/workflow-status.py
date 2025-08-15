#!/usr/bin/env python3
"""
GitHub Actions 状态查询 API
用于查询工作流运行状态
"""
import json
import os
import requests
from datetime import datetime


def _json_response(status: int, body: dict, cors: bool = True):
    """生成标准 JSON 响应"""
    headers = {'Content-Type': 'application/json'}
    if cors:
        headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        })
    return {
        'statusCode': status,
        'headers': headers,
        'body': json.dumps(body, ensure_ascii=False)
    }


def handler(event, context):
    """主处理函数"""
    # 处理 CORS 预检请求
    if event.get('httpMethod') == 'OPTIONS':
        return _json_response(200, {'message': 'CORS preflight'})
    
    try:
        # 获取环境变量
        github_token = os.getenv('GITHUB_TOKEN')
        github_repo = os.getenv('GITHUB_REPOSITORY', 'gqy22/batch_mcp')
        
        if not github_token:
            return _json_response(500, {'error': 'GitHub Token 未配置'})
        
        # 获取查询参数
        query_params = event.get('queryStringParameters', {}) or {}
        run_id = query_params.get('run_id')
        limit = int(query_params.get('limit', '5'))
        
        # 准备 GitHub API 请求
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'batch-mcp-frontend'
        }
        
        # 获取最近的工作流运行
        runs_url = f"https://api.github.com/repos/{github_repo}/actions/runs"
        response = requests.get(runs_url, headers=headers, params={'per_page': limit}, timeout=30)
        
        if response.status_code == 200:
            runs_data = response.json()
            runs = []
            
            for run in runs_data.get('workflow_runs', []):
                run_info = {
                    'id': run['id'],
                    'name': run['name'],
                    'status': run['status'],
                    'conclusion': run.get('conclusion'),
                    'created_at': run['created_at'],
                    'updated_at': run['updated_at'],
                    'html_url': run['html_url'],
                    'head_branch': run['head_branch'],
                    'head_sha': run['head_sha'][:7] if run.get('head_sha') else None,
                    'run_number': run['run_number']
                }
                
                # 如果指定了 run_id，检查是否匹配
                if run_id:
                    # 检查 run_id 是否在运行的 head_commit_message 或其他地方
                    if run_id in str(run.get('head_commit', {}).get('message', '')):
                        run_info['matched'] = True
                
                runs.append(run_info)
            
            return _json_response(200, {
                'success': True,
                'runs': runs,
                'total_count': runs_data.get('total_count', 0),
                'github_actions_url': f'https://github.com/{github_repo}/actions',
                'queried_at': datetime.now().isoformat()
            })
        else:
            return _json_response(400, {
                'success': False,
                'error': f'获取工作流运行失败: HTTP {response.status_code}',
                'status_code': response.status_code
            })
            
    except requests.exceptions.RequestException as e:
        return _json_response(500, {'error': f'GitHub API 请求失败: {str(e)}'})
    except Exception as e:
        return _json_response(500, {'error': f'服务器内部错误: {str(e)}'})


# Vercel 无服务器函数入口
def main(request):
    """Vercel 函数入口点 - 转换请求格式"""
    # 将 Vercel/Flask 请求对象转换为事件格式
    event = {
        'httpMethod': request.method,
        'queryStringParameters': request.args.to_dict() if hasattr(request, 'args') else {}
    }
    
    return handler(event, None)
