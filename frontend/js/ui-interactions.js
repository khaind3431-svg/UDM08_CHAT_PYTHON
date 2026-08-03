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

  // ---- Forward modal ----
  document.querySelectorAll('[data-action="forward"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const modal = document.querySelector('.modal-backdrop');
      if (modal) modal.style.display = 'flex';
    });
  });

  document.querySelectorAll('[data-action="close-modal"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const modal = document.querySelector('.modal-backdrop');
      if (modal) modal.style.display = 'none';
    });
  });

  // ---- Contact selection highlight ----
  document.querySelectorAll('.contact-item').forEach((item) => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.contact-item').forEach((i) => i.classList.remove('active'));
      item.classList.add('active');
      item.classList.remove('unread');
      const badge = item.querySelector('.unread-badge');
      if (badge) badge.remove();
    });
  });
})();
