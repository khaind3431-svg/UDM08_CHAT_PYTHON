(function () {
  window.ChatNetwork.whenApiReady((api) => {
    const loginForm = document.getElementById('form-login');
    const loginError = document.getElementById('login-error');
    const loginSubmitBtn = document.getElementById('login-submit');
    const registerForm = document.getElementById('form-register');
    const serverAddressInput = document.getElementById('server-address');
    const serverStatus = document.getElementById('server-status');

    function showError(message) {
      if (!loginError) return;
      loginError.textContent = message || '';
      loginError.style.display = message ? 'block' : 'none';
    }

    function setSubmitting(isSubmitting) {
      if (loginSubmitBtn) loginSubmitBtn.disabled = isSubmitting;
    }

    function showServerStatus(text, kind) {
      // kind: 'connecting' | 'error' | ''
      if (!serverStatus) return;
      serverStatus.textContent = text || '';
      const colorVar = kind === 'error' ? 'var(--danger)'
        : kind === 'connecting' ? 'var(--text-faint)'
        : 'var(--online, #2e9e5b)';
      serverStatus.style.color = colorVar;
    }

    // Tach chuoi "host:port" nguoi dung nhap thanh { host, port }.
    // Tra ve { ok:false, error } neu dinh dang sai hoac port ngoai
    // khoang hop le, de bao loi ro rang TRUOC KHI thu ket noi.
    function parseServerAddress() {
      const raw = (serverAddressInput ? serverAddressInput.value : '').trim();
      if (!raw) {
        return { ok: false, error: 'Vui lòng nhập địa chỉ Server (IP:Port).' };
      }
      const lastColon = raw.lastIndexOf(':');
      if (lastColon <= 0 || lastColon === raw.length - 1) {
        return { ok: false, error: 'Định dạng phải là IP:Port, ví dụ 127.0.0.1:5000.' };
      }
      const host = raw.slice(0, lastColon).trim();
      const portText = raw.slice(lastColon + 1).trim();
      const port = Number(portText);
      if (!host) {
        return { ok: false, error: 'Thiếu địa chỉ IP/host của Server.' };
      }
      if (!Number.isInteger(port) || port < 1 || port > 65535) {
        return { ok: false, error: 'Port không hợp lệ (phải là số từ 1 đến 65535).' };
      }
      return { ok: true, host, port };
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

        const server = parseServerAddress();
        if (!server.ok) {
          showServerStatus(server.error, 'error');
          return;
        }

        showError('');
        showServerStatus(`Đang kết nối tới ${server.host}:${server.port}...`, 'connecting');
        setSubmitting(true);
        api.login(username, password, server.host, server.port).then((result) => {
          if (!result.ok) {
            setSubmitting(false);
            showServerStatus('', '');
            showError(result.error);
          } else {
            showServerStatus('Đã kết nối, đang đăng nhập...', 'connecting');
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

        const server = parseServerAddress();
        if (!server.ok) {
          showServerStatus(server.error, 'error');
          return;
        }

        showError('');
        showServerStatus(`Đang kết nối tới ${server.host}:${server.port}...`, 'connecting');
        api.register(displayName, username, password, confirm, server.host, server.port).then((result) => {
          showServerStatus('', '');
          if (!result.ok) showError(result.error);
        });
      });
    }

    window.addEventListener('chat:LOGIN_OK', () => {
      setSubmitting(false);
      showServerStatus('Kết nối thành công.', '');
      api.navigate_to_chat();
    });

    window.addEventListener('chat:LOGIN_ERR', (event) => {
      setSubmitting(false);
      showServerStatus('', '');
      showError(event.detail.join('|'));
    });

    window.addEventListener('chat:REGISTER_OK', () => {
      showError('');
      const loginTab = document.querySelector('.auth-tabs button[data-target="form-login"]');
      if (loginTab) loginTab.click();
      alert('Đăng ký thành công! Hãy đăng nhập.');
    });

    window.addEventListener('chat:REGISTER_ERR', (event) => {
      showServerStatus('', '');
      showError(event.detail.join('|'));
    });

    window.addEventListener('chat:disconnected', () => {
      setSubmitting(false);
      showServerStatus('', '');
      showError('Mất kết nối tới server. Kiểm tra lại địa chỉ Server và server đã chạy chưa.');
    });
  });
})();