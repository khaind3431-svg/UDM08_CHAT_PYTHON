(function () {
  window.ChatNetwork.whenApiReady((api) => {
    const loginForm = document.getElementById('form-login');
    const loginError = document.getElementById('login-error');
    const loginSubmitBtn = document.getElementById('login-submit');
    const registerForm = document.getElementById('form-register');

    function showError(message) {
      if (!loginError) return;
      loginError.textContent = message || '';
      loginError.style.display = message ? 'block' : 'none';
    }

    function setSubmitting(isSubmitting) {
      if (loginSubmitBtn) loginSubmitBtn.disabled = isSubmitting;
    }

    if (loginForm) {
      loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;

        if (!username || !password) {
          showError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.');
          return;
        }

        showError('');
        setSubmitting(true);
        api.login(username, password).then((result) => {
          if (!result.ok) {
            setSubmitting(false);
            showError(result.error);
          }
        });
      });
    }

    if (registerForm) {
      registerForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const displayName = document.getElementById('register-displayname').value.trim();
        const username = document.getElementById('register-username').value.trim();
        const password = document.getElementById('register-password').value;
        const confirm = document.getElementById('register-confirm').value;

        if (!displayName || !username || !password || !confirm) {
          showError('Vui lòng nhập đầy đủ thông tin đăng ký.');
          return;
        }

        showError('');
        api.register(displayName, username, password, confirm).then((result) => {
          if (!result.ok) showError(result.error);
        });
      });
    }

    window.addEventListener('chat:LOGIN_OK', () => {
      setSubmitting(false);
      api.navigate_to_chat();
    });

    window.addEventListener('chat:LOGIN_ERR', (event) => {
      setSubmitting(false);
      showError(event.detail.join('|'));
    });

    window.addEventListener('chat:REGISTER_OK', () => {
      showError('');
      const loginTab = document.querySelector('.auth-tabs button[data-target="form-login"]');
      if (loginTab) loginTab.click();
      alert('Đăng ký thành công! Hãy đăng nhập.');
    });

    window.addEventListener('chat:REGISTER_ERR', (event) => {
      showError(event.detail.join('|'));
    });

    window.addEventListener('chat:disconnected', () => {
      setSubmitting(false);
      showError('Mất kết nối tới server. Kiểm tra lại server đã chạy chưa.');
    });
  });
})();