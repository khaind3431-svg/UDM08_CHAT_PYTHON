// ==========================================================================
// WIRELINE — chat-avatar.js
//
// Module HOAN TOAN DOC LAP voi chat-network.js: khong doc, khong ghi,
// khong goi ham noi bo nao cua no ca. File nay chi lam DUY NHAT 1 viec:
// khi biet duoc avatar that cua 1 username (qua su kien chat:USERINFO),
// tu dong tim va thay o "2 chu cai dau ten" bang anh dai dien that,
// o ca 3 noi:
//   - Danh sach ban be (sidebar)
//   - Header cuoc tro chuyen dang mo
//   - Bong bong tin nhan (van ban va anh) cua nguoi gui
//
// Cach hoat dong: dung MutationObserver de "nhin" DOM thay doi, dua vao
// cac thuoc tinh/noi dung DA CO SAN TU TRUOC (khong can chat-network.js
// them bat ky "moc" nao rieng cho file nay):
//   - .contact-item co san thuoc tinh data-target="<username>"
//   - .chat-header .identity .name da hien san username dang mo chat
//   - .sender-name trong bong bong tin nhan da hien san username nguoi gui
//
// Nho vay, chat-network.js khong can sua mot dong nao de file nay hoat
// dong - hoan toan tach biet, de doc, de xoa neu khong can nua.
// ==========================================================================

(function () {
  const avatarCache = {};      // username -> data-URI avatar that ('' = da hoi nhung chua co)
  const fetchRequested = new Set();
  let api = null;

  window.ChatNetwork.whenApiReady((chatApi) => {
    api = chatApi;
  });

  // Hoi ngam avatar that cua 1 username qua GETINFO (co san trong
  // gui_client.py/profile_controller.py), chi hoi 1 lan cho 1 nguoi
  // trong 1 phien lam viec de tranh spam.
  function ensureFetched(username) {
    if (!username || !api) return;
    if (Object.prototype.hasOwnProperty.call(avatarCache, username)) return;
    if (fetchRequested.has(username)) return;
    fetchRequested.add(username);
    api.get_user_info(username);
  }

  function paintAvatar(el, avatarUrl) {
    if (!el || !avatarUrl) return;
    el.style.backgroundImage = `url(${avatarUrl})`;
    el.style.backgroundSize = 'cover';
    el.style.backgroundPosition = 'center';
    el.textContent = '';
  }

  function paintFriendsList() {
    document.querySelectorAll('#friends-list .contact-item[data-target]').forEach((item) => {
      const username = item.dataset.target;
      const avatarEl = item.querySelector('.avatar');
      if (!username || !avatarEl) return;
      if (avatarCache[username]) {
        paintAvatar(avatarEl, avatarCache[username]);
      } else {
        ensureFetched(username);
      }
    });
  }

  function paintChatHeader() {
    const nameEl = document.querySelector('.chat-header .identity .name');
    const avatarEl = document.querySelector('.chat-header > .avatar');
    if (!nameEl || !avatarEl) return;
    const username = nameEl.textContent.trim();
    if (!username || username === 'Chọn một người bạn để trò chuyện') return;
    if (avatarCache[username]) {
      paintAvatar(avatarEl, avatarCache[username]);
    } else {
      ensureFetched(username);
    }
  }

  function paintMessageRow(row) {
    if (!row.classList || !row.classList.contains('in')) return; // tin cua minh khong co avatar
    const senderEl = row.querySelector('.sender-name');
    const avatarEl = row.querySelector('.avatar');
    if (!senderEl || !avatarEl) return;
    const username = senderEl.textContent.trim();
    if (!username) return;
    if (avatarCache[username]) {
      paintAvatar(avatarEl, avatarCache[username]);
    } else {
      ensureFetched(username);
    }
  }

  function paintAllMessages() {
    document.querySelectorAll('#message-scroll .msg-row.in').forEach(paintMessageRow);
  }

  function observe() {
    const friendsList = document.getElementById('friends-list');
    const messageScroll = document.getElementById('message-scroll');
    const chatHeader = document.querySelector('.chat-header');

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType !== 1) return;

          if (friendsList && (node === friendsList || friendsList.contains(node))) {
            paintFriendsList();
          }
          if (messageScroll && (node === messageScroll || messageScroll.contains(node))) {
            if (node.classList && node.classList.contains('msg-row')) {
              paintMessageRow(node);
            } else {
              paintAllMessages();
            }
          }
        });
      });
      paintChatHeader();
    });

    if (friendsList) observer.observe(friendsList, { childList: true, subtree: true });
    if (messageScroll) observer.observe(messageScroll, { childList: true, subtree: true });
    if (chatHeader) observer.observe(chatHeader, { childList: true, subtree: true, characterData: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', observe);
  } else {
    observe();
  }

  window.addEventListener('chat:USERINFO', (event) => {
    const [username, , , , , , , avatarUrl] = event.detail;
    if (!username) return;
    avatarCache[username] = avatarUrl || '';
    if (avatarUrl) {
      paintFriendsList();
      paintChatHeader();
      paintAllMessages();
    }
  });
})();