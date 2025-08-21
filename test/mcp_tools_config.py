#!/usr/bin/env python3
"""
完整的MCP工具配置和测试映射

基于test.csv中的MCP工具，创建正确的部署配置和测试方案

作者: AI Assistant  
日期: 2025-08-14
"""

# MCP工具配置映射表
MCP_TOOLS_CONFIG = {
    "youtube": {
        "name": "YouTube视频信息工具",
        "package": "@limecooler/yt-info-mcp@latest", 
        "github": "https://github.com/Limecooler/yt-video-info",
        "tools": ["get_video_info"],
        "test_args": {"video_id": "dQw4w9WgXcQ"},
        "mcp_args": {"video_id": "dQw4w9WgXcQ"},
        "param_name": "video_id",
        "sys_prompt": "你是一个YouTube视频信息查询助手，可以帮助用户获取视频的详细信息。",
        "user_message": "请获取视频ID为dQw4w9WgXcQ的YouTube视频信息",
        "category": "信息获取",
        "verified": True
    },
    "think": {
        "name": "最小化思考工具",
        "package": "minimal-think-mcp",
        "github": "https://github.com/differentstuff/minimal-think-mcp", 
        "tools": ["think"],
        "test_args": {"reasoning": "什么是人工智能？请分析其定义和应用。"},
        "mcp_args": {"reasoning": "什么是人工智能？请分析其定义和应用。"},
        "param_name": "reasoning",
        "sys_prompt": "你是一个AI思考助手，可以使用思考工具进行深度分析和推理。",
        "user_message": "请使用思考工具分析：什么是人工智能及其应用领域？",
        "category": "思考辅助",
        "verified": True
    },
    "svelte": {
        "name": "Svelte文档工具",
        "package": "mcp-svelte-docs",
        "github": "https://github.com/spences10/mcp-svelte-docs",
        "tools": ["search_docs"],
        "test_args": {"query": "components"},
        "mcp_args": {"query": "components"},
        "param_name": "query",
        "sys_prompt": "你是一个Svelte文档查询助手，可以帮助用户查找Svelte相关文档。",
        "user_message": "请查找Svelte组件的相关文档",
        "category": "文档检索"
    },
    "openalex": {
        "name": "学术文献检索工具",
        "package": "openalex-mcp",
        "github": "https://github.com/reetp14/openalex-mcp",
        "tools": ["search_papers"],
        "test_args": {"query": "machine learning"},
        "mcp_args": {"query": "machine learning"},
        "param_name": "query",
        "sys_prompt": "你是一个学术文献检索助手，可以帮助用户查找和分析学术论文。",
        "user_message": "请搜索关于机器学习的最新学术论文",
        "category": "学术检索"
    },
    "12306": {
        "name": "12306查询工具",
        "package": "12306-mcp",
        "github": "https://github.com/Joooook/12306-mcp",
        "tools": ["query_train"],
        "test_args": {"from": "北京", "to": "上海"},
        "mcp_args": {"from": "北京", "to": "上海"},
        "param_name": "from_to",
        "sys_prompt": "你是一个火车票查询助手，可以帮助用户查询火车票信息。",
        "user_message": "请查询从北京到上海的火车票信息",
        "category": "信息查询"
    },
    "context7": {
        "name": "Context7工具",
        "package": "@upstash/context7-mcp",
        "github": "https://github.com/upstash/context7",
        "tools": ["resolve-library-id", "get-library-docs"],
        "test_args": {"libraryName": "react"},
        "mcp_args": {"libraryName": "react"},
        "param_name": "libraryName",
        "sys_prompt": "你是一个代码文档查询助手，可以帮助用户查找库和框架的文档。",
        "user_message": "请查找React库的相关文档",
        "category": "信息查询",
        "verified": True
    }
}

def get_npx_command(tool_key: str) -> list:
    """获取NPX启动命令"""
    config = MCP_TOOLS_CONFIG.get(tool_key)
    if not config:
        raise ValueError(f"未知的MCP工具: {tool_key}")
    
    package = config["package"]
    return ["npx", "-y", package]

def print_mcp_tools_summary():
    """打印MCP工具总结"""
    print("🔧 MCP工具配置总结")
    print("=" * 70)
    
    for key, config in MCP_TOOLS_CONFIG.items():
        status = "✅ 已验证" if config.get("verified") else "⏳ 待测试"
        print(f"\n📦 {config['name']} ({key})")
        print(f"   包名: {config['package']}")
        print(f"   工具: {', '.join(config['tools'])}")
        print(f"   分类: {config['category']}")
        print(f"   状态: {status}")

if __name__ == "__main__":
    print_mcp_tools_summary()
    
    print("\n🎯 推荐测试顺序:")
    print("1. context7 - 已验证成功 ✅")
    print("2. youtube - 正在测试中 ⏳")
    print("3. think - 思考辅助工具")
    print("4. svelte - 文档检索工具")
    print("5. openalex - 学术检索工具")
    print("6. 12306 - 火车票查询工具")
    
    print(f"\n📋 总计: {len(MCP_TOOLS_CONFIG)} 个MCP工具")
    verified_count = sum(1 for config in MCP_TOOLS_CONFIG.values() if config.get("verified"))
    print(f"已验证: {verified_count} 个")
    print(f"待测试: {len(MCP_TOOLS_CONFIG) - verified_count} 个")
