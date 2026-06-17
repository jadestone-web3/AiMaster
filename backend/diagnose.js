// 在 Chrome 插件的弹窗中按 F12 打开 Console
// 然后运行以下代码来诊断问题

console.log('=== AiMaster 诊断 ===');

// 1. 检查 API 地址
console.log('API_BASE_URL:', typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : '未定义');

// 2. 测试后端连接
if (typeof API_BASE_URL !== 'undefined') {
    fetch(`${API_BASE_URL}/`)
        .then(r => r.json())
        .then(data => {
            console.log('✅ 后端连接成功:', data);
        })
        .catch(err => {
            console.log('❌ 后端连接失败:', err);
        });
} else {
    console.log('❌ API_BASE_URL 未定义，插件代码可能有问题');
}

// 3. 检查存储的 token
chrome.storage.local.get(['apiBaseUrl', 'authToken'], (result) => {
    console.log('存储的配置:', result);
});

// 4. 测试验证码接口
if (typeof API_BASE_URL !== 'undefined') {
    fetch(`${API_BASE_URL}/api/auth/captcha`)
        .then(r => r.json())
        .then(data => {
            console.log('✅ 验证码接口正常:', data.captcha_id);
        })
        .catch(err => {
            console.log('❌ 验证码接口失败:', err);
        });
}
