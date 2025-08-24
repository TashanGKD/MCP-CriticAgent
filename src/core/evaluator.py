
import requests
import os
import re
import json
import time
from datetime import datetime, timedelta, timezone
import statistics

# --- 评分权重配置 ---

# 1. 最终分数权重 (总和必须为100)
FINAL_WEIGHTS = {
    'sustainability': 50,
    'popularity': 50
}

# 2. 可持续性内部指标权重 (总和必须为100)
SUSTAINABILITY_WEIGHTS = {
    'recency': 20,
    'frequency': 30,
    'stability': 20,
    'issue_responsiveness': 15,
    'issue_health': 15
}

# 3. 受欢迎程度内部指标权重 (总和必须为100)
POPULARITY_WEIGHTS = {
    'stars': 70,
    'forks': 30
}

# --- 验证权重配置 ---
assert sum(FINAL_WEIGHTS.values()) == 100, "最终权重总和必须为100"
assert sum(SUSTAINABILITY_WEIGHTS.values()) == 100, "可持续性权重总和必须为100"
assert sum(POPULARITY_WEIGHTS.values()) == 100, "受欢迎程度权重总和必须为100"

# --- API 和头部信息 ---
API_URL = "https://api.github.com"
HUB_TOKEN = os.environ.get("HUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if HUB_TOKEN:
    HEADERS["Authorization"] = f"token {HUB_TOKEN}"

# --- 辅助函数和API调用 ---

def parse_github_url(url):
    if not isinstance(url, str): return None, None
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if match:
        owner, repo = match.groups()
        return owner, repo.replace('.git', '')
    return None, None

def get_repo_data(owner, repo):
    url = f"{API_URL}/repos/{owner}/{repo}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_commit_data(owner, repo, limit=100):
    url = f"{API_URL}/repos/{owner}/{repo}/commits"
    params = {"per_page": limit}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_issue_data(owner, repo, state='closed', limit=100):
    url = f"{API_URL}/repos/{owner}/{repo}/issues"
    params = {"per_page": limit, "state": state}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_closed_issues_count(owner, repo):
    url = f"{API_URL}/search/issues"
    params = {'q': f'repo:{owner}/{repo} is:issue is:closed'}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json().get('total_count', 0)

# --- 分析函数模块 ---

# === 可持续性分析模块 ===
def analyze_recency(repo_data):
    last_pushed_str = repo_data.get('pushed_at')
    if not last_pushed_str: return 0, "无法获取最后更新时间"
    days = (datetime.now(timezone.utc) - datetime.fromisoformat(last_pushed_str.replace('Z', '+00:00'))).days
    w = SUSTAINABILITY_WEIGHTS['recency']
    if days <= 7:   score, reason = w, f"非常活跃 (最近 {days} 天内有更新)"
    elif days <= 30:  score, reason = w * 0.8, "活跃 (最近一个月内有更新)"
    else:             score, reason = 0, "项目可能已废弃 (超过一年未更新)"
    return int(score), reason

def analyze_frequency(commit_data):
    if not commit_data: return 0, "没有提交记录"
    ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
    recent_commits = [c for c in commit_data if datetime.fromisoformat(c['commit']['author']['date'].replace('Z', '+00:00')) > ninety_days_ago]
    count = len(recent_commits)
    per_week = count / (90 / 7) if count > 0 else 0
    w = SUSTAINABILITY_WEIGHTS['frequency']
    if per_week >= 5: score, reason = w, f"非常高频 (近90天 {count} 次提交, 约 {per_week:.1f} 次/周)"
    elif per_week >= 2: score, reason = w * 0.8, f"较高频率 (近90天 {count} 次提交, 约 {per_week:.1f} 次/周)"
    else:             score, reason = 0, "近90天内无提交"
    return int(score), reason

def analyze_stability(commit_data):
    if len(commit_data) < 5: return 0, "提交记录过少 (<5)，无法评估稳定性"
    dates = [datetime.fromisoformat(c['commit']['author']['date'].replace('Z', '+00:00')) for c in commit_data]
    intervals = [(dates[i] - dates[i+1]).days for i in range(len(dates) - 1)]
    print(f"DEBUG: intervals: {intervals}")
    if not intervals: return 0, "无法计算提交间隔"
    std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0
    w = SUSTAINABILITY_WEIGHTS['stability']
    if std_dev <= 3:    score, reason = w, f"非常稳定 (提交间隔标准差: {std_dev:.2f} 天)"
    elif std_dev <= 7:  score, reason = w * 0.8, f"比较稳定 (提交间隔标准差: {std_dev:.2f} 天)"
    else:               score, reason = w * 0.2, f"更新非常不稳定 (标准差: {std_dev:.2f} 天)"
    return int(score), reason

def analyze_issue_responsiveness(closed_issues):
    if not closed_issues: return 0, "近期没有已关闭的Issue"
    resolution_days = [(datetime.fromisoformat(i['closed_at'].replace('Z', '+00:00')) - datetime.fromisoformat(i['created_at'].replace('Z', '+00:00'))).days for i in closed_issues if 'pull_request' not in i]
    print(f"DEBUG: resolution_days: {resolution_days}")
    if not resolution_days: return int(SUSTAINABILITY_WEIGHTS['issue_responsiveness'] * 0.5), "近期关闭的都是PR"
    median_days = statistics.median(resolution_days)
    w = SUSTAINABILITY_WEIGHTS['issue_responsiveness']
    if median_days <= 3:   score, reason = w, f"响应极快 (中位数解决时间: {median_days:.1f} 天)"
    elif median_days <= 7: score, reason = w * 0.8, f"响应较快 (中位数解决时间: {median_days:.1f} 天)"
    else:                  score, reason = w * 0.2, f"响应缓慢 (中位数解决时间: {median_days:.1f} 天)"
    return int(score), reason

def analyze_issue_health(repo_data, closed_issues_count):
    open_issues_count = repo_data.get('open_issues_count', 0)
    total_issues = open_issues_count + closed_issues_count
    if total_issues == 0: return SUSTAINABILITY_WEIGHTS['issue_health'], "项目中没有Issue"
    open_ratio = open_issues_count / total_issues
    w = SUSTAINABILITY_WEIGHTS['issue_health']
    if open_ratio <= 0.05: score, reason = w, f"非常健康 (开放Issue比例: {open_ratio:.1%})"
    elif open_ratio <= 0.15: score, reason = w * 0.8, f"比较健康 (开放Issue比例: {open_ratio:.1%})"
    else:                  score, reason = w * 0.2, f"不健康 (开放Issue比例: {open_ratio:.1%}, 严重积压)"
    return int(score), reason

# === 受欢迎程度分析模块 ===
def analyze_stars(repo_data):
    star_count = repo_data.get('stargazers_count', 0)
    w = POPULARITY_WEIGHTS['stars']
    if star_count >= 10000: score, reason = w, f"顶级项目 ({star_count:,} stars)"
    elif star_count >= 2000:  score, reason = w * 0.8, f"非常受欢迎 ({star_count:,} stars)"
    elif star_count >= 500:   score, reason = w * 0.6, f"广受欢迎 ({star_count:,} stars)"
    elif star_count >= 100:   score, reason = w * 0.3, f"有一定关注度 ({star_count:,} stars)"
    else:                   score, reason = w * 0.1, f"小众项目 ({star_count:,} stars)"
    return int(score), reason

def analyze_forks(repo_data):
    fork_count = repo_data.get('forks_count', 0)
    w = POPULARITY_WEIGHTS['forks']
    if fork_count >= 2000:  score, reason = w, f"生态系统级 ({fork_count:,} forks)"
    elif fork_count >= 500:   score, reason = w * 0.8, f"社区活跃 ({fork_count:,} forks)"
    elif fork_count >= 100:   score, reason = w * 0.5, f"有社区贡献 ({fork_count:,} forks)"
    else:                   score, reason = w * 0.2, f"个人或小团队项目 ({fork_count:,} forks)"
    return int(score), reason

# --- 评估流程编排 ---

def evaluate_sustainability(repo_data, commit_data, closed_issues, closed_issues_count):
    recency_s, recency_r = analyze_recency(repo_data)
    frequency_s, frequency_r = analyze_frequency(commit_data)
    stability_s, stability_r = analyze_stability(commit_data)
    responsiveness_s, responsiveness_r = analyze_issue_responsiveness(closed_issues)
    health_s, health_r = analyze_issue_health(repo_data, closed_issues_count)
    
    total_score = recency_s + frequency_s + stability_s + responsiveness_s + health_s
    details = {
        "recency": {"score": recency_s, "reason": recency_r, "weight": SUSTAINABILITY_WEIGHTS['recency']},
        "frequency": {"score": frequency_s, "reason": frequency_r, "weight": SUSTAINABILITY_WEIGHTS['frequency']},
        "stability": {"score": stability_s, "reason": stability_r, "weight": SUSTAINABILITY_WEIGHTS['stability']},
        "issue_responsiveness": {"score": responsiveness_s, "reason": responsiveness_r, "weight": SUSTAINABILITY_WEIGHTS['issue_responsiveness']},
        "issue_health": {"score": health_s, "reason": health_r, "weight": SUSTAINABILITY_WEIGHTS['issue_health']}
    }
    return {"total_score": total_score, "details": details}

def evaluate_popularity(repo_data):
    stars_s, stars_r = analyze_stars(repo_data)
    forks_s, forks_r = analyze_forks(repo_data)

    total_score = stars_s + forks_s
    details = {
        "stars": {"score": stars_s, "reason": stars_r, "weight": POPULARITY_WEIGHTS['stars']},
        "forks": {"score": forks_s, "reason": forks_r, "weight": POPULARITY_WEIGHTS['forks']}
    }
    return {"total_score": total_score, "details": details}

def evaluate_full_repository_profile(github_url):
    owner, repo = parse_github_url(github_url)
    if not owner or not repo:
        return {"status": "error", "message": f"无效的GitHub URL: {github_url}"}
    try:
        repo_data = get_repo_data(owner, repo)
        time.sleep(0.5)
        commit_data = get_commit_data(owner, repo)
        time.sleep(0.5)
        closed_issues = get_issue_data(owner, repo, state='closed')
        time.sleep(0.5)
        closed_issues_count = get_closed_issues_count(owner, repo)

        sustainability = evaluate_sustainability(repo_data, commit_data, closed_issues, closed_issues_count)
        popularity = evaluate_popularity(repo_data)

        final_score = (sustainability['total_score'] * (FINAL_WEIGHTS['sustainability'] / 100)) + \
                      (popularity['total_score'] * (FINAL_WEIGHTS['popularity'] / 100))
        
        return {
            "status": "success",
            "full_name": repo_data.get('full_name'),
            "final_score": int(final_score),
            "sustainability": sustainability,
            "popularity": popularity
        }
    except requests.exceptions.RequestException as e:
        error_message = f"API请求失败: {e}"
        if e.response is not None: error_message += f" (Status code: {e.response.status_code})"
        return {"status": "error", "message": error_message}
    except TypeError as e:
        import traceback
        return {"status": "error", "message": f"发生类型错误: {e}", "traceback": traceback.format_exc()}
    except Exception as e:
        import traceback
        return {"status": "error", "message": f"发生未知错误: {e}", "traceback": traceback.format_exc()}
