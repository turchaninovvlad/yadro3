const FeedbackForm = (() => {

    let config = {
        validTypes: [],
        maxMessageLength: 1000
    };


    const elements = {
        form: null,
        feedbackType: null,
        fullName: null,
        email: null,
        phone: null,
        message: null,
        fileInput: null,
        charsLeft: null,
        serverError: null
    };


    const errorMessages = {
        feedbackType: 'Пожалуйста, выберите тип обращения',
        fullName: 'ФИО должно быть от 2 до 100 символов',
        email: 'Введите корректный email',
        phone: 'Формат: +7 999 123-45-67 (от 5 до 20 символов)',
        message: 'Сообщение должно быть от 10 до 1000 символов',
        file: {
            size: 'Файл слишком большой. Максимальный размер: 5MB',
            type: 'Неподдерживаемый тип файла. Разрешены: JPG, PNG, PDF'
        },
        server: 'Произошла ошибка при отправке формы. Пожалуйста, попробуйте позже.'
    };


    const escapeHtml = (unsafe) => {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    const validatePhone = (phone) => {
        if (!phone) return true;
        const phoneRegex = /^\+?[\d\s\-()]{5,20}$/;
        const cleaned = phone.replace(/[^\d+]/g, '');
        return phoneRegex.test(phone) && cleaned.length >= 5 && cleaned.length <= 15;
    };

    const showError = (element, errorElement, message) => {
        element.classList.add('invalid');
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    };

    const hideError = (element, errorElement) => {
        element.classList.remove('invalid');
        errorElement.classList.add('hidden');
    };

    const validateForm = () => {
        let isValid = true;
        const formData = new FormData();

        if (!config.validTypes.includes(elements.feedbackType.value)) {
            showError(elements.feedbackType, elements.feedbackTypeError, errorMessages.feedbackType);
            isValid = false;
        } else {
            formData.append('feedback_type', elements.feedbackType.value);
            hideError(elements.feedbackType, elements.feedbackTypeError);
        }

        const fullName = escapeHtml(elements.fullName.value.trim());
        if (fullName.length < 2 || fullName.length > 100) {
            showError(elements.fullName, elements.fullNameError, errorMessages.fullName);
            isValid = false;
        } else {
            formData.append('full_name', fullName);
            hideError(elements.fullName, elements.fullNameError);
        }

        const email = escapeHtml(elements.email.value.trim());
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showError(elements.email, elements.emailError, errorMessages.email);
            isValid = false;
        } else {
            formData.append('email', email);
            hideError(elements.email, elements.emailError);
        }

        const phone = escapeHtml(elements.phone.value.trim());
        if (phone && !validatePhone(phone)) {
            showError(elements.phone, elements.phoneError, errorMessages.phone);
            isValid = false;
        } else if (phone) {
            formData.append('phone', phone);
            hideError(elements.phone, elements.phoneError);
        }

        const message = escapeHtml(elements.message.value.trim());
        if (message.length < 10 || message.length > config.maxMessageLength) {
            showError(elements.message, elements.messageError, errorMessages.message);
            isValid = false;
        } else {
            formData.append('message', message);
            hideError(elements.message, elements.messageError);
        }

        if (elements.fileInput.files.length > 0) {
            const file = elements.fileInput.files[0];
            const validTypes = ['image/jpeg', 'image/png', 'application/pdf'];
            
            if (file.size > 5 * 1024 * 1024) {
                showError(elements.fileInput, elements.fileError, errorMessages.file.size);
                isValid = false;
            } else if (!validTypes.includes(file.type)) {
                showError(elements.fileInput, elements.fileError, errorMessages.file.type);
                isValid = false;
            } else {
                formData.append('file', file);
                hideError(elements.fileInput, elements.fileError);
            }
        }

        return isValid ? formData : null;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        elements.serverError.classList.add('hidden');

        const formData = validateForm();
        if (!formData) {
            window.scrollTo(0, 0);
            return;
        }

        try {
            const response = await fetch('/feedback/submit', {
                method: 'POST',
                body: formData
            });

            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            const result = await response.json();
            
            if (response.status === 422 || response.status === 413 || response.status === 415) {
                elements.serverError.textContent = result.detail || errorMessages.server;
                elements.serverError.classList.remove('hidden');
                window.scrollTo(0, 0);
            } else if (!response.ok) {
                throw new Error('Server error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            elements.serverError.textContent = errorMessages.server;
            elements.serverError.classList.remove('hidden');
            window.scrollTo(0, 0);
        }
    };

    const initEventListeners = () => {
        elements.form.addEventListener('submit', handleSubmit);
        
        elements.message.addEventListener('input', () => {
            const remaining = config.maxMessageLength - elements.message.value.length;
            elements.charsLeft.textContent = remaining;
        });

        document.querySelectorAll('input, textarea, select').forEach(input => {
            input.addEventListener('input', function() {
                const errorElement = document.getElementById(`${this.id}_error`);
                if (errorElement) {
                    hideError(this, errorElement);
                }
            });
        });
    };

    return {
        init: (data) => {
            config.validTypes = data.types.map(type => type.value);
            
            elements.form = document.getElementById('feedbackForm');
            elements.feedbackType = document.getElementById('feedback_type');
            elements.fullName = document.getElementById('full_name');
            elements.email = document.getElementById('email');
            elements.phone = document.getElementById('phone');
            elements.message = document.getElementById('message');
            elements.fileInput = document.getElementById('file');
            elements.charsLeft = document.getElementById('charsLeft');
            elements.serverError = document.getElementById('serverError');
            
            elements.feedbackTypeError = document.getElementById('feedback_type_error');
            elements.fullNameError = document.getElementById('full_name_error');
            elements.emailError = document.getElementById('email_error');
            elements.phoneError = document.getElementById('phone_error');
            elements.messageError = document.getElementById('message_error');
            elements.fileError = document.getElementById('file_error');
            
            elements.feedbackTypeError.textContent = errorMessages.feedbackType;
            elements.fullNameError.textContent = errorMessages.fullName;
            elements.emailError.textContent = errorMessages.email;
            elements.phoneError.textContent = errorMessages.phone;
            elements.messageError.textContent = errorMessages.message;
            
            initEventListeners();
        }
    };
})();
