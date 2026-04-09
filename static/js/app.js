/**
 * 熵食源 - 应用程序脚本
 */

// 工具函数
const utils = {
    // 格式化日期
    formatDate: function(date) {
        const d = new Date(date);
        return d.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    },
    
    // 格式化时间
    formatTime: function(time) {
        return time.substring(0, 5);
    },
    
    // 显示提示消息
    showToast: function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; animation: slideIn 0.3s ease;';
        toast.innerHTML = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    },
    
    // 防抖函数
    debounce: function(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
};

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 自动关闭提示消息
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'fadeOut 0.5s ease forwards';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
    
    // 表单验证
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // 数字输入格式化
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && this.step) {
                const decimals = this.step.includes('.') ? 
                    this.step.split('.')[1].length : 0;
                this.value = parseFloat(this.value).toFixed(decimals);
            }
        });
    });
});

// 食物搜索功能
async function searchFoods(query) {
    if (!query || query.length < 1) return;
    
    try {
        const response = await fetch(`/api/foods?q=${encodeURIComponent(query)}`);
        const foods = await response.json();
        return foods;
    } catch (error) {
        console.error('搜索失败:', error);
        return [];
    }
}

// 计算热量
function calculateCalories(baseCalories, quantity) {
    return Math.round(baseCalories * quantity / 100);
}

// 计算营养素
function calculateNutrient(baseValue, quantity) {
    return (baseValue * quantity / 100).toFixed(1);
}

// 获取每日数据
async function getDailyStats(date) {
    try {
        const response = await fetch(`/api/stats/daily?date=${date}`);
        return await response.json();
    } catch (error) {
        console.error('获取数据失败:', error);
        return null;
    }
}

// 语音识别（如果浏览器支持）
const voiceRecognition = {
    isSupported: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
    
    start: function(onResult, onError) {
        if (!this.isSupported) {
            onError('您的浏览器不支持语音识别');
            return null;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.lang = 'zh-CN';
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onresult = function(event) {
            const result = event.results[0][0].transcript;
            onResult(result);
        };
        
        recognition.onerror = function(event) {
            onError(event.error);
        };
        
        recognition.start();
        return recognition;
    }
};

// 图表初始化（预留）
const charts = {
    initCalorieChart: function(canvasId, data) {
        // 使用Chart.js初始化
        // 需要在页面引入Chart.js库
        console.log('图表初始化预留:', canvasId);
    }
};

// 导出功能
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { utils, voiceRecognition };
}
