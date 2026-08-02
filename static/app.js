const urlsEl = document.getElementById("urls");
const noPlaylistEl = document.getElementById("no-playlist");
const btnAdd = document.getElementById("btn-add");
const btnStart = document.getElementById("btn-start");
const btnCancel = document.getElementById("btn-cancel");
const btnOpenFolder = document.getElementById("btn-open-folder");
const queueList = document.getElementById("queue-list");
const progressText = document.getElementById("progress-text");
const downloadsPathEl = document.getElementById("downloads-path");
const successMessage = document.getElementById("success-message");
const installWarning = document.getElementById("install-warning");
const ytdlpDirEl = document.getElementById("ytdlp-dir");
const btnBrowse = document.getElementById("btn-browse");
const btnSavePath = document.getElementById("btn-save-path");
const pathStatus = document.getElementById("path-status");

let pollTimer = null;
let hasQueue = false;
let pathConfigured = false;

function statusLabel(status) {
  const map = {
    pendente: "Pendente",
    baixando: "Baixando",
    concluido: "Concluído",
    erro: "Erro",
    cancelado: "Cancelado",
  };
  return map[status] || status;
}

function renderQueue(queue) {
  queueList.innerHTML = "";
  queue.forEach((item) => {
    const li = document.createElement("li");

    const titleWrap = document.createElement("div");
    titleWrap.className = "item-title";
    titleWrap.textContent = item.title || item.url;
    if (item.error) {
      const errSpan = document.createElement("span");
      errSpan.className = "item-error";
      errSpan.textContent = item.error;
      titleWrap.appendChild(document.createElement("br"));
      titleWrap.appendChild(errSpan);
    }

    const badge = document.createElement("span");
    badge.className = `status-badge status-${item.status}`;
    badge.textContent = statusLabel(item.status);

    li.appendChild(titleWrap);
    li.appendChild(badge);
    queueList.appendChild(li);
  });
}

async function checkInstallation() {
  const res = await fetch("/api/check");
  const data = await res.json();
  if (!data.ok) {
    if (data.path) {
      installWarning.textContent =
        `Atenção: arquivos não encontrados em "${data.path}": ${data.missing.join(", ")}. Verifique a instalação do yt-dlp/ffmpeg.`;
    } else {
      installWarning.textContent =
        "Configure abaixo a pasta onde estão yt-dlp.exe e ffmpeg.exe antes de usar.";
    }
    installWarning.classList.remove("hidden");
    pathConfigured = false;
  } else {
    installWarning.classList.add("hidden");
    pathConfigured = true;
  }
  updateAddButtonState();
}

function updateAddButtonState() {
  btnAdd.disabled = !pathConfigured;
}

async function loadSettings() {
  const res = await fetch("/api/settings");
  const data = await res.json();
  ytdlpDirEl.value = data.ytdlp_dir || "";
}

async function browseFolder() {
  btnBrowse.disabled = true;
  try {
    const res = await fetch("/api/browse-folder", { method: "POST" });
    const data = await res.json();
    if (data.path) {
      ytdlpDirEl.value = data.path;
    }
  } finally {
    btnBrowse.disabled = false;
  }
}

async function savePath() {
  const path = ytdlpDirEl.value.trim();
  if (!path) {
    alert("Informe ou selecione uma pasta.");
    return;
  }

  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ytdlp_dir: path }),
  });
  const data = await res.json();

  if (!res.ok) {
    pathStatus.textContent = data.error || "Erro ao salvar caminho.";
    pathStatus.className = "path-status error";
    return;
  }

  if (data.ok) {
    pathStatus.textContent = "Caminho salvo e válido. yt-dlp e ffmpeg encontrados.";
    pathStatus.className = "path-status ok";
  } else {
    pathStatus.textContent = `Caminho salvo, mas faltam arquivos: ${data.missing.join(", ")}.`;
    pathStatus.className = "path-status error";
  }

  await checkInstallation();
  await pollStatus();
}

async function addQueue() {
  const lines = urlsEl.value
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .slice(0, 10);

  if (lines.length === 0) {
    alert("Cole ao menos um link do YouTube.");
    return;
  }

  const res = await fetch("/api/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ urls: lines }),
  });
  const data = await res.json();

  if (!res.ok) {
    alert(data.error || "Erro ao adicionar à fila.");
    return;
  }

  hasQueue = true;
  renderQueue(data.queue);
  updateProgress(data.queue);
  btnStart.disabled = false;
  successMessage.classList.add("hidden");
}

function updateProgress(queue) {
  const concluidos = queue.filter((i) => i.status === "concluido").length;
  progressText.textContent = `${concluidos} de ${queue.length} concluídos`;
}

async function startDownloads() {
  const res = await fetch("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ no_playlist: noPlaylistEl.checked }),
  });
  const data = await res.json();

  if (!res.ok) {
    alert(data.error || "Erro ao iniciar downloads.");
    return;
  }

  btnStart.disabled = true;
  btnAdd.disabled = true;
  btnCancel.classList.remove("hidden");
  successMessage.classList.add("hidden");
  startPolling();
}

async function cancelDownloads() {
  await fetch("/api/cancel", { method: "POST" });
}

async function openFolder() {
  const res = await fetch("/api/open-folder", { method: "POST" });
  const data = await res.json();
  if (!res.ok) {
    alert(data.error || "Não foi possível abrir a pasta.");
  }
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(pollStatus, 2000);
  pollStatus();
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function pollStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();

  renderQueue(data.queue);
  updateProgress(data.queue);
  downloadsPathEl.textContent = data.downloads_dir;

  if (!data.running) {
    stopPolling();
    btnAdd.disabled = false;
    btnCancel.classList.add("hidden");

    const total = data.queue.length;
    const finished = data.queue.every((i) =>
      ["concluido", "erro", "cancelado"].includes(i.status)
    );
    if (total > 0 && finished && data.concluidos === total) {
      successMessage.classList.remove("hidden");
      btnOpenFolder.classList.add("highlight");
    }
  }
}

btnAdd.addEventListener("click", addQueue);
btnStart.addEventListener("click", startDownloads);
btnCancel.addEventListener("click", cancelDownloads);
btnOpenFolder.addEventListener("click", openFolder);
btnBrowse.addEventListener("click", browseFolder);
btnSavePath.addEventListener("click", savePath);

loadSettings();
checkInstallation();
pollStatus();
