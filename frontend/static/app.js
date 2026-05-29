/* Billie Jean Law — Vera Chat Widget + Voice */
(function () {
  const SESSION_ID = 'bjl_' + Math.random().toString(36).slice(2, 10);
  let isOpen = false;
  let greeted = false;

  /* ── TTS ─────────────────────────────────────────────────────────────── */
  let voiceMuted = false;
  let preferredVoice = null;

  function loadVoice() {
    const voices = speechSynthesis.getVoices();
    preferredVoice =
      voices.find(v => v.name === 'Google US English') ||
      voices.find(v => v.name.includes('Samantha')) ||
      voices.find(v => v.lang === 'en-US' && !v.localService) ||
      voices.find(v => v.lang === 'en-US') ||
      null;
  }
  loadVoice();
  if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = loadVoice;
  }

  function speak(text) {
    if (voiceMuted) return;
    speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.rate = 1.0;
    utt.pitch = 1.0;
    utt.volume = 1.0;
    if (preferredVoice) utt.voice = preferredVoice;
    const avatar = document.getElementById('chat-avatar');
    utt.onstart = () => avatar && avatar.classList.add('speaking');
    utt.onend   = () => avatar && avatar.classList.remove('speaking');
    utt.onerror = () => avatar && avatar.classList.remove('speaking');
    speechSynthesis.speak(utt);
  }

  window.toggleMute = function () {
    voiceMuted = !voiceMuted;
    speechSynthesis.cancel();
    const btn = document.getElementById('mute-btn');
    if (btn) btn.textContent = voiceMuted ? '🔇' : '🔊';
    const avatar = document.getElementById('chat-avatar');
    if (avatar) avatar.classList.remove('speaking');
  };

  /* ── STT ─────────────────────────────────────────────────────────────── */
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let isListening = false;

  if (SpeechRecognition) {
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) micBtn.style.display = 'flex';

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      isListening = true;
      const btn = document.getElementById('mic-btn');
      if (btn) btn.classList.add('listening');
      const input = document.getElementById('chat-input');
      if (input) { input.placeholder = 'Listening...'; input.value = ''; }
      speechSynthesis.cancel();
    };

    recognition.onresult = (e) => {
      const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
      const input = document.getElementById('chat-input');
      if (input) input.value = transcript;
      if (e.results[e.results.length - 1].isFinal && transcript.trim()) {
        recognition.stop();
        setTimeout(() => window.sendMessage(), 100);
      }
    };

    recognition.onend = () => {
      isListening = false;
      const btn = document.getElementById('mic-btn');
      if (btn) btn.classList.remove('listening');
      const input = document.getElementById('chat-input');
      if (input) input.placeholder = 'Describe your situation...';
    };

    recognition.onerror = (e) => {
      isListening = false;
      const btn = document.getElementById('mic-btn');
      if (btn) btn.classList.remove('listening');
      const input = document.getElementById('chat-input');
      if (input) input.placeholder = 'Describe your situation...';
      if (e.error === 'not-allowed') {
        addBotMessage('Microphone access was denied. You can still type your question below.');
      }
    };
  }

  window.toggleMic = function () {
    if (!recognition) return;
    if (isListening) { recognition.stop(); } else { recognition.start(); }
  };

  /* ── CHAT ────────────────────────────────────────────────────────────── */
  window.toggleChat = function () {
    const win = document.getElementById('chat-window');
    isOpen = !isOpen;
    win.classList.toggle('open', isOpen);
    if (isOpen && !greeted) {
      greeted = true;
      setTimeout(() => {
        const greeting =
          "Hi, I'm Vera — intake specialist at Billie Jean Law. " +
          "Tell me what's going on and I'll help you understand your options and connect you with the right attorney. " +
          "Everything you share here is confidential.";
        addBotMessage(greeting);
        speak(greeting);
      }, 400);
    }
    if (isOpen) {
      document.getElementById('chat-input').focus();
    } else {
      speechSynthesis.cancel();
    }
  };

  window.openChat = function () {
    if (!isOpen) window.toggleChat();
  };

  window.sendMessage = async function () {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    addUserMessage(text);
    input.value = '';
    input.style.height = 'auto';

    const typingId = addTyping();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: SESSION_ID }),
      });
      const data = await res.json();
      removeTyping(typingId);
      addBotMessage(data.response);
      speak(data.response);
    } catch {
      removeTyping(typingId);
      const err = "I'm having trouble connecting. Please call us directly at (540) 555-2400 and we'll help you right away.";
      addBotMessage(err);
      speak(err);
    }
  };

  function addUserMessage(text) {
    const msgs = document.getElementById('chat-messages');
    const el = document.createElement('div');
    el.className = 'msg user';
    el.textContent = text;
    msgs.appendChild(el);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function addBotMessage(text) {
    const msgs = document.getElementById('chat-messages');
    const el = document.createElement('div');
    el.className = 'msg bot';
    el.textContent = text;
    msgs.appendChild(el);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function addTyping() {
    const msgs = document.getElementById('chat-messages');
    const id = 'typing_' + Date.now();
    const el = document.createElement('div');
    el.className = 'msg typing';
    el.id = id;
    el.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    msgs.appendChild(el);
    msgs.scrollTop = msgs.scrollHeight;
    return id;
  }

  function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  document.getElementById('chat-input').addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 100) + 'px';
  });

  document.getElementById('chat-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      window.sendMessage();
    }
  });
})();
