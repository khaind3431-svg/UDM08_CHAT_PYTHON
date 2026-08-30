(function () {
  window.ChatNetwork.whenApiReady((api) => {
    const state = {
      username: null,
      currentTarget: null,
      onlineUsers: [],
      pendingReplyId: null,
      pendingForwardId: null,
      pendingRequestCount: 0,
      friends: [],
    };

    const elements = {
      currentUsername: document.getElementById('current-username'),
      friendsList: document.getElementById('friends-list'),
      friendsCount: document.getElementById('friends-count'),
      chatHeaderName: document.querySelector('.chat-header .identity .name'),
      chatHeaderStatus: document.querySelector('.chat-header .identity .status'),
      chatHeaderAvatar: document.querySelector('.chat-header > .avatar'),
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
      // Ket ban + Profile
      friendAddInput: document.getElementById('friend-add-input'),
      friendAddBtn: document.getElementById('friend-add-btn'),
      friendAddStatus: document.getElementById('friend-add-status'),
      friendRequestsBtn: document.getElementById('friend-requests-btn'),
      friendRequestsBadge: document.getElementById('friend-requests-badge'),
      friendRequestsModal: document.getElementById('friend-requests-modal-backdrop'),
      friendRequestsList: document.getElementById('friend-requests-list'),
      friendRequestsEmpty: document.getElementById('friend-requests-empty'),
      friendRequestsClose: document.getElementById('friend-requests-close'),
      profileModal: document.getElementById('profile-modal-backdrop'),
      profileModalClose: document.getElementById('profile-modal-close'),
      profileAvatar: document.getElementById('profile-avatar'),
      profileFullname: document.getElementById('profile-fullname'),
      profileUsername: document.getElementById('profile-username'),
      profileStatus: document.getElementById('profile-status'),
      profileBio: document.getElementById('profile-bio'),
      profileActions: document.getElementById('profile-actions'),
    };

    init();

    async function init() {
      const session = await api.get_state();
      state.username = session.username;
      state.onlineUsers = session.online_users || [];

      if (elements.currentUsername) elements.currentUsername.textContent = state.username || 'Bạn';

      renderEmptyState();
      bindComposer();
      bindImageUpload();
      bindReplyCancel();
      bindForwardConfirm();
      bindLogout();
      bindFriendAdd();
      bindFriendRequestsPanel();
      bindProfileModal();
      api.get_friend_requests();
      api.get_friend_list();
    }

    function renderEmptyState() {
      if (elements.chatHeaderName) elements.chatHeaderName.textContent = 'Chọn một người bạn để trò chuyện';
      if (elements.chatHeaderStatus) elements.chatHeaderStatus.innerHTML = '&nbsp;';
      if (elements.messageScroll) elements.messageScroll.innerHTML = '';
    }

    function renderFriendsList() {
      if (!elements.friendsList) return;
      elements.friendsList.innerHTML = '';

      if (elements.friendsCount) elements.friendsCount.textContent = String(state.friends.length);

      if (state.friends.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'empty-hint';
        empty.textContent = 'Bạn chưa có bạn bè nào.';
        elements.friendsList.appendChild(empty);
        return;
      }

      state.friends.forEach((username) => {
        const isOnline = state.onlineUsers.includes(username);
        const item = document.createElement('div');
        item.className = 'contact-item';
        item.dataset.target = username;
        if (username === state.currentTarget) item.classList.add('active');

        const initials = username.slice(0, 2).toUpperCase();
        const statusClass = isOnline ? 'avatar status' : 'avatar status offline';
        item.innerHTML = `
          <span class="${statusClass}" style="width:46px;height:46px">${initials}</span>
          <div class="meta">
            <div class="row-top"><span class="name">${escapeHtml(username)}</span></div>
            <div class="preview">${isOnline ? 'Đang hoạt động' : 'Ngoại tuyến'}</div>
          </div>
          <button class="info-btn" data-action="view-profile" aria-label="Xem thông tin">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
          </button>`;
        item.addEventListener('click', () => selectTarget(username));
        const infoBtn = item.querySelector('[data-action="view-profile"]');
        if (infoBtn) {
          infoBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            openProfile(username);
          });
        }
        elements.friendsList.appendChild(item);
      });
    }

    function selectTarget(target) {
      state.currentTarget = target;

      document.querySelectorAll('.sidebar .contact-item').forEach((item) => {
        item.classList.toggle('active', item.dataset.target === target);
      });

      const isOnline = state.onlineUsers.includes(target);
      if (elements.chatHeaderName) elements.chatHeaderName.textContent = target;
      if (elements.chatHeaderStatus) {
        elements.chatHeaderStatus.innerHTML = isOnline
          ? '<span class="dot"></span>Đang hoạt động'
          : 'Ngoại tuyến';
      }
      if (elements.chatHeaderAvatar) {
        elements.chatHeaderAvatar.textContent = target.slice(0, 2).toUpperCase();
        elements.chatHeaderAvatar.classList.toggle('offline', !isOnline);
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
      if (!input || !state.currentTarget) return;
      const content = input.value.trim();
      if (!content) return;

      if (state.pendingReplyId !== null) {
        api.send_reply(state.pendingReplyId, content);
        cancelReply();
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
        if (!file || !state.currentTarget) return;
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

    // Ghi chu: khong con lang nghe chat:MESSAGE (kenh broadcast) nua vi
    // da bo phong chat chung. Thong bao SYSTEM (ai vao/roi phong) tu
    // server gui qua kenh nay gio khong co noi nao de hien, nen bo qua.

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
      // Luu y: backend hien REPLY dang gui toi TAT CA nguoi dang online
      // (khong rieng tu that su), day la gioi han thiet ke da co tu
      // truoc. De tranh hien nham vao cuoc chat khong lien quan, chi
      // hien khi nguoi gui la chinh minh hoac la nguoi dang mo chat cung.
      const [sender, content, , originalSender, originalSnippet] = event.detail;
      if (sender !== state.username && sender !== state.currentTarget) return;
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
      const belongsHere = isOwn ? state.currentTarget === target : state.currentTarget === sender;
      if (belongsHere) appendImageBubble({ sender, fileName, mimeType, dataBase64, isOwn });
    });

    window.addEventListener('chat:ONLINE', (event) => {
      const [csv] = event.detail;
      state.onlineUsers = csv ? csv.split(',').filter(Boolean) : [];
      renderFriendsList();
      if (state.currentTarget) {
        // Cap nhat lai cham trang thai tren header neu dang mo dung
        // nguoi vua doi trang thai online/offline.
        selectTarget(state.currentTarget);
      }
    });

    window.addEventListener('chat:ERROR', (event) => {
      appendSystemLine('Lỗi: ' + event.detail.join('|'));
    });

    window.addEventListener('chat:disconnected', () => {
      appendSystemLine('Mất kết nối tới server.');
    });

    // ---- Ket ban + Profile: cac thong diep tu server ----

    window.addEventListener('chat:USERINFO', (event) => {
      const [username, fullName, bio, status, friendStatus] = event.detail;
      renderProfile({ username, fullName, bio, status, friendStatus });
    });

    window.addEventListener('chat:FRIENDREQ_IN', (event) => {
      const [fromUsername] = event.detail;
      appendSystemLine(`${fromUsername} đã gửi cho bạn một lời mời kết bạn.`);
      setPendingRequestCount(state.pendingRequestCount + 1);
      if (elements.friendRequestsModal && elements.friendRequestsModal.style.display === 'flex') {
        loadFriendRequests();
      }
    });

    window.addEventListener('chat:FRIENDREQ_OK', (event) => {
      const [targetUsername] = event.detail;
      showFriendAddStatus(`Đã gửi lời mời kết bạn tới ${targetUsername}.`, true);
      if (elements.profileModal.style.display === 'flex'
          && elements.profileUsername.textContent === '@' + targetUsername) {
        openProfile(targetUsername);
      }
    });

    window.addEventListener('chat:FRIENDREQ_ERR', (event) => {
      const [errorMessage] = event.detail;
      showFriendAddStatus(errorMessage || 'Không gửi được lời mời kết bạn.', false);
    });

    window.addEventListener('chat:FRIENDRESP_IN', (event) => {
      const [otherUsername, action] = event.detail;
      if (action === 'ACCEPT') {
        appendSystemLine(`Bạn và ${otherUsername} đã trở thành bạn bè.`);
        api.get_friend_list();
      } else {
        appendSystemLine(`${otherUsername} đã từ chối lời mời kết bạn.`);
      }
      if (elements.profileModal.style.display === 'flex'
          && elements.profileUsername.textContent === '@' + otherUsername) {
        openProfile(otherUsername);
      }
    });

    window.addEventListener('chat:FRIENDRESP_OK', (event) => {
      const [otherUsername, action] = event.detail;
      if (action === 'ACCEPT') {
        appendSystemLine(`Bạn và ${otherUsername} đã trở thành bạn bè.`);
        api.get_friend_list();
      }
    });

    window.addEventListener('chat:FRIENDRESP_ERR', (event) => {
      const [errorMessage] = event.detail;
      appendSystemLine('Lỗi: ' + (errorMessage || 'Không xử lý được lời mời kết bạn.'));
    });

    window.addEventListener('chat:FRIENDREQUESTS', (event) => {
      const [csv] = event.detail;
      const usernames = csv ? csv.split(',').filter(Boolean) : [];
      setPendingRequestCount(usernames.length);
      renderFriendRequestsList(usernames);
    });

    window.addEventListener('chat:FRIENDLIST', (event) => {
      const [csv] = event.detail;
      state.friends = csv ? csv.split(',').filter(Boolean) : [];
      renderFriendsList();
      if (!state.currentTarget && state.friends.length > 0) {
        selectTarget(state.friends[0]);
      }
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

    // ---- Ket ban: gui loi moi tu o input nho trong sidebar ----
    function bindFriendAdd() {
      if (!elements.friendAddBtn || !elements.friendAddInput) return;
      const submit = () => {
        const target = elements.friendAddInput.value.trim();
        if (!target) return;
        api.add_friend(target).then((result) => {
          if (result && result.ok === false) {
            showFriendAddStatus(result.error || 'Không gửi được lời mời.', false);
          } else {
            elements.friendAddInput.value = '';
          }
        });
      };
      elements.friendAddBtn.addEventListener('click', submit);
      elements.friendAddInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          submit();
        }
      });
    }

    function showFriendAddStatus(text, ok) {
      if (!elements.friendAddStatus) return;
      elements.friendAddStatus.textContent = text;
      elements.friendAddStatus.className = 'friend-add-status ' + (ok ? 'ok' : 'err');
      setTimeout(() => {
        if (elements.friendAddStatus.textContent === text) {
          elements.friendAddStatus.textContent = '';
          elements.friendAddStatus.className = 'friend-add-status';
        }
      }, 4000);
    }

    // ---- Bang so luong loi moi ket ban dang cho ----
    function setPendingRequestCount(count) {
      state.pendingRequestCount = count;
      if (!elements.friendRequestsBadge) return;
      if (count > 0) {
        elements.friendRequestsBadge.textContent = String(count);
        elements.friendRequestsBadge.style.display = 'flex';
      } else {
        elements.friendRequestsBadge.style.display = 'none';
      }
    }

    // ---- Modal: danh sach loi moi ket ban ----
    function bindFriendRequestsPanel() {
      if (elements.friendRequestsBtn) {
        elements.friendRequestsBtn.addEventListener('click', () => {
          if (elements.friendRequestsModal) elements.friendRequestsModal.style.display = 'flex';
          loadFriendRequests();
        });
      }
      if (elements.friendRequestsClose) {
        elements.friendRequestsClose.addEventListener('click', () => {
          if (elements.friendRequestsModal) elements.friendRequestsModal.style.display = 'none';
        });
      }
    }

    function loadFriendRequests() {
      api.get_friend_requests();
    }

    function renderFriendRequestsList(usernames) {
      if (!elements.friendRequestsList) return;
      elements.friendRequestsList.innerHTML = '';

      if (usernames.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'empty-hint';
        empty.textContent = 'Không có lời mời nào.';
        elements.friendRequestsList.appendChild(empty);
        return;
      }

      usernames.forEach((username) => {
        const row = document.createElement('div');
        row.className = 'friend-req-item';
        row.innerHTML = `
          <span class="avatar status" style="width:38px;height:38px;font-size:12px">${username.slice(0, 2).toUpperCase()}</span>
          <span class="name">${escapeHtml(username)}</span>
          <div class="req-actions">
            <button class="accept-btn" data-user="${escapeHtml(username)}">Đồng ý</button>
            <button class="reject-btn" data-user="${escapeHtml(username)}">Từ chối</button>
          </div>`;
        row.querySelector('.accept-btn').addEventListener('click', () => {
          api.respond_friend_request(username, true);
          row.remove();
          setPendingRequestCount(Math.max(0, state.pendingRequestCount - 1));
        });
        row.querySelector('.reject-btn').addEventListener('click', () => {
          api.respond_friend_request(username, false);
          row.remove();
          setPendingRequestCount(Math.max(0, state.pendingRequestCount - 1));
        });
        elements.friendRequestsList.appendChild(row);
      });
    }

    // ---- Modal: xem thong tin ca nhan ----
    function bindProfileModal() {
      if (elements.profileModalClose) {
        elements.profileModalClose.addEventListener('click', () => {
          if (elements.profileModal) elements.profileModal.style.display = 'none';
        });
      }
    }

    function openProfile(username) {
      if (elements.profileModal) elements.profileModal.style.display = 'flex';
      if (elements.profileFullname) elements.profileFullname.textContent = 'Đang tải...';
      if (elements.profileBio) elements.profileBio.textContent = '';
      if (elements.profileActions) elements.profileActions.innerHTML = '';
      api.get_user_info(username);
    }

    const FRIEND_STATUS_LABEL = {
      online: 'Đang hoạt động',
      offline: 'Ngoại tuyến',
      away: 'Vắng mặt',
    };

    function renderProfile({ username, fullName, bio, status, friendStatus }) {
      if (elements.profileModal) elements.profileModal.style.display = 'flex';
      if (elements.profileAvatar) elements.profileAvatar.textContent = username.slice(0, 2).toUpperCase();
      if (elements.profileFullname) elements.profileFullname.textContent = fullName || username;
      if (elements.profileUsername) elements.profileUsername.textContent = '@' + username;
      if (elements.profileBio) {
        elements.profileBio.textContent = bio || 'Người dùng này chưa có tiểu sử.';
      }
      if (elements.profileStatus) {
        const isOnline = status === 'online';
        elements.profileStatus.className = 'profile-status' + (isOnline ? ' online' : '');
        elements.profileStatus.innerHTML =
          '<span class="dot"></span>' + (FRIEND_STATUS_LABEL[status] || 'Ngoại tuyến');
      }
      renderProfileActions(username, friendStatus);
    }

    function renderProfileActions(username, friendStatus) {
      if (!elements.profileActions) return;
      elements.profileActions.innerHTML = '';

      const makeBtn = (label, cls, onClick) => {
        const btn = document.createElement('button');
        btn.className = cls;
        btn.textContent = label;
        btn.addEventListener('click', onClick);
        return btn;
      };

      if (friendStatus === 'self') {
        return; // khong hien nut gi voi chinh minh
      }

      if (friendStatus === 'friends') {
        elements.profileActions.appendChild(
          makeBtn('Nhắn tin', 'btn-primary', () => {
            elements.profileModal.style.display = 'none';
            selectTarget(username);
          })
        );
        return;
      }

      if (friendStatus === 'pending_sent') {
        elements.profileActions.appendChild(makeBtn('Đã gửi lời mời', 'btn-ghost', () => {}));
        return;
      }

      if (friendStatus === 'pending_received') {
        elements.profileActions.appendChild(
          makeBtn('Đồng ý kết bạn', 'btn-primary', () => {
            api.respond_friend_request(username, true);
            elements.profileModal.style.display = 'none';
          })
        );
        elements.profileActions.appendChild(
          makeBtn('Từ chối', 'btn-ghost', () => {
            api.respond_friend_request(username, false);
            elements.profileModal.style.display = 'none';
          })
        );
        return;
      }

      // friendStatus === 'none'
      elements.profileActions.appendChild(
        makeBtn('Kết bạn', 'btn-primary', () => {
          api.add_friend(username);
        })
      );
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