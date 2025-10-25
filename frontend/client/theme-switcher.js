// Theme Switcher - темная/светлая тема
(function() {
    // Проверить сохраненную тему
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // CSS переменные для тем
    const themes = {
        light: {
            '--bg-primary': '#f5f7fa',
            '--bg-secondary': '#ffffff',
            '--text-primary': '#333333',
            '--text-secondary': '#666666',
            '--border-color': '#ddd',
            '--shadow': '0 2px 8px rgba(0,0,0,0.1)'
        },
        dark: {
            '--bg-primary': '#1a1a1a',
            '--bg-secondary': '#2d2d2d',
            '--text-primary': '#e0e0e0',
            '--text-secondary': '#b0b0b0',
            '--border-color': '#444',
            '--shadow': '0 2px 8px rgba(0,0,0,0.3)'
        }
    };
    
    // Применить тему
    function applyTheme(theme) {
        const root = document.documentElement;
        const colors = themes[theme];
        
        for (const [key, value] of Object.entries(colors)) {
            root.style.setProperty(key, value);
        }
        
        document.body.className = theme;
        localStorage.setItem('theme', theme);
    }
    
    // Переключить тему
    window.toggleTheme = function() {
        const newTheme = localStorage.getItem('theme') === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        updateThemeButton();
    };
    
    // Обновить кнопку
    function updateThemeButton() {
        const btn = document.getElementById('themeToggle');
        if (btn) {
            const theme = localStorage.getItem('theme');
            btn.textContent = theme === 'dark' ? '☀️' : '🌙';
            btn.title = theme === 'dark' ? 'Светлая тема' : 'Темная тема';
        }
    }
    
    // Применить при загрузке
    applyTheme(currentTheme);
    
    // Создать кнопку переключения
    window.addEventListener('DOMContentLoaded', function() {
        const button = document.createElement('button');
        button.id = 'themeToggle';
        button.onclick = window.toggleTheme;
        button.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 2px solid var(--border-color);
            background: var(--bg-secondary);
            cursor: pointer;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1001;
            box-shadow: var(--shadow);
            transition: all 0.3s;
        `;
        
        button.onmouseenter = function() {
            this.style.transform = 'scale(1.1)';
        };
        
        button.onmouseleave = function() {
            this.style.transform = 'scale(1)';
        };
        
        document.body.appendChild(button);
        updateThemeButton();
    });
})();

