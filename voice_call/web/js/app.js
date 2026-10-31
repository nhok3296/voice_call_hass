document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("themeToggle");
  const speakerSelect = document.getElementById("speakerSelect");
  const refreshSpeakers = document.getElementById("refreshSpeakers");
  const volumeSlider = document.getElementById("volumeSlider");
  const volumeDisplay = document.getElementById("volumeDisplay");
  const micButton = document.getElementById("micButton");
  const micHint = document.getElementById("micHint");
  const micTimer = document.getElementById("micTimer");
  const cancelBtn = document.getElementById("cancelBtn");
  const stopBtn = document.getElementById("stopBtn");
  const statusBox = document.getElementById("statusBox");

  let isRecording = false;
  let isPressed = false;
  let isSending = false;
  let mediaRecorder = null;
  let audioStream = null;
  let audioChunks = [];
  let startTime = 0;
  let timerInterval = null;

  // 1. Theme Management
  const savedTheme = localStorage.getItem("vc_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  themeToggle.textContent = savedTheme === "dark" ? "☀️" : "🌙";

  themeToggle.addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") || "dark";
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("vc_theme", next);
    themeToggle.textContent = next === "dark" ? "☀️" : "🌙";
  });

  // 2. Status Helper
  function setStatus(msg, type = "normal") {
    statusBox.textContent = msg;
    statusBox.className = "status-box " + type;
  }

  // 3. Volume Control
  const savedVol = localStorage.getItem("vc_volume") || "65";
  volumeSlider.value = savedVol;
  volumeDisplay.textContent = savedVol + "%";
  volumeSlider.addEventListener("input", () => {
    volumeDisplay.textContent = volumeSlider.value + "%";
    localStorage.setItem("vc_volume", volumeSlider.value);
  });

  // 4. Populate Speakers to Select Dropdown
  function renderSpeakers(speakers) {
    if (!speakers || speakers.length === 0) return false;

    const currentVal = speakerSelect.value || localStorage.getItem("vc_speaker");
    speakerSelect.innerHTML = "";

    speakers.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.entity_id;
      const st = s.is_available ? (s.state === "off" ? "Sẵn sàng" : s.state) : "Ngoại tuyến";
      opt.textContent = `${s.friendly_name} (${st})`;
      if (!s.is_available) opt.style.color = "#94a3b8";
      speakerSelect.appendChild(opt);
    });

    if (currentVal && Array.from(speakerSelect.options).some((o) => o.value === currentVal)) {
      speakerSelect.value = currentVal;
    }

    speakerSelect.disabled = false;
    return true;
  }

  // Nạp ngay từ cache offline nếu có (đảm bảo bấm được chọn loa ngay lập tức)
  try {
    const cached = JSON.parse(localStorage.getItem("vc_cached_speakers") || "[]");
    if (cached.length > 0) {
      renderSpeakers(cached);
    }
  } catch (_) {}

  // 5. Load Speakers từ API
  async function loadSpeakers(silent = false) {
    try {
      if (!silent) setStatus("Đang kiểm tra danh sách loa...", "loading");

      const targetUrl = new URL("api/speakers", document.baseURI).href;
      const r = await fetch(targetUrl, { credentials: "same-origin" });
      const contentType = r.headers.get("content-type") || "";

      if (!contentType.includes("application/json")) {
        const text = await r.text();
        throw new Error(`Server trả về HTTP ${r.status}: ${text.slice(0, 80)}`);
      }

      const data = await r.json();

      if (data.speakers && data.speakers.length > 0) {
        renderSpeakers(data.speakers);
        localStorage.setItem("vc_cached_speakers", JSON.stringify(data.speakers));
        if (!isRecording && !isSending) {
          setStatus("Sẵn sàng. Chọn loa và nhấn giữ micro để gọi.", "success");
        }
      } else {
        if (!speakerSelect.options.length) {
          speakerSelect.innerHTML = "<option value=''>Không tìm thấy loa nào</option>";
          setStatus("Không tìm thấy loa trên Home Assistant.", "error");
        }
      }
    } catch (e) {
      if (!speakerSelect.options.length) {
        setStatus(`Lỗi kết nối loa: ${e.message}`, "error");
      }
    } finally {
      // ĐẢM BẢO LUÔN MỞ KHÓA SELECT CHO NGƯỜI DÙNG BẤM
      speakerSelect.disabled = false;
    }
  }

  speakerSelect.addEventListener("change", () => {
    localStorage.setItem("vc_speaker", speakerSelect.value);
  });

  // Tự động reload khi người dùng chạm vào select nếu đang rỗng
  speakerSelect.addEventListener("focus", () => {
    if (!speakerSelect.options.length || speakerSelect.options[0]?.value === "") {
      loadSpeakers(true);
    }
  });

  refreshSpeakers.addEventListener("click", () => loadSpeakers(false));

  // Tự động làm mới khi quay lại app từ màn hình khác (resume)
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      loadSpeakers(true);
    }
  });
  window.addEventListener("pageshow", () => loadSpeakers(true));

  // 6. Recorder Helper
  function getSupportedMime() {
    const list = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/webm", "audio/mp4"];
    return list.find((m) => window.MediaRecorder && MediaRecorder.isTypeSupported(m)) || "";
  }

  async function getAudioStream() {
    // 1. Gọi trực tiếp nếu có
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        return await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        });
      } catch (err) {
        throw new Error(`Micro bị từ chối: ${err.message || err.name}`);
      }
    }

    // 2. Fallback cho WebView
    const legacy = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
    if (legacy) {
      return new Promise((res, rej) => {
        legacy.call(navigator, { audio: true }, res, (err) =>
          rej(new Error(`Micro bị từ chối: ${err.message || err.name}`))
        );
      });
    }

    if (!window.isSecureContext) {
      throw new Error("Trình duyệt chặn Micro trên HTTP local. Hãy dùng App Home Assistant hoặc mở HTTPS!");
    }

    throw new Error("Trình duyệt không hỗ trợ Web Audio API hoặc Micro bị chặn.");
  }

  async function startRecord() {
    if (isRecording || isSending) return;
    isPressed = true;

    try {
      const mime = getSupportedMime();
      audioStream = await getAudioStream();

      if (!isPressed) {
        stopTracks();
        return;
      }

      audioChunks = [];
      mediaRecorder = new MediaRecorder(audioStream, { mimeType: mime });
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size) audioChunks.push(e.data);
      };
      mediaRecorder.onstop = sendRecord;

      mediaRecorder.start(250);
      isRecording = true;
      startTime = Date.now();

      micButton.classList.add("recording");
      micHint.textContent = "ĐANG THU ÂM — THẢ ĐỂ PHÁT";
      micHint.style.color = "var(--danger-color)";
      cancelBtn.disabled = false;
      setStatus("Đang ghi âm giọng nói...", "loading");

      timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        micTimer.textContent = `${elapsed}s / 120s`;
        if (elapsed >= 120) stopRecord(false);
      }, 250);
    } catch (e) {
      stopTracks();
      setStatus(`Không mở được micro: ${e.message}`, "error");
    }
  }

  function stopTracks() {
    if (audioStream) {
      audioStream.getTracks().forEach((t) => t.stop());
      audioStream = null;
    }
    mediaRecorder = null;
  }

  function stopRecord(cancel = false) {
    isPressed = false;
    if (!isRecording) return;
    isRecording = false;

    clearInterval(timerInterval);
    micButton.classList.remove("recording");
    cancelBtn.disabled = true;
    micHint.style.color = "var(--text-primary)";

    if (cancel) {
      audioChunks = [];
      stopTracks();
      micHint.textContent = "Đã hủy cuộc gọi";
      micTimer.textContent = "";
      setStatus("Đã hủy bản ghi âm.", "normal");
      setTimeout(() => (micHint.textContent = "Nhấn giữ để nói"), 1500);
    } else {
      micHint.textContent = "ĐANG PHÁT RA LOA...";
      setStatus("Đang xử lý và phát qua loa...", "loading");
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
      }
    }
  }

  async function sendRecord() {
    stopTracks();
    if (!audioChunks.length) {
      micHint.textContent = "Nhấn giữ để nói";
      micTimer.textContent = "";
      return;
    }

    isSending = true;
    const speaker = speakerSelect.value;
    const speakerName = speakerSelect.selectedOptions[0]?.text || speaker;
    const volume = Number(volumeSlider.value) / 100;
    const blob = new Blob(audioChunks, { type: "audio/webm" });

    const fd = new FormData();
    fd.append("speaker", speaker);
    fd.append("volume", String(volume));
    fd.append("audio", blob, "voice.webm");

    try {
      const targetUrl = new URL("api/talk", document.baseURI).href;
      const res = await fetch(targetUrl, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
      });
      const contentType = res.headers.get("content-type") || "";

      if (!contentType.includes("application/json")) {
        const text = await res.text();
        throw new Error(`Lỗi máy chủ (${res.status}): ${text.slice(0, 100)}`);
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Lỗi máy chủ");
      setStatus(`Đã phát thành công qua ${speakerName}!`, "success");
    } catch (e) {
      setStatus(`Lỗi phát loa: ${e.message}`, "error");
    } finally {
      isSending = false;
      audioChunks = [];
      micHint.textContent = "Nhấn giữ để nói";
      micTimer.textContent = "";
    }
  }

  // Pointer Events
  micButton.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    try {
      micButton.setPointerCapture(e.pointerId);
    } catch (_) {}
    startRecord();
  });
  micButton.addEventListener("pointerup", (e) => {
    e.preventDefault();
    stopRecord(false);
  });
  micButton.addEventListener("pointercancel", () => stopRecord(false));
  micButton.addEventListener("lostpointercapture", () => {
    if (isRecording) stopRecord(false);
  });

  cancelBtn.addEventListener("click", () => stopRecord(true));

  stopBtn.addEventListener("click", async () => {
    const spk = speakerSelect.value;
    if (!spk) return;
    try {
      stopBtn.disabled = true;
      const targetUrl = new URL(`api/speakers/${encodeURIComponent(spk)}/stop`, document.baseURI).href;
      await fetch(targetUrl, { method: "POST", credentials: "same-origin" });
      setStatus(`Đã dừng loa ${spk}.`, "success");
    } catch (e) {
      setStatus(`Không dừng được: ${e.message}`, "error");
    } finally {
      stopBtn.disabled = false;
    }
  });

  loadSpeakers(false);
});
