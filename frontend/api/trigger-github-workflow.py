#!/usr/bin/env python3
"""
前端 GitHub Actions 触发 API
用于从前端界面触发 GitHub Actions 工作流
"""
import json
import os
import uuid
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
    
    # 只处理 POST 请求
    if event.get('httpMethod') != 'POST':
        return _json_response(405, {'error': '只支持 POST 请求'})
    
    try:
        # 解析请求体
        body = json.loads(event.get('body', '{}'))
        
        # 获取环境变量
        github_token = os.getenv('HUB_TOKEN')
        github_repo = os.getenv('GITHUB_REPOSITORY', 'gqy22/batch_mcp')
        
        if not github_token:
            return _json_response(500, {'error': 'GitHub Token 未配置'})
        
        # 获取请求参数
        workflow_file = body.get('workflow_file', 'mcp-api-service.yml')
        mcp_url = body.get('mcp_url', 'https://github.com/upstash/context7')
        test_timeout = body.get('test_timeout', '120')
        mode = body.get('mode', 'frontend_trigger')
        enable_ai_analysis = body.get('enable_ai_analysis', 'false')
        
        # 生成唯一运行 ID
        run_id = f"web-{str(uuid.uuid4())[:8]}"
        
        # 准备 GitHub API 请求
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'batch-mcp-frontend'
        }
        
        # 构建工作流触发 URL
        dispatch_url = f"https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_file}/dispatches"
        
        # 准备工作流输入参数
        workflow_inputs = {
            'mcp_url': mcp_url,
            'test_timeout': str(test_timeout),
            'run_id': run_id,
            'mode': mode,
            'enable_ai_analysis': str(enable_ai_analysis).lower()
        }
        
        payload = {
            'ref': 'main',
            'inputs': workflow_inputs
        }
        
        # 触发工作流
        response = requests.post(dispatch_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 204:
            # 成功触发
            return _json_response(200, {
                'success': True,
                'message': 'GitHub Actions 工作流已成功触发',
                'run_id': run_id,
                'workflow_file': workflow_file,
                'github_url': f'https://github.com/{github_repo}/actions',
                'inputs': workflow_inputs,
                'triggered_at': datetime.now().isoformat()
            })
        else:
            # 触发失败
            error_detail = response.text if response.text else f'HTTP {response.status_code}'
            return _json_response(400, {
                'success': False,
                'error': f'工作流触发失败: {error_detail}',
                'status_code': response.status_code
            })
            
    except json.JSONDecodeError:
        return _json_response(400, {'error': '无效的 JSON 请求体'})
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
        'body': request.get_data(as_text=True) if hasattr(request, 'get_data') else request.data
    }
    
    return handler(event, None)
