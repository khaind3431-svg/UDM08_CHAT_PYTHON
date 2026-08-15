// ===========================================================
// WIRELINE — UI-only interactions
// Handles purely visual state (which tab/panel/modal is open).
// Sending, receiving, replying "for real" and forwarding "for
// real" belong to the networking layer and are NOT implemented
// here — these handlers only demonstrate the intended GUI.
// ===========================================================

(function () {
  // ---- Auth tabs (login.html) ----
  const authTabs = document.querySelectorAll('.auth-tabs button');
  authTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      authTabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      const target = tab.dataset.target;
      document.querySelectorAll('.auth-form').forEach((f) => {
        f.style.display = f.id === target ? 'flex' : 'none';
      });
    });
  });

  // ---- Emoji picker (chat.html) ----
  const emojiBtn = document.querySelector('[data-action="toggle-emoji"]');
  const emojiPicker = document.querySelector('.emoji-picker');
  if (emojiBtn && emojiPicker) {
    emojiBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      emojiPicker.style.display = emojiPicker.style.display === 'block' ? 'none' : 'block';
    });
    document.addEventListener('click', (e) => {
      if (!emojiPicker.contains(e.target) && e.target !== emojiBtn) {
        emojiPicker.style.display = 'none';
      }
    });
    emojiPicker.querySelectorAll('.grid button').forEach((btn) => {
      btn.addEventListener('click', () => {
        const input = document.querySelector('.composer input[type="text"]');
        if (input) input.value += btn.textContent;
      });
    });
  }

  // ---- Reply banner (composer) ----
  document.querySelectorAll('[data-action="reply"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const banner = document.querySelector('.reply-banner');
      if (banner) banner.style.display = 'flex';
    });
  });

  const replyClose = document.querySelector('.reply-banner .close-btn');
  if (replyClose) {
    replyClose.addEventListener('click', () => {
      replyClose.closest('.reply-banner').style.display = 'none';
    });
  }

  // ---- Forward modal: mở/đóng ----
  const forwardModal = document.querySelector('.modal-backdrop');

  document.querySelectorAll('[data-action="forward"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (forwardModal) forwardModal.style.display = 'flex';
    });
  });

  document.querySelectorAll('[data-action="close-modal"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (forwardModal) forwardModal.style.display = 'none';
    });
  });

  // Nút xác nhận "Chuyển tiếp" trong modal — bấm là đóng modal lại
  // (phần gửi thật cho ai sẽ do JS nối mạng xử lý sau, không phải ở đây).
  const forwardConfirmBtn = document.getElementById('forward-confirm-btn');
  if (forwardConfirmBtn) {
    forwardConfirmBtn.addEventListener('click', () => {
      if (forwardModal) forwardModal.style.display = 'none';
    });
  }

  // Chọn người nhận trong modal Forward — chỉ tô sáng phần tử được
  // bấm bên TRONG modal, không đụng gì tới danh sách liên hệ ở sidebar
  // (2 khu vực này tình cờ dùng chung class .contact-item).
  document.querySelectorAll('.forward-list .contact-item').forEach((item) => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.forward-list .contact-item').forEach((i) => i.classList.remove('selected'));
      item.classList.add('selected');
    });
  });

  // ---- Chọn liên hệ ở sidebar (tô active + xoá badge chưa đọc) ----
  // Chỉ áp dụng cho .contact-item nằm trong sidebar, KHÔNG áp dụng cho
  // .contact-item bên trong modal Forward.
  document.querySelectorAll('.sidebar .contact-item').forEach((item) => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.sidebar .contact-item').forEach((i) => i.classList.remove('active'));
      item.classList.add('active');
      item.classList.remove('unread');
      const badge = item.querySelector('.unread-badge');
      if (badge) badge.remove();
    });
  });
})();