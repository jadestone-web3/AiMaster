// 在 Chrome 扩展页面的 Console 中运行此脚本来清除旧配置
// chrome://extensions/ → 找到 AiMaster → 点击"详细信息" → "检查视图"

console.log('🧹 清除 AiMaster 旧配置...');

// 清除旧的 API 地址
chrome.storage.local.remove(['apiBaseUrl', 'authToken', 'refreshToken', 'currentUser'], () => {
    console.log('✅ 旧配置已清除');

    // 设置新的本地地址
    chrome.storage.local.set({
        apiBaseUrl: 'http://localhost:8000'
    }, () => {
        console.log('✅ 新地址已设置: http://localhost:8000');

        // 验证
        chrome.storage.local.get(['apiBaseUrl'], (result) => {
            console.log('📍 当前配置:', result);
            console.log('✅ 完成！请重新加载插件');
        });
    });
});
