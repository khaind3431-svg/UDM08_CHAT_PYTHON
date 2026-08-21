(function () {
  function whenApiReady(callback) {
    if (window.pywebview && window.pywebview.api) {
      callback(window.pywebview.api);
    } else {
      window.addEventListener('pywebviewready', () => callback(window.pywebview.api));
    }
  }

  function parseLine(line) {
    const parts = line.split('|');
    return { type: parts[0], parts: parts.slice(1) };
  }

  window.onServerMessage = function (line) {
    if (line === '__DISCONNECTED__') {
      window.dispatchEvent(new CustomEvent('chat:disconnected'));
      return;
    }
    const { type, parts } = parseLine(line);
    window.dispatchEvent(new CustomEvent('chat:' + type, { detail: parts }));
  };

  window.ChatNetwork = { whenApiReady, parseLine };
})();