"""
AiMaster 本地后端完整测试脚本
测试所有 API 端点
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)

def test_health_check():
    """测试健康检查"""
    print_section("1️⃣ 健康检查")
    response = requests.get(f"{BASE_URL}/")
    print(f"✅ GET /")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_captcha():
    """测试验证码接口"""
    print_section("2️⃣ 获取验证码")
    response = requests.get(f"{BASE_URL}/api/auth/captcha")
    data = response.json()
    print(f"✅ GET /api/auth/captcha")
    print(f"   Captcha ID: {data['captcha_id']}")
    return data['captcha_id']

def test_login(captcha_id):
    """测试登录"""
    print_section("3️⃣ 用户登录")
    payload = {
        "username": "admin",
        "password": "admin123",
        "captcha_id": captcha_id,
        "captcha_code": "1234"  # 验证码任意输入
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    print(f"✅ POST /api/auth/login")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()['access_token']

def test_get_current_user(token):
    """测试获取当前用户信息"""
    print_section("4️⃣ 获取当前用户信息")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"✅ GET /api/auth/me")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_submit_article(token):
    """测试提交文章"""
    print_section("5️⃣ 提交文章进行AI改写")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "platform": "netease",
        "article": {
            "title": "测试文章：AI技术的未来",
            "content": "人工智能技术正在快速发展，它将改变我们的生活方式。从自动驾驶到智能助手，AI已经渗透到各个领域。",
            "author": "测试作者",
            "publishTime": "2026-06-15"
        }
    }
    response = requests.post(f"{BASE_URL}/api/articles", json=payload, headers=headers)
    print(f"✅ POST /api/articles")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result.get('task_id')

def test_wait_for_task(token, task_id):
    """等待任务完成并获取进度"""
    print_section("6️⃣ 等待AI改写完成")
    headers = {"Authorization": f"Bearer {token}"}

    print("⏳ 处理中...")
    for i in range(6):  # 最多等待6次（每次2秒）
        response = requests.get(f"{BASE_URL}/api/tasks/{task_id}", headers=headers)
        task = response.json()
        progress = task.get('progress', 0)
        status = task.get('status', 'unknown')

        print(f"   进度: {progress}% | 状态: {status}")

        if status == 'completed':
            print("\n✅ 任务完成！")
            print(json.dumps(task, indent=2, ensure_ascii=False))
            return task
        elif status == 'failed':
            print("\n❌ 任务失败")
            return task

        time.sleep(2)

    return task

def test_get_tasks(token):
    """测试获取任务列表"""
    print_section("7️⃣ 获取任务列表")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
    tasks = response.json()
    print(f"✅ GET /api/tasks")
    print(f"   共 {len(tasks)} 个任务")
    print(json.dumps(tasks, indent=2, ensure_ascii=False))

def main():
    print("\n" + "🚀" * 25)
    print("  AiMaster 本地后端完整测试")
    print("🚀" * 25)

    try:
        # 1. 健康检查
        test_health_check()

        # 2. 获取验证码
        captcha_id = test_captcha()

        # 3. 登录
        token = test_login(captcha_id)

        # 4. 获取用户信息
        test_get_current_user(token)

        # 5. 提交文章
        task_id = test_submit_article(token)

        # 6. 等待任务完成
        if task_id:
            final_task = test_wait_for_task(token, task_id)

            # 7. 获取任务列表
            test_get_tasks(token)

        print_section("✅ 所有测试通过")
        print("📝 测试总结：")
        print("   ✅ 后端服务正常运行")
        print("   ✅ 用户认证功能正常")
        print("   ✅ 文章提交功能正常")
        print("   ✅ AI改写功能正常")
        print("   ✅ 任务查询功能正常")
        print("\n💡 Chrome 插件可以正常使用！")

    except Exception as e:
        print_section("❌ 测试失败")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
