(function () {
  const BROADCAST_TARGET = '__broadcast__';

  window.ChatNetwork.whenApiReady((api) => {
    const state = {
      username: null,
      currentTarget: BROADCAST_TARGET,
      onlineUsers: [],
      pendingReplyId: null,
      pendingForwardId: null,
    };

    const elements = {
      currentUsername: document.getElementById('current-username'),
      onlineCount: document.getElementById('online-count'),
      onlineUsersList: document.getElementById('online-users-list'),
      broadcastItem: document.querySelector('.contact-item[data-target="__broadcast__"]'),
      chatHeaderName: document.querySelector('.chat-header .identity .name'),
      chatHeaderStatus: document.querySelector('.chat-header .identity .status'),
      messageScroll: document.getElementById('message-scroll'),
      composerInput: document.getElementById('composer-input'),
      sendBtn: document.getElementById('send-btn'),
      imageBtn: document.getElementById('image-btn'),
      imageInput: document.getElementById('image-input'),
      replyBanner: document.getElementById('reply-banner'),
      replyBannerName: document.getElementById('reply-banner-name'),
      replyBannerSnippet: document.getElementById('reply-banner-snippet'),
      replyCancelBtn: document.getElementById('reply-cancel-btn'),
      forwardModal: document.querySelector('.modal-backdrop'),
      forwardList: document.getElementById('forward-list'),
      forwardQuoted: document.getElementById('forward-quoted'),
      forwardConfirmBtn: document.getElementById('forward-confirm-btn'),
    };

    init();

    async function init() {
      const session = await api.get_state();
      state.username = session.username;
      state.onlineUsers = session.online_users || [];

      if (elements.currentUsername) elements.currentUsername.textContent = state.username || 'Bạn';

      renderOnlineList();
      selectTarget(BROADCAST_TARGET);
      bindBroadcastItem();
      bindComposer();
      bindImageUpload();
      bindReplyCancel();
      bindForwardConfirm();
      bindLogout();
    }

    function renderOnlineList() {
      if (!elements.onlineUsersList) return;
      elements.onlineUsersList.innerHTML = '';

      const others = state.onlineUsers.filter((u) => u !== state.username);
      if (elements.onlineCount) elements.onlineCount.textContent = String(others.length);

      others.forEach((username) => {
        const item = document.createElement('div');
        item.className = 'contact-item';
        item.dataset.target = username;
        if (username === state.currentTarget) item.classList.add('active');

        const initials = username.slice(0, 2).toUpperCase();
        item.innerHTML = `
          <span class="avatar status" style="width:46px;height:46px">${initials}</span>
          <div class="meta">
            <div class="row-top"><span class="name">${escapeHtml(username)}</span></div>
            <div class="preview">Nhấn để nhắn riêng</div>
          </div>`;
        item.addEventListener('click', () => selectTarget(username));
        elements.onlineUsersList.appendChild(item);
      });
    }

    function bindBroadcastItem() {
      if (elements.broadcastItem) {
        elements.broadcastItem.addEventListener('click', () => selectTarget(BROADCAST_TARGET));
      }
    }

    function selectTarget(target) {
      state.currentTarget = target;

      document.querySelectorAll('.sidebar .contact-item').forEach((item) => {
        item.classList.toggle('active', item.dataset.target === target);
      });

      if (elements.chatHeaderName) {
        elements.chatHeaderName.textContent = target === BROADCAST_TARGET ? 'Tất cả mọi người' : target;
      }
      if (elements.chatHeaderStatus) {
        elements.chatHeaderStatus.innerHTML = target === BROADCAST_TARGET
          ? 'Tin nhắn gửi tới mọi người đang online'
          : '<span class="dot"></span>Đang nhắn riêng';
      }

      if (elements.messageScroll) elements.messageScroll.innerHTML = '';
      cancelReply();
    }

    function bindComposer() {
      if (elements.sendBtn) elements.sendBtn.addEventListener('click', sendCurrentInput);
      if (elements.composerInput) {
        elements.composerInput.addEventListener('keydown', (event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            sendCurrentInput();
          }
        });
      }
    }

    function sendCurrentInput() {
      const input = elements.composerInput;
      if (!input) return;
      const content = input.value.trim();
      if (!content) return;

      if (state.pendingReplyId !== null) {
        api.send_reply(state.pendingReplyId, content);
        cancelReply();
      } else if (state.currentTarget === BROADCAST_TARGET) {
        api.send_message(content);
      } else {
        api.send_private(state.currentTarget, content);
      }
      input.value = '';
    }

    function bindImageUpload() {
      if (!elements.imageBtn || !elements.imageInput) return;
      elements.imageBtn.addEventListener('click', () => elements.imageInput.click());
      elements.imageInput.addEventListener('change', () => {
        const file = elements.imageInput.files && elements.imageInput.files[0];
        elements.imageInput.value = '';
        if (!file) return;
        const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowed.includes(file.type)) {
          appendSystemLine('Lỗi: Chỉ chọn ảnh JPG, PNG, GIF hoặc WEBP.');
          return;
        }
        if (file.size > 2 * 1024 * 1024) {
          appendSystemLine('Lỗi: Ảnh không được vượt quá 2 MB.');
          return;
        }

        const reader = new FileReader();
        reader.onload = () => {
          const result = String(reader.result || '');
          const comma = result.indexOf(',');
          if (comma < 0) return;
          api.send_image(state.currentTarget, file.name, file.type, result.slice(comma + 1));
        };
        reader.onerror = () => appendSystemLine('Lỗi: Không đọc được ảnh.');
        reader.readAsDataURL(file);
      });
    }

    window.addEventListener('chat:MESSAGE', (event) => {
      const [sender, content] = event.detail;
      if (sender === 'SYSTEM') {
        if (state.currentTarget === BROADCAST_TARGET) appendSystemLine(content);
        return;
      }
      if (state.currentTarget === BROADCAST_TARGET) {
        appendBubble({ sender, content, isOwn: sender === state.username, messageId: null });
      }
    });

    window.addEventListener('chat:PRIVATE', (event) => {
      const [sender, rawContent, rawId] = event.detail;
      const messageId = rawId && rawId !== '0' ? rawId : null;

      if (sender === state.username) {
        const match = /^To (.+?): ([\s\S]*)$/.exec(rawContent);
        if (!match) return;
        const [, target, content] = match;
        if (state.currentTarget === target) {
          appendBubble({ sender, content, isOwn: true, messageId });
        }
      } else if (state.currentTarget === sender) {
        appendBubble({ sender, content: rawContent, isOwn: false, messageId });
      }
    });

    window.addEventListener('chat:REPLY', (event) => {
      const [sender, content, , originalSender, originalSnippet] = event.detail;
      if (state.currentTarget !== BROADCAST_TARGET) return;
      appendBubble({
        sender,
        content,
        isOwn: sender === state.username,
        messageId: null,
        replyTo: { name: originalSender, snippet: originalSnippet },
      });
    });

    window.addEventListener('chat:IMAGE', (event) => {
      const [sender, target, fileName, mimeType, dataBase64] = event.detail;
      const isOwn = sender === state.username;
      const belongsHere = target === BROADCAST_TARGET
        ? state.currentTarget === BROADCAST_TARGET
        : (isOwn ? state.currentTarget === target : state.currentTarget === sender);
      if (belongsHere) appendImageBubble({ sender, fileName, mimeType, dataBase64, isOwn });
    });

    window.addEventListener('chat:ONLINE', (event) => {
      const [csv] = event.detail;
      state.onlineUsers = csv ? csv.split(',').filter(Boolean) : [];
      renderOnlineList();
    });

    window.addEventListener('chat:ERROR', (event) => {
      appendSystemLine('Lỗi: ' + event.detail.join('|'));
    });

    window.addEventListener('chat:disconnected', () => {
      appendSystemLine('Mất kết nối tới server.');
    });

    function appendBubble({ sender, content, isOwn, messageId, replyTo }) {
      if (!elements.messageScroll) return;

      const row = document.createElement('div');
      row.className = 'msg-row ' + (isOwn ? 'out' : 'in');
      if (messageId) row.dataset.messageId = messageId;

      const avatarHtml = isOwn ? '' :
        `<span class="avatar" style="width:30px;height:30px;font-size:11px">${sender.slice(0, 2).toUpperCase()}</span>`;
      const senderNameHtml = isOwn ? '' : `<span class="sender-name">${escapeHtml(sender)}</span>`;

      const replyPreviewHtml = replyTo ? `
        <div class="reply-preview">
          <div class="content">
            <div class="to-name">${escapeHtml(replyTo.name || '')}</div>
            <div class="snippet">${escapeHtml(replyTo.snippet || '')}</div>
          </div>
        </div>` : '';

      const actionsHtml = messageId ? `
        <div class="msg-actions">
          <button data-action="reply" aria-label="Trả lời">↩</button>
          <button data-action="forward" aria-label="Chuyển tiếp">➦</button>
        </div>` : '';

      row.innerHTML = `
        ${avatarHtml}
        <div class="msg-col">
          ${senderNameHtml}
          ${replyPreviewHtml}
          <div class="bubble-wrap">
            <div class="bubble">${escapeHtml(content)}</div>
            ${actionsHtml}
          </div>
          <span class="msg-meta">${formatTime()}</span>
        </div>`;

      if (messageId) {
        const replyBtn = row.querySelector('[data-action="reply"]');
        const forwardBtn = row.querySelector('[data-action="forward"]');
        if (replyBtn) replyBtn.addEventListener('click', () => startReply(messageId, sender, content));
        if (forwardBtn) forwardBtn.addEventListener('click', () => openForwardModal(messageId, content));
      }

      elements.messageScroll.appendChild(row);
      elements.messageScroll.scrollTop = elements.messageScroll.scrollHeight;
    }

    function appendSystemLine(text) {
      if (!elements.messageScroll) return;
      const div = document.createElement('div');
      div.className = 'date-divider';
      div.textContent = text;
      elements.messageScroll.appendChild(div);
      elements.messageScroll.scrollTop = elements.messageScroll.scrollHeight;
    }

    function appendImageBubble({ sender, fileName, mimeType, dataBase64, isOwn }) {
      if (!elements.messageScroll) return;
      const row = document.createElement('div');
      row.className = 'msg-row ' + (isOwn ? 'out' : 'in');

      if (!isOwn) {
        const avatar = document.createElement('span');
        avatar.className = 'avatar';
        avatar.style.cssText = 'width:30px;height:30px;font-size:11px';
        avatar.textContent = sender.slice(0, 2).toUpperCase();
        row.appendChild(avatar);
      }

      const col = document.createElement('div');
      col.className = 'msg-col';
      if (!isOwn) {
        const name = document.createElement('span');
        name.className = 'sender-name';
        name.textContent = sender;
        col.appendChild(name);
      }

      const bubble = document.createElement('div');
      bubble.className = 'bubble image-bubble';
      const img = document.createElement('img');
      img.className = 'chat-image';
      img.src = `data:${mimeType};base64,${dataBase64}`;
      img.alt = fileName || 'Ảnh đã gửi';
      img.title = fileName || 'Ảnh đã gửi';
      img.addEventListener('click', () => window.open(img.src, '_blank'));
      bubble.appendChild(img);
      col.appendChild(bubble);

      const meta = document.createElement('span');
      meta.className = 'msg-meta';
      meta.textContent = formatTime();
      col.appendChild(meta);
      row.appendChild(col);
      elements.messageScroll.appendChild(row);
      elements.messageScroll.scrollTop = elements.messageScroll.scrollHeight;
    }

    function startReply(messageId, sender, content) {
      state.pendingReplyId = messageId;
      if (elements.replyBanner) elements.replyBanner.style.display = 'flex';
      if (elements.replyBannerName) elements.replyBannerName.textContent = 'Đang trả lời ' + sender;
      if (elements.replyBannerSnippet) elements.replyBannerSnippet.textContent = content;
      if (elements.composerInput) elements.composerInput.focus();
    }

    function cancelReply() {
      state.pendingReplyId = null;
      if (elements.replyBanner) elements.replyBanner.style.display = 'none';
    }

    function bindReplyCancel() {
      if (elements.replyCancelBtn) elements.replyCancelBtn.addEventListener('click', cancelReply);
    }

    function openForwardModal(messageId, content) {
      state.pendingForwardId = messageId;
      if (elements.forwardQuoted) elements.forwardQuoted.textContent = content;

      if (elements.forwardList) {
        elements.forwardList.innerHTML = '';
        state.onlineUsers
          .filter((u) => u !== state.username)
          .forEach((username) => {
            const item = document.createElement('div');
            item.className = 'contact-item';
            item.dataset.target = username;
            item.innerHTML = `
              <span class="avatar status" style="width:46px;height:46px">${username.slice(0, 2).toUpperCase()}</span>
              <div class="meta"><div class="row-top"><span class="name">${escapeHtml(username)}</span></div></div>`;
            item.addEventListener('click', () => {
              elements.forwardList.querySelectorAll('.contact-item').forEach((i) => i.classList.remove('selected'));
              item.classList.add('selected');
            });
            elements.forwardList.appendChild(item);
          });
      }

      if (elements.forwardModal) elements.forwardModal.style.display = 'flex';
    }

    function bindForwardConfirm() {
      if (!elements.forwardConfirmBtn) return;
      elements.forwardConfirmBtn.addEventListener('click', () => {
        const selected = elements.forwardList
          ? elements.forwardList.querySelector('.contact-item.selected')
          : null;
        if (selected && state.pendingForwardId !== null) {
          api.send_forward(state.pendingForwardId, selected.dataset.target);
        }
        state.pendingForwardId = null;
        if (elements.forwardModal) elements.forwardModal.style.display = 'none';
      });
    }

    function bindLogout() {
      const logoutBtn = document.getElementById('logout-btn');
      if (!logoutBtn) return;
      logoutBtn.addEventListener('click', () => {
        api.logout();
        api.navigate_to_login();
      });
    }

    function formatTime() {
      const now = new Date();
      return String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text == null ? '' : text;
      return div.innerHTML;
    }
  });
})();
