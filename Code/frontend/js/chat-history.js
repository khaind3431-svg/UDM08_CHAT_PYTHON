(function () {
  let api = null;
  let myUsername = null;

  window.ChatNetwork.whenApiReady(async (chatApi) => {
    api = chatApi;
    const session = await api.get_state();
    myUsername = session.username;
  });

  // Doc "ai la nguoi dang mo chat cung" truc tiep tu chinh giao dien
  // (chat-network.js da tu render san ten nguoi do vao day) - tranh
  // phai tu luu 1 bien state rieng co the bi lech voi ban chinh.
  function currentOpenTarget() {
    const nameEl = document.querySelector('.chat-header .identity .name');
    if (!nameEl) return null;
    const text = nameEl.textContent.trim();
    if (!text || text === 'Chọn một người bạn để trò chuyện') return null;
    return text;
  }

  // Bam vao 1 nguoi trong danh sach ban be (o sidebar) -> xin lai lich
  // su tin nhan cu cua cuoc tro chuyen do. Dùng event delegation nen
  // hoat dong dung voi ca nhung item duoc ve lai sau nay.
  document.addEventListener('click', (event) => {
    const item = event.target.closest('#friends-list .contact-item[data-target]');
    if (!item || !api) return;
    api.get_history(item.dataset.target);
  });

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : text;
    return div.innerHTML;
  }

  // created_at tu SQLite luu dang "YYYY-MM-DD HH:MM:SS" theo gio UTC
  // (mac dinh cua ham datetime('now')) - doi sang gio dia phuong nguoi
  // xem de hien dung nhu tin nhan gui truc tiep.
  function formatHistoryTime(createdAt) {
    if (!createdAt) return '';
    const isoLike = createdAt.replace(' ', 'T') + 'Z';
    const date = new Date(isoLike);
    if (Number.isNaN(date.getTime())) return '';
    return String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');
  }

  function appendHistoryBubble(sender, content, timeText) {
    const messageScroll = document.getElementById('message-scroll');
    if (!messageScroll) return;
    const isOwn = sender === myUsername;

    const row = document.createElement('div');
    row.className = 'msg-row ' + (isOwn ? 'out' : 'in');

    const avatarHtml = isOwn ? '' :
      `<span class="avatar" style="width:30px;height:30px;font-size:11px">${sender.slice(0, 2).toUpperCase()}</span>`;
    const senderNameHtml = isOwn ? '' : `<span class="sender-name">${escapeHtml(sender)}</span>`;

    row.innerHTML = `
      ${avatarHtml}
      <div class="msg-col">
        ${senderNameHtml}
        <div class="bubble-wrap">
          <div class="bubble">${escapeHtml(content)}</div>
        </div>
        <span class="msg-meta">${timeText}</span>
      </div>`;

    messageScroll.appendChild(row);
  }

  window.addEventListener('chat:HISTORY', (event) => {
    const [target, sender, content, , createdAt] = event.detail;
    // Chi ve neu day dung la cuoc tro chuyen dang mo NGAY LUC NAY -
    // tranh hien nham tin nhan cu cua 1 nguoi khac neu nguoi dung bam
    // chuyen qua lai nhanh giua nhieu ban be truoc khi phan hoi ve kip.
    if (currentOpenTarget() !== target) return;
    appendHistoryBubble(sender, content, formatHistoryTime(createdAt));
  });

  window.addEventListener('chat:HISTORY_END', (event) => {
    const [target] = event.detail;
    if (currentOpenTarget() !== target) return;
    const messageScroll = document.getElementById('message-scroll');
    if (messageScroll) messageScroll.scrollTop = messageScroll.scrollHeight;
  });
})();