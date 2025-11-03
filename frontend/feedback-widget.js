/**
 * Виджет обратной связи HackAPI 2025
 * Универсальный компонент для всех UI страниц
 * 
 * Использование:
 * <script src="/static/feedback-widget.js"></script>
 * <script>
 *   initFeedbackWidget({
 *     bankCode: 'vbank',  // vbank / abank / sbank / directory
 *     uiType: 'client',   // client / banker / admin
 *     participantLogin: 'team010-1'  // опционально
 *   });
 * </script>
 */

(function() {
    'use strict';

    // Глобальные переменные виджета
    let widgetConfig = {
        bankCode: 'unknown',
        uiType: 'client',
        participantLogin: null,
        directoryUrl: getDirectoryUrl()  // URL Directory Service
    };

    /**
     * Определение URL Directory Service (dev/production)
     */
    function getDirectoryUrl() {
        const hostname = window.location.hostname;
        
        // Production
        if (hostname.includes('bankingapi.ru')) {
            return 'https://open.bankingapi.ru/directory';
        }
        
        // Development
        return 'http://localhost:5432';
    }

    /**
     * Инициализация виджета
     */
    window.initFeedbackWidget = function(config) {
        widgetConfig = { ...widgetConfig, ...config };
        
        // Создать элементы виджета при загрузке DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', createWidget);
        } else {
            createWidget();
        }
    };

    /**
     * Создание HTML элементов виджета
     */
    function createWidget() {
        // Проверить, не создан ли виджет уже
        if (document.getElementById('feedback-widget-btn')) {
            return;
        }

        // Стили виджета
        const style = document.createElement('style');
        style.textContent = `
            /* Плавающая кнопка */
            #feedback-widget-btn {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                cursor: pointer;
                z-index: 9998;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                transition: all 0.3s ease;
                font-family: system-ui, -apple-system, sans-serif;
            }

            #feedback-widget-btn:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
            }

            /* Модальное окно */
            #feedback-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.6);
                z-index: 9999;
                padding: 20px;
                overflow-y: auto;
                backdrop-filter: blur(4px);
            }

            #feedback-modal.active {
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .feedback-modal-content {
                background: white;
                border-radius: 12px;
                width: 100%;
                max-width: 500px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                animation: slideIn 0.3s ease;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .feedback-modal-header {
                padding: 24px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .feedback-modal-header h2 {
                margin: 0;
                font-size: 20px;
                font-weight: 600;
                color: #1f2937;
            }

            .feedback-modal-close {
                background: none;
                border: none;
                font-size: 28px;
                color: #6b7280;
                cursor: pointer;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: all 0.2s;
            }

            .feedback-modal-close:hover {
                background: #f3f4f6;
                color: #1f2937;
            }

            .feedback-modal-body {
                padding: 24px;
            }

            .feedback-form-group {
                margin-bottom: 20px;
            }

            .feedback-form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #374151;
                font-size: 14px;
            }

            .feedback-form-group label .required {
                color: #ef4444;
            }

            .feedback-form-group select,
            .feedback-form-group input,
            .feedback-form-group textarea {
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                font-family: inherit;
                transition: all 0.2s;
            }

            .feedback-form-group select:focus,
            .feedback-form-group input:focus,
            .feedback-form-group textarea:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .feedback-form-group textarea {
                resize: vertical;
                min-height: 100px;
            }

            .feedback-form-hint {
                font-size: 12px;
                color: #6b7280;
                margin-top: 4px;
            }

            .feedback-modal-footer {
                padding: 20px 24px;
                border-top: 1px solid #e5e7eb;
                display: flex;
                gap: 12px;
                justify-content: flex-end;
            }

            .feedback-btn {
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }

            .feedback-btn-secondary {
                background: #f3f4f6;
                color: #374151;
            }

            .feedback-btn-secondary:hover {
                background: #e5e7eb;
            }

            .feedback-btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            .feedback-btn-primary:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }

            .feedback-btn-primary:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }

            /* Success message */
            .feedback-success {
                text-align: center;
                padding: 40px 24px;
            }

            .feedback-success-icon {
                font-size: 64px;
                margin-bottom: 16px;
            }

            .feedback-success h3 {
                margin: 0 0 8px 0;
                color: #059669;
                font-size: 20px;
            }

            .feedback-success p {
                margin: 0;
                color: #6b7280;
            }

            /* Dark theme */
            body.dark .feedback-modal-content {
                background: #1f2937;
            }

            body.dark .feedback-modal-header {
                border-bottom-color: #374151;
            }

            body.dark .feedback-modal-header h2 {
                color: #f9fafb;
            }

            body.dark .feedback-modal-close {
                color: #9ca3af;
            }

            body.dark .feedback-modal-close:hover {
                background: #374151;
                color: #f9fafb;
            }

            body.dark .feedback-form-group label {
                color: #e5e7eb;
            }

            body.dark .feedback-form-group select,
            body.dark .feedback-form-group input,
            body.dark .feedback-form-group textarea {
                background: #374151;
                border-color: #4b5563;
                color: #f9fafb;
            }

            body.dark .feedback-form-hint {
                color: #9ca3af;
            }

            body.dark .feedback-modal-footer {
                border-top-color: #374151;
            }

            body.dark .feedback-btn-secondary {
                background: #374151;
                color: #e5e7eb;
            }

            body.dark .feedback-btn-secondary:hover {
                background: #4b5563;
            }

            /* Responsive */
            @media (max-width: 640px) {
                #feedback-widget-btn {
                    bottom: 20px;
                    right: 20px;
                    width: 50px;
                    height: 50px;
                    font-size: 20px;
                }

                .feedback-modal-content {
                    margin: 0;
                    max-height: 100vh;
                    border-radius: 0;
                }
            }
        `;
        document.head.appendChild(style);

        // Кнопка открытия виджета
        const button = document.createElement('button');
        button.id = 'feedback-widget-btn';
        button.innerHTML = '💬';
        button.title = 'Обратная связь';
        button.onclick = openFeedbackModal;
        document.body.appendChild(button);

        // Модальное окно
        const modal = document.createElement('div');
        modal.id = 'feedback-modal';
        modal.innerHTML = `
            <div class="feedback-modal-content">
                <div class="feedback-modal-header">
                    <h2>Обратная связь</h2>
                    <button class="feedback-modal-close" onclick="closeFeedbackModal()">×</button>
                </div>
                <div class="feedback-modal-body">
                    <form id="feedback-form">
                        <div class="feedback-form-group">
                            <label>
                                Тип обращения <span class="required">*</span>
                            </label>
                            <select id="feedback-type" required>
                                <option value="bug">🐛 Ошибка</option>
                                <option value="suggestion">💡 Предложение</option>
                                <option value="question">❓ Вопрос</option>
                                <option value="other">📝 Другое</option>
                            </select>
                        </div>

                        <div class="feedback-form-group">
                            <label>
                                Описание <span class="required">*</span>
                            </label>
                            <textarea id="feedback-message" required minlength="10" maxlength="5000" 
                                placeholder="Опишите вашу проблему или предложение..."></textarea>
                            <div class="feedback-form-hint">
                                Минимум 10 символов
                            </div>
                        </div>

                        <div class="feedback-form-group">
                            <label>Ваш логин</label>
                            <input type="text" id="feedback-login" placeholder="team010-1" maxlength="100">
                            <div class="feedback-form-hint">
                                Укажите ваш логин для связи (опционально)
                            </div>
                        </div>

                        <div class="feedback-form-group">
                            <label>Telegram</label>
                            <input type="text" id="feedback-telegram" placeholder="@username" maxlength="100">
                            <div class="feedback-form-hint">
                                Ваш Telegram для связи (опционально)
                            </div>
                        </div>
                    </form>
                </div>
                <div class="feedback-modal-footer">
                    <button type="button" class="feedback-btn feedback-btn-secondary" onclick="closeFeedbackModal()">
                        Отмена
                    </button>
                    <button type="submit" form="feedback-form" class="feedback-btn feedback-btn-primary" id="feedback-submit">
                        Отправить
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Закрытие при клике вне модального окна
        modal.onclick = function(e) {
            if (e.target === modal) {
                closeFeedbackModal();
            }
        };

        // Обработчик отправки формы
        const form = document.getElementById('feedback-form');
        form.onsubmit = handleSubmit;
    }

    /**
     * Открыть модальное окно
     */
    function openFeedbackModal() {
        const modal = document.getElementById('feedback-modal');
        modal.classList.add('active');
        
        // Автозаполнение логина, если доступен
        if (widgetConfig.participantLogin) {
            document.getElementById('feedback-login').value = widgetConfig.participantLogin;
        }
    }

    /**
     * Закрыть модальное окно
     */
    window.closeFeedbackModal = function() {
        const modal = document.getElementById('feedback-modal');
        modal.classList.remove('active');
        
        // Сброс формы
        document.getElementById('feedback-form').reset();
    };

    /**
     * Отправка формы
     */
    async function handleSubmit(e) {
        e.preventDefault();

        const submitBtn = document.getElementById('feedback-submit');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Отправка...';

        const feedbackData = {
            feedback_type: document.getElementById('feedback-type').value,
            message: document.getElementById('feedback-message').value,
            participant_login: document.getElementById('feedback-login').value || null,
            telegram: document.getElementById('feedback-telegram').value || null,
            page_url: window.location.href,
            bank_code: widgetConfig.bankCode,
            ui_type: widgetConfig.uiType
        };

        try {
            const response = await fetch(`${widgetConfig.directoryUrl}/api/feedback/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(feedbackData)
            });

            if (response.ok) {
                showSuccess();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка отправки');
            }
        } catch (error) {
            console.error('Feedback error:', error);
            alert('Ошибка отправки обращения: ' + error.message);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Отправить';
        }
    }

    /**
     * Показать сообщение об успехе
     */
    function showSuccess() {
        const modalBody = document.querySelector('.feedback-modal-body');
        const modalFooter = document.querySelector('.feedback-modal-footer');
        
        modalBody.innerHTML = `
            <div class="feedback-success">
                <div class="feedback-success-icon">✅</div>
                <h3>Спасибо за обращение!</h3>
                <p>Мы рассмотрим ваше сообщение в ближайшее время</p>
            </div>
        `;
        
        modalFooter.innerHTML = `
            <button type="button" class="feedback-btn feedback-btn-primary" onclick="closeFeedbackModal()">
                Закрыть
            </button>
        `;

        // Автозакрытие через 3 секунды
        setTimeout(() => {
            closeFeedbackModal();
            // Восстановить форму
            setTimeout(() => {
                location.reload();
            }, 300);
        }, 3000);
    }

})();

