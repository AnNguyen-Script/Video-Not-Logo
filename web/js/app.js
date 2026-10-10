/**
 * ═════════════════════════════════════════════════════════════════════════
 * VIDEO PRO MAX STUDIO v3.0.0 ULTRA — CORE JAVASCRIPT SYSTEM
 * Interactive Canvas • Atria Dawn AI Studio • Re-Up Engine • Media Cinema
 * ═════════════════════════════════════════════════════════════════════════
 */

// ─────────────────────────────────────────────────────────── 1. GLOBAL STATE & CONFIG
const AppState = {
    version: "3.0.0",
    ws: null,
    wsConnected: false,
    activeTab: "tab-download",
    currentAnalysis: null,
    selectedMode: "video", // "video" | "audio"
    selectedQuality: "best",
    selectedBitrate: "192",
    tasks: {},
    vaultFiles: [],
    settings: {},
    bgStyle: localStorage.getItem("vpm_bg_style") || "aurora",
    audioCtx: null,
    audioAnalyser: null,
    currentAIOutput: "",
    reupStart: 0,
    reupEnd: null,
};

// ─────────────────────────────────────────────────────────── 2. DOM LOAD & INITIALIZATION
document.addEventListener("DOMContentLoaded", () => {
    initBackgroundEngine();
    initCollapsibleSections();
    initDownloaderModule();
    initMediaVaultModule();
    initCinemaPlayer();
    connectWebSocket();
    loadInitialData();
});

// ─────────────────────────────────────────────────────────── 3. CLEAN UTILITY BACKGROUND INIT
function initBackgroundEngine() {
    // Utility Dark Theme is clean and solid - no particle overhead needed
    AppState.bgStyle = "minimal";
    document.documentElement.setAttribute("data-bg-style", "minimal");
}

function setBgStyle(style) {
    AppState.bgStyle = style || "minimal";
    document.documentElement.setAttribute("data-bg-style", "minimal");
}

// ─────────────────────────────────────────────────────────── 4. NAVIGATION TABS
function initNavigation() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const targetId = tab.dataset.tab;
            switchTab(targetId);
        });
    });

    // Header Share Quick Button
    const btnHeaderShare = document.getElementById("btn-header-share");
    if (btnHeaderShare) {
        btnHeaderShare.addEventListener("click", () => switchTab("tab-share"));
    }
}

// ─────────────────────────────────────────────────────────── 4B. COLLAPSIBLE SECTIONS CONTROLLER
function initCollapsibleSections() {
    // 1. Tasks section toggle
    const btnToggleTasks = document.getElementById("btn-toggle-tasks");
    const tasksBody = document.getElementById("tasks-collapsible-body");
    const savedTasksCollapse = localStorage.getItem("vpm_collapse_tasks");

    if (btnToggleTasks && tasksBody) {
        if (savedTasksCollapse === "1") {
            tasksBody.classList.add("collapsed");
            btnToggleTasks.classList.add("collapsed");
        }
        btnToggleTasks.addEventListener("click", () => {
            const isNowCollapsed = tasksBody.classList.toggle("collapsed");
            btnToggleTasks.classList.toggle("collapsed", isNowCollapsed);
            localStorage.setItem("vpm_collapse_tasks", isNowCollapsed ? "1" : "0");
        });
    }

    // 2. Vault section toggle
    const btnToggleVault = document.getElementById("btn-toggle-vault");
    const vaultBody = document.getElementById("vault-collapsible-body");
    const savedVaultCollapse = localStorage.getItem("vpm_collapse_vault");

    if (btnToggleVault && vaultBody) {
        if (savedVaultCollapse === "1") {
            vaultBody.classList.add("collapsed");
            btnToggleVault.classList.add("collapsed");
        }
        btnToggleVault.addEventListener("click", () => {
            const isNowCollapsed = vaultBody.classList.toggle("collapsed");
            btnToggleVault.classList.toggle("collapsed", isNowCollapsed);
            localStorage.setItem("vpm_collapse_vault", isNowCollapsed ? "1" : "0");
        });
    }

    // 3. Platform chips toggle
    const btnToggleChips = document.getElementById("btn-toggle-chips");
    const chipsWrap = document.getElementById("platform-chips-wrap");
    const savedChipsCollapse = localStorage.getItem("vpm_collapse_chips");

    if (btnToggleChips && chipsWrap) {
        if (savedChipsCollapse === "1") {
            chipsWrap.classList.add("collapsed");
            btnToggleChips.classList.add("collapsed");
        }
        btnToggleChips.addEventListener("click", () => {
            const isNowCollapsed = chipsWrap.classList.toggle("collapsed");
            btnToggleChips.classList.toggle("collapsed", isNowCollapsed);
            localStorage.setItem("vpm_collapse_chips", isNowCollapsed ? "1" : "0");
        });
    }
}

function expandTasksSection() {
    const btnToggleTasks = document.getElementById("btn-toggle-tasks");
    const tasksBody = document.getElementById("tasks-collapsible-body");
    if (tasksBody && tasksBody.classList.contains("collapsed")) {
        tasksBody.classList.remove("collapsed");
        if (btnToggleTasks) btnToggleTasks.classList.remove("collapsed");
        localStorage.setItem("vpm_collapse_tasks", "0");
    }
}

function expandVaultSection() {
    const btnToggleVault = document.getElementById("btn-toggle-vault");
    const vaultBody = document.getElementById("vault-collapsible-body");
    if (vaultBody && vaultBody.classList.contains("collapsed")) {
        vaultBody.classList.remove("collapsed");
        if (btnToggleVault) btnToggleVault.classList.remove("collapsed");
        localStorage.setItem("vpm_collapse_vault", "0");
    }
}

function switchTab(tabId) {
    if (tabId === "tab-tasks" || tabId === "tasks-section") {
        expandTasksSection();
        renderTasks();
        const el = document.getElementById("tasks-section");
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (tabId === "tab-vault" || tabId === "vault-section") {
        expandVaultSection();
        loadVaultFiles();
        const el = document.getElementById("vault-section");
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (tabId === "tab-download") {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
}

// ─────────────────────────────────────────────────────────── 5. DOWNLOADER MODULE & CYBER RADAR
function initDownloaderModule() {
    const btnAnalyze = document.getElementById("btn-analyze");
    const btnPaste = document.getElementById("btn-paste");
    const urlInput = document.getElementById("url-input");
    const btnToggleBatch = document.getElementById("btn-toggle-batch");
    const batchDrawer = document.getElementById("batch-drawer");
    const btnBatchPaste = document.getElementById("btn-batch-clipboard");
    const btnBatchStart = document.getElementById("btn-batch-start");
    const btnExecuteDownload = document.getElementById("btn-execute-download");

    // Paste Action
    if (btnPaste) {
        btnPaste.addEventListener("click", async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text && text.startsWith("http")) {
                    urlInput.value = text.trim();
                    showToast("Đã dán liên kết từ bộ nhớ tạm!", "info");
                    triggerAnalysis(text.trim());
                } else {
                    showToast("Bộ nhớ tạm không chứa link hợp lệ!", "error");
                }
            } catch {
                showToast("Vui lòng cấp quyền truy cập Clipboard!", "error");
            }
        });
    }

    // Enter to analyze
    if (urlInput) {
        urlInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const val = urlInput.value.trim();
                if (val) triggerAnalysis(val);
            }
        });
    }

    // Click Analyze
    if (btnAnalyze) {
        btnAnalyze.addEventListener("click", () => {
            const val = urlInput.value.trim();
            if (!val) {
                showToast("Vui lòng nhập hoặc dán đường link video!", "error");
                return;
            }
            triggerAnalysis(val);
        });
    }

    // Platform chips click
    document.querySelectorAll(".p-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            const p = chip.dataset.platform;
            if (p === "more") {
                showToast("Hỗ trợ tải hơn 1000+ nền tảng (YouTube, TikTok, FB, Insta, Douyin, X...)", "info");
            } else {
                urlInput.placeholder = `Dán đường link ${chip.textContent.trim()} vào đây...`;
                urlInput.focus();
            }
        });
    });

    // Batch toggle
    if (btnToggleBatch && batchDrawer) {
        btnToggleBatch.addEventListener("click", () => {
            const isHidden = batchDrawer.style.display === "none";
            batchDrawer.style.display = isHidden ? "block" : "none";
            btnToggleBatch.classList.toggle("active", isHidden);
        });
    }

    // Batch Paste
    if (btnBatchPaste) {
        btnBatchPaste.addEventListener("click", async () => {
            try {
                const text = await navigator.clipboard.readText();
                const textarea = document.getElementById("batch-urls");
                if (textarea && text) {
                    textarea.value = (textarea.value + "\n" + text).trim();
                    showToast("Đã dán link vào danh sách hàng loạt!", "info");
                }
            } catch {
                showToast("Không thể đọc bộ nhớ tạm!", "error");
            }
        });
    }

    // Batch Start
    if (btnBatchStart) {
        btnBatchStart.addEventListener("click", () => {
            const textarea = document.getElementById("batch-urls");
            const urls = (textarea.value || "")
                .split("\n")
                .map((u) => u.trim())
                .filter((u) => u.startsWith("http"));

            if (!urls.length) {
                showToast("Vui lòng dán ít nhất 1 đường link hợp lệ!", "error");
                return;
            }

            const quality = document.getElementById("batch-quality").value;
            const audioOnly = document.getElementById("batch-audio-only").checked;

            fetch("/api/download/batch", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    urls,
                    quality,
                    audio_only: audioOnly,
                    audio_bitrate: "192",
                }),
            })
                .then((r) => r.json())
                .then((res) => {
                    if (res.ok) {
                        showToast(`Đã thêm ${res.count} video vào hàng đợi tải xuống!`, "success");
                        textarea.value = "";
                        batchDrawer.style.display = "none";
                        switchTab("tab-tasks");
                    }
                })
                .catch(() => showToast("Lỗi khởi chạy tải hàng loạt!", "error"));
        });
    }

    // Format Mode Switch (Video vs Audio)
    const btnModeVideo = document.getElementById("btn-mode-video");
    const btnModeAudio = document.getElementById("btn-mode-audio");
    const panelVideo = document.getElementById("panel-video-quality");
    const panelAudio = document.getElementById("panel-audio-quality");

    if (btnModeVideo && btnModeAudio) {
        btnModeVideo.addEventListener("click", () => {
            AppState.selectedMode = "video";
            btnModeVideo.classList.add("active");
            btnModeAudio.classList.remove("active");
            panelVideo.style.display = "block";
            panelAudio.style.display = "none";
            document.getElementById("btn-download-text").textContent = "Tải Video MP4 Chuẩn";
        });

        btnModeAudio.addEventListener("click", () => {
            AppState.selectedMode = "audio";
            btnModeAudio.classList.add("active");
            btnModeVideo.classList.remove("active");
            panelVideo.style.display = "none";
            panelAudio.style.display = "block";
            document.getElementById("btn-download-text").textContent = "Tải Âm Thanh MP3 Lossless";
        });
    }

    // Bitrate chips click
    document.querySelectorAll(".audio-bitrate-panel .q-chip-btn").forEach((chip) => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".audio-bitrate-panel .q-chip-btn").forEach((c) => c.classList.remove("active"));
            chip.classList.add("active");
            AppState.selectedBitrate = chip.dataset.bitrate;
        });
    });

    // Execute Download Button
    if (btnExecuteDownload) {
        btnExecuteDownload.addEventListener("click", () => {
            if (!AppState.currentAnalysis || !AppState.currentAnalysis.url) {
                showToast("Vui lòng phân tích link trước khi tải!", "error");
                return;
            }

            const isAudio = AppState.selectedMode === "audio";
            const cutStart = parseFloat(document.getElementById("opt-cut-start").value) || null;
            const cutEnd = parseFloat(document.getElementById("opt-cut-end").value) || null;
            const subs = document.getElementById("opt-subs").value || null;

            const payload = {
                url: AppState.currentAnalysis.url,
                quality: AppState.selectedQuality,
                audio_only: isAudio,
                audio_bitrate: AppState.selectedBitrate,
                cut_start: cutStart,
                cut_end: cutEnd,
                subs_lang: subs,
                is_playlist: AppState.currentAnalysis.is_playlist || false,
            };

            btnExecuteDownload.disabled = true;
            btnExecuteDownload.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang khởi tạo...`;

            fetch("/api/download", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
                .then((r) => r.json())
                .then((res) => {
                    btnExecuteDownload.disabled = false;
                    btnExecuteDownload.innerHTML = `<i class="fa-solid fa-cloud-arrow-down"></i> <span id="btn-download-text">Bắt đầu tải xuống ngay</span>`;
                    if (res.ok) {
                        showToast("Đã bắt đầu tiến trình tải xuống!", "success");
                        switchTab("tab-tasks");
                    } else {
                        showToast(res.error || "Không thể bắt đầu tải!", "error");
                    }
                })
                .catch(() => {
                    btnExecuteDownload.disabled = false;
                    btnExecuteDownload.innerHTML = `<i class="fa-solid fa-cloud-arrow-down"></i> Bắt đầu tải xuống ngay`;
                    showToast("Lỗi kết nối máy chủ API!", "error");
                });
        });
    }
}

// ─────────────────────────────────────────────────────────── 6. CYBER RADAR ANALYSIS RUNNER
function triggerAnalysis(url) {
    const radarLoader = document.getElementById("radar-loader");
    const previewCard = document.getElementById("preview-card");
    const radarUrlLabel = document.getElementById("radar-target-url");
    const radarStageTitle = document.getElementById("radar-current-stage-title");

    if (!radarLoader || !previewCard) return;

    previewCard.style.display = "none";
    radarLoader.style.display = "block";
    radarUrlLabel.textContent = url;

    // Reset Stages
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById(`stage-${i}`);
        if (step) {
            step.className = "stage-step";
            step.querySelector(".stage-indicator").innerHTML = "";
        }
    }

    // Phased Animation Sequence
    setStage(1, "Đang giải mã URL và kết nối cụm CDN...");

    setTimeout(() => setStage(2, "Đang vượt rào cản n-token và chống 403..."), 600);
    setTimeout(() => setStage(3, "Đang bóc tách luồng gốc không watermark..."), 1300);

    const browser = document.getElementById("opt-browser-cookie")?.value || null;

    fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, browser }),
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.ok) {
                setStage(4, "Đã tối ưu bảng định dạng sẵn sàng tải!");
                setTimeout(() => {
                    radarLoader.style.display = "none";
                    renderPreview(data);
                }, 400);
            } else {
                radarLoader.style.display = "none";
                showToast(data.error || "Không thể phân tích video này!", "error");
            }
        })
        .catch((err) => {
            radarLoader.style.display = "none";
            showToast("Lỗi kết nối máy chủ phân tích: " + err, "error");
        });
}

function setStage(stageNum, message) {
    const radarStageTitle = document.getElementById("radar-current-stage-title");
    if (radarStageTitle) radarStageTitle.textContent = message;

    for (let i = 1; i < stageNum; i++) {
        const prev = document.getElementById(`stage-${i}`);
        if (prev) {
            prev.className = "stage-step done";
            prev.querySelector(".stage-indicator").innerHTML = `<i class="fa-solid fa-check text-emerald"></i>`;
        }
    }

    const current = document.getElementById(`stage-${stageNum}`);
    if (current) {
        current.className = "stage-step active";
        current.querySelector(".stage-indicator").innerHTML = `<span class="spinner-inline"></span>`;
    }
}

function renderPreview(data) {
    AppState.currentAnalysis = data;
    const previewCard = document.getElementById("preview-card");
    if (!previewCard) return;

    document.getElementById("preview-thumb").src = data.thumbnail || "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600";
    document.getElementById("preview-duration").innerHTML = `<i class="fa-regular fa-clock"></i> ${data.duration_str || "00:00"}`;
    document.getElementById("preview-platform").textContent = data.platform || "Video";
    document.getElementById("preview-title").textContent = data.title || "Video không tiêu đề";
    document.getElementById("preview-uploader").textContent = data.uploader || "Ẩn danh";

    // Build Quality Chips
    const container = document.getElementById("quality-selector-container");
    container.innerHTML = "";

    const formats = data.formats || [];
    if (!formats.length) {
        formats.push(
            { id: "best", label: "Tự động cao nhất", badge: "4K / 1080p MP4", note: "Khuyên dùng" },
            { id: "1080", label: "1080p Full HD", badge: "MP4 Chuẩn", note: "Sắc nét" },
            { id: "720", label: "720p HD", badge: "MP4 Nhẹ", note: "Tiết kiệm" }
        );
    }

    formats.forEach((fmt, idx) => {
        const btn = document.createElement("button");
        btn.className = `q-chip-btn ${idx === 0 ? "active" : ""}`;
        btn.dataset.quality = fmt.id || fmt.quality || "best";
        btn.innerHTML = `
            <span class="q-name">${fmt.label || fmt.height + "p" || "Best"}</span>
            <span class="q-badge">${fmt.badge || fmt.filesize_str || "Chuẩn MP4"}</span>
        `;
        btn.addEventListener("click", () => {
            container.querySelectorAll(".q-chip-btn").forEach((c) => c.classList.remove("active"));
            btn.classList.add("active");
            AppState.selectedQuality = btn.dataset.quality;
        });
        container.appendChild(btn);
    });

    AppState.selectedQuality = formats[0].id || "best";
    previewCard.style.display = "block";
    previewCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ─────────────────────────────────────────────────────────── 7. GOOGLE & INTERNET IDEA DISCOVERY
function initIdeaDiscoveryModule() {
    const input = document.getElementById("idea-search-input");
    const btnSearch = document.getElementById("btn-idea-search");
    const suggestionsBox = document.getElementById("google-suggestions-box");
    const presetsContainer = document.getElementById("trending-presets-container");

    // Load trending presets
    fetch("/api/ideas/trending")
        .then((r) => r.json())
        .then((data) => {
            if (data.ok && presetsContainer) {
                presetsContainer.innerHTML = "";
                data.presets.forEach((p) => {
                    const card = document.createElement("div");
                    card.className = "preset-chip-card";
                    card.innerHTML = `
                        <div class="preset-icon"><i class="${p.icon}"></i></div>
                        <div class="preset-info">
                            <span class="preset-title">${p.title}</span>
                            <span class="preset-sub">${p.subtitle}</span>
                        </div>
                    `;
                    card.addEventListener("click", () => {
                        input.value = p.query;
                        searchIdeas(p.query);
                        loadCreativePrompts(p.title);
                    });
                    presetsContainer.appendChild(card);
                });
            }
        });

    // Debounced Google Autocomplete
    let debounceTimer = null;
    if (input) {
        input.addEventListener("input", () => {
            clearTimeout(debounceTimer);
            const q = input.value.trim();
            if (q.length < 2) {
                suggestionsBox.style.display = "none";
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/api/ideas/suggestions?q=${encodeURIComponent(q)}`)
                    .then((r) => r.json())
                    .then((data) => {
                        if (data.ok && data.suggestions && data.suggestions.length) {
                            suggestionsBox.innerHTML = "";
                            data.suggestions.forEach((s) => {
                                const item = document.createElement("div");
                                item.className = "suggestion-item";
                                item.innerHTML = `<i class="fa-solid fa-magnifying-glass text-cyan"></i> <span>${s}</span>`;
                                item.addEventListener("click", () => {
                                    input.value = s;
                                    suggestionsBox.style.display = "none";
                                    searchIdeas(s);
                                });
                                suggestionsBox.appendChild(item);
                            });
                            suggestionsBox.style.display = "block";
                        } else {
                            suggestionsBox.style.display = "none";
                        }
                    });
            }, 250);
        });

        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                suggestionsBox.style.display = "none";
                const q = input.value.trim();
                if (q) searchIdeas(q);
            }
        });
    }

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".ideas-search-input-wrap") && suggestionsBox) {
            suggestionsBox.style.display = "none";
        }
    });

    if (btnSearch) {
        btnSearch.addEventListener("click", () => {
            const q = input.value.trim();
            if (q) searchIdeas(q);
        });
    }

    // Close prompts button
    const btnClosePrompts = document.getElementById("btn-close-prompts");
    if (btnClosePrompts) {
        btnClosePrompts.addEventListener("click", () => {
            document.getElementById("ai-prompts-section").style.display = "none";
        });
    }
}

function searchIdeas(query) {
    const grid = document.getElementById("ideas-cards-grid");
    const skeleton = document.getElementById("ideas-skeleton");
    const queryLabel = document.getElementById("search-query-label");
    const countLabel = document.getElementById("results-count-label");

    if (!grid) return;
    if (queryLabel) queryLabel.textContent = `"${query}"`;
    if (skeleton) skeleton.style.display = "grid";
    grid.innerHTML = "";

    fetch(`/api/ideas/search?q=${encodeURIComponent(query)}&limit=12`)
        .then((r) => r.json())
        .then((data) => {
            if (skeleton) skeleton.style.display = "none";
            if (data.ok && data.results && data.results.length) {
                if (countLabel) countLabel.textContent = `${data.results.length} video sẵn sàng`;
                data.results.forEach((v) => {
                    const card = document.createElement("div");
                    card.className = "idea-video-card";
                    card.innerHTML = `
                        <div class="idea-thumb-wrap">
                            <img src="${v.thumbnail}" alt="${v.title}" class="idea-thumb-img" loading="lazy">
                            <span class="idea-duration-badge">${v.duration_str || "00:00"}</span>
                        </div>
                        <div class="idea-card-body">
                            <h4 class="idea-card-title" title="${v.title}">${v.title}</h4>
                            <div class="idea-card-meta">
                                <span><i class="fa-regular fa-user"></i> ${v.uploader}</span>
                                <span><i class="fa-solid fa-eye"></i> ${v.views_str}</span>
                            </div>
                            <div class="idea-actions-row">
                                <button class="btn-idea-dl" data-url="${v.url}"><i class="fa-solid fa-bolt"></i> Tải nhanh</button>
                                <button class="btn-idea-analyze" data-url="${v.url}" title="Phân tích chất lượng"><i class="fa-solid fa-wand-magic-sparkles"></i></button>
                                <button class="btn-idea-prompts" data-title="${v.title}" title="Gợi ý kịch bản"><i class="fa-solid fa-lightbulb"></i></button>
                            </div>
                        </div>
                    `;

                    // 1-Click Fast Download
                    card.querySelector(".btn-idea-dl").addEventListener("click", () => {
                        fastDownloadUrl(v.url);
                    });

                    // Analyze Details
                    card.querySelector(".btn-idea-analyze").addEventListener("click", () => {
                        switchTab("tab-download");
                        document.getElementById("url-input").value = v.url;
                        triggerAnalysis(v.url);
                    });

                    // Prompts Generation
                    card.querySelector(".btn-idea-prompts").addEventListener("click", () => {
                        loadCreativePrompts(v.title);
                    });

                    grid.appendChild(card);
                });
            } else {
                if (countLabel) countLabel.textContent = `0 kết quả`;
                grid.innerHTML = `<div class="empty-state"><div class="empty-icon"><i class="fa-solid fa-magnifying-glass"></i></div><h3>Không tìm thấy video nào</h3><p>Hãy thử tìm kiếm với từ khóa khác.</p></div>`;
            }
        })
        .catch(() => {
            if (skeleton) skeleton.style.display = "none";
            showToast("Lỗi khi tìm kiếm video từ internet!", "error");
        });

    loadCreativePrompts(query);
}

function loadCreativePrompts(topic) {
    const section = document.getElementById("ai-prompts-section");
    const topicLabel = document.getElementById("prompt-topic-name");
    const hooksList = document.getElementById("prompt-hooks-list");
    const outlineList = document.getElementById("prompt-outline-list");
    const tagsContainer = document.getElementById("prompt-tags-container");

    if (!section) return;

    fetch(`/api/ideas/prompts?topic=${encodeURIComponent(topic)}`)
        .then((r) => r.json())
        .then((data) => {
            if (data.ok && data.prompts) {
                const p = data.prompts;
                if (topicLabel) topicLabel.textContent = `"${p.topic}"`;

                if (hooksList) {
                    hooksList.innerHTML = p.hooks
                        .map((h) => `<li><i class="fa-solid fa-angle-right text-cyan"></i> ${h}</li>`)
                        .join("");
                }

                if (outlineList) {
                    outlineList.innerHTML = p.script_outline
                        .map((s) => `<li><i class="fa-regular fa-clock text-violet"></i> ${s}</li>`)
                        .join("");
                }

                if (tagsContainer) {
                    tagsContainer.innerHTML = p.hashtags
                        .map((t) => `<span class="prompt-tag-pill">${t}</span>`)
                        .join("");

                    tagsContainer.querySelectorAll(".prompt-tag-pill").forEach((pill) => {
                        pill.addEventListener("click", () => {
                            navigator.clipboard.writeText(pill.textContent);
                            showToast(`Đã sao chép ${pill.textContent}!`, "info");
                        });
                    });
                }

                section.style.display = "block";
            }
        });
}

function fastDownloadUrl(url) {
    fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            url,
            quality: "best",
            audio_only: false,
            audio_bitrate: "192",
        }),
    })
        .then((r) => r.json())
        .then((res) => {
            if (res.ok) {
                showToast("⚡ Đã bắt đầu tải nhanh! Đang chuyển sang Hàng đợi...", "success");
                switchTab("tab-tasks");
            } else {
                showToast(res.error || "Không thể tải video!", "error");
            }
        })
        .catch(() => showToast("Lỗi kết nối máy chủ!", "error"));
}

// ─────────────────────────────────────────────────────────── 8. TASKS & QUEUE MANAGER
function renderTasks() {
    fetch("/api/tasks")
        .then((r) => r.json())
        .then((data) => {
            if (data.ok) {
                const container = document.getElementById("tasks-container");
                const empty = document.getElementById("tasks-empty");
                const counter = document.getElementById("active-tasks-count");

                if (!container) return;

                const tasks = data.tasks || [];
                const runningCount = tasks.filter((t) => t.status === "running").length;

                if (counter) {
                    counter.textContent = runningCount;
                    counter.style.display = runningCount > 0 ? "inline-block" : "none";
                }

                const tasksBadge = document.getElementById("tasks-badge");
                if (tasksBadge) {
                    tasksBadge.textContent = runningCount > 0 ? `${runningCount} đang tải` : `${tasks.length}`;
                    tasksBadge.style.color = runningCount > 0 ? "var(--cyan)" : "var(--text-secondary)";
                }

                if (!tasks.length) {
                    if (empty) empty.style.display = "flex";
                    return;
                }
                if (empty) empty.style.display = "none";

                container.innerHTML = "";
                tasks.forEach((t) => {
                    const card = document.createElement("div");
                    card.className = `task-card-item ${t.status}`;
                    const prog = t.progress || {};
                    const pct = prog.percent || (t.status === "completed" ? 100 : 0);

                    card.innerHTML = `
                        <div class="task-top-row">
                            <span class="task-title"><i class="fa-solid fa-download text-cyan"></i> ${t.url}</span>
                            <span class="task-status-pill ${t.status}">${t.status === "running" ? "Đang tải" : t.status === "completed" ? "Xong" : "Lỗi"}</span>
                        </div>
                        <div class="task-progress-bar-wrap">
                            <div class="task-progress-fill" style="width: ${pct}%"></div>
                        </div>
                        <div class="task-meta-row">
                            <span><i class="fa-solid fa-gauge-high"></i> ${prog.speed || "—"} | ${prog.downloaded || "0 MB"}</span>
                            <span><strong>${pct.toFixed(1)}%</strong> | ETA: ${prog.eta || "—"}</span>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
        });
}

// ─────────────────────────────────────────────────────────── 9. MEDIA VAULT & CINEMA PLAYER
function initMediaVaultModule() {
    const filterInput = document.getElementById("vault-filter-input");
    const btnRefresh = document.getElementById("btn-refresh-vault");

    if (filterInput) {
        filterInput.addEventListener("input", () => {
            filterVaultGrid(filterInput.value.trim().toLowerCase());
        });
    }

    if (btnRefresh) {
        btnRefresh.addEventListener("click", loadVaultFiles);
    }

    document.querySelectorAll(".vault-filter-chips .filter-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".vault-filter-chips .filter-chip").forEach((c) => c.classList.remove("active"));
            chip.classList.add("active");
            filterVaultByType(chip.dataset.filter);
        });
    });
}

function loadVaultFiles() {
    fetch("/api/files")
        .then((r) => r.json())
        .then((data) => {
            if (data.ok) {
                AppState.vaultFiles = data.files || [];
                const countBadge = document.getElementById("vault-count");
                if (countBadge) countBadge.textContent = AppState.vaultFiles.length;

                const vaultBadge = document.getElementById("vault-badge");
                if (vaultBadge) vaultBadge.textContent = `${AppState.vaultFiles.length} tệp`;

                const videoCount = AppState.vaultFiles.filter((f) => f.type === "video").length;
                const audioCount = AppState.vaultFiles.filter((f) => f.type === "audio").length;

                document.getElementById("count-all").textContent = AppState.vaultFiles.length;
                document.getElementById("count-video").textContent = videoCount;
                document.getElementById("count-audio").textContent = audioCount;

                renderVaultGrid(AppState.vaultFiles);
                populateToolboxFileSelects();
                populateAIFileSelects();
                populateReupFileSelects();
            }
        });
}

function renderVaultGrid(files) {
    const grid = document.getElementById("vault-grid");
    const empty = document.getElementById("vault-empty");

    if (!grid) return;
    grid.innerHTML = "";

    if (!files || !files.length) {
        if (empty) empty.style.display = "flex";
        return;
    }
    if (empty) empty.style.display = "none";

    files.forEach((file) => {
        const card = document.createElement("div");
        card.className = "media-card";
        const isAudio = file.type === "audio" || (file.ext && ["mp3", "m4a", "wav", "flac", "aac", "ogg"].includes(file.ext.replace(/^\./, "").toLowerCase()));
        const dateDisplay = file.date_str || file.modified_str || "—";
        const sizeDisplay = file.size_str || "0 MB";
        const extName = (file.ext || (isAudio ? "MP3" : "MP4")).toUpperCase().replace(/^\./, "");

        card.innerHTML = `
            <div class="media-preview-box" data-filename="${encodeURIComponent(file.filename)}" data-type="${isAudio ? 'audio' : 'video'}">
                ${
                    isAudio
                        ? `<div class="audio-disc-preview">
                             <i class="fa-solid fa-music"></i>
                             <span class="preview-badge audio">${extName}</span>
                           </div>`
                        : `<div class="video-preview-thumb-box">
                             <i class="fa-solid fa-film preview-center-icon"></i>
                             <span class="preview-badge video">${extName}</span>
                           </div>`
                }
                <div class="media-play-overlay"><i class="fa-solid fa-play"></i></div>
            </div>
            <div class="media-card-body">
                <h4 class="media-file-name" title="${file.filename}">${file.filename}</h4>
                <div class="media-file-info">
                    <span title="Dung lượng"><i class="fa-regular fa-hard-drive"></i> ${sizeDisplay}</span>
                    <span title="Thời gian tải"><i class="fa-regular fa-clock"></i> ${dateDisplay}</span>
                </div>
                <div class="media-card-actions">
                    <button class="btn-subtle btn-sm btn-play-media"><i class="fa-solid fa-play"></i> Phát</button>
                    <a href="/api/files/download/${encodeURIComponent(file.filename)}" class="btn-subtle btn-sm" download><i class="fa-solid fa-download"></i> Tải về</a>
                    <button class="btn-subtle btn-sm btn-del-media text-red" data-filename="${encodeURIComponent(file.filename)}" title="Xóa video"><i class="fa-solid fa-trash"></i></button>
                </div>
            </div>
        `;

        card.querySelector(".media-preview-box").addEventListener("click", () => openCinemaPlayer(file));
        card.querySelector(".btn-play-media").addEventListener("click", () => openCinemaPlayer(file));
        card.querySelector(".btn-del-media").addEventListener("click", (e) => {
            e.stopPropagation();
            if (confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn tệp:\n${file.filename}?`)) {
                deleteFile(file.filename);
            }
        });

        grid.appendChild(card);
    });
}

function filterVaultGrid(query) {
    const filtered = AppState.vaultFiles.filter((f) => f.filename.toLowerCase().includes(query));
    renderVaultGrid(filtered);
}

function filterVaultByType(type) {
    if (type === "all") {
        renderVaultGrid(AppState.vaultFiles);
    } else {
        const filtered = AppState.vaultFiles.filter((f) => f.type === type);
        renderVaultGrid(filtered);
    }
}

async function deleteFile(filename) {
    const enc = encodeURIComponent(filename);

    // 1. Dừng và giải phóng toàn bộ thẻ media đang mở file này
    document.querySelectorAll("video, audio").forEach((m) => {
        if (m.src && m.src.includes(enc)) {
            m.pause();
            m.removeAttribute("src");
            m.load();
        }
    });

    // Nếu rạp chiếu Cinema Modal đang phát video này, đóng và giải phóng ngay
    const cinemaModal = document.getElementById("cinema-modal");
    if (cinemaModal && cinemaModal.style.display !== "none") {
        closeCinemaPlayer();
    }

    showToast("Đang giải phóng và xử lý xóa tệp...", "info");

    // 2. Chờ 350ms để trình duyệt và Python server đóng hẳn socket handle
    await new Promise((resolve) => setTimeout(resolve, 350));

    try {
        const resp = await fetch(`/api/files/${enc}`, { method: "DELETE" });
        const res = await resp.json();
        if (res.ok) {
            showToast(`Đã xóa thành công: ${filename}`, "success");
            loadVaultFiles();
        } else {
            showToast(res.error || "Không thể xóa tệp!", "error");
        }
    } catch (err) {
        showToast("Lỗi kết nối máy chủ khi xóa tệp: " + err, "error");
    }
}

// ─────────────────────────────────────────────────────────── 10. CINEMA PLAYER & AUDIO WAVEFORM
function initCinemaPlayer() {
    const modal = document.getElementById("cinema-modal");
    const btnClose = document.getElementById("btn-close-cinema");

    if (btnClose && modal) {
        btnClose.addEventListener("click", () => closeCinemaPlayer());
        modal.addEventListener("click", (e) => {
            if (e.target === modal) closeCinemaPlayer();
        });
    }
}

function openCinemaPlayer(file) {
    const modal = document.getElementById("cinema-modal");
    const title = document.getElementById("cinema-title");
    const videoScreen = document.getElementById("cinema-screen-container");
    const audioScreen = document.getElementById("cinema-audio-container");
    const videoElem = document.getElementById("cinema-video");
    const audioElem = document.getElementById("cinema-audio");
    const downloadBtn = document.getElementById("btn-cinema-download");

    if (!modal) return;

    title.textContent = file.filename;
    downloadBtn.href = `/api/files/download/${encodeURIComponent(file.filename)}`;

    const streamUrl = `/api/files/stream/${encodeURIComponent(file.filename)}`;

    if (file.type === "video") {
        videoScreen.style.display = "block";
        audioScreen.style.display = "none";
        audioElem.pause();
        videoElem.src = streamUrl;
        videoElem.play();
    } else {
        videoScreen.style.display = "none";
        audioScreen.style.display = "flex";
        videoElem.pause();
        audioElem.src = streamUrl;
        audioElem.play();
        startWaveformVisualizer(audioElem);
    }

    modal.style.display = "flex";
}

function closeCinemaPlayer() {
    const modal = document.getElementById("cinema-modal");
    const videoElem = document.getElementById("cinema-video");
    const audioElem = document.getElementById("cinema-audio");

    if (videoElem) {
        videoElem.pause();
        videoElem.src = "";
    }
    if (audioElem) {
        audioElem.pause();
        audioElem.src = "";
    }
    if (modal) modal.style.display = "none";
}

function startWaveformVisualizer(audioElement) {
    const canvas = document.getElementById("audio-waveform-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (!AppState.audioCtx) {
        AppState.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        AppState.audioAnalyser = AppState.audioCtx.createAnalyser();
        const source = AppState.audioCtx.createMediaElementSource(audioElement);
        source.connect(AppState.audioAnalyser);
        AppState.audioAnalyser.connect(AppState.audioCtx.destination);
        AppState.audioAnalyser.fftSize = 64;
    }

    const bufferLength = AppState.audioAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function drawWave() {
        if (audioElement.paused || audioElement.ended) return;
        requestAnimationFrame(drawWave);

        AppState.audioAnalyser.getByteFrequencyData(dataArray);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 2;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const barHeight = (dataArray[i] / 255) * canvas.height;
            const grad = ctx.createLinearGradient(0, canvas.height, 0, 0);
            grad.addColorStop(0, "#06b6d4");
            grad.addColorStop(1, "#8b5cf6");

            ctx.fillStyle = grad;
            ctx.fillRect(x, canvas.height - barHeight, barWidth - 2, barHeight);
            x += barWidth;
        }
    }

    audioElement.addEventListener("play", () => {
        if (AppState.audioCtx && AppState.audioCtx.state === "suspended") {
            AppState.audioCtx.resume();
        }
        drawWave();
    });
}

// ─────────────────────────────────────────────────────────── 10B. AI STUDIO MODULE (ATRIA DAWN AI)
let aiThinkingInterval = null;

function setAIThinking(isThinking, customTitle = "Atria AI đang tư duy suy luận chuyên sâu...") {
    const indicator = document.getElementById("ai-thinking-indicator");
    const resultContainer = document.getElementById("ai-result-container");
    const reasoningContainer = document.getElementById("ai-reasoning-container");
    if (!indicator) return;

    const titleEl = indicator.querySelector(".thinking-title");
    if (titleEl) titleEl.textContent = customTitle;

    if (isThinking) {
        indicator.style.display = "flex";
        if (resultContainer) resultContainer.style.opacity = "0.2";
        if (reasoningContainer) reasoningContainer.style.display = "none";

        let currentStep = 1;
        const steps = [
            document.getElementById("think-step-1"),
            document.getElementById("think-step-2"),
            document.getElementById("think-step-3"),
        ];
        steps.forEach((s, idx) => {
            if (s) s.className = idx === 0 ? "think-step active" : "think-step";
        });

        clearInterval(aiThinkingInterval);
        aiThinkingInterval = setInterval(() => {
            currentStep = (currentStep % 3) + 1;
            steps.forEach((s, idx) => {
                if (s) {
                    if (idx + 1 === currentStep) {
                        s.className = "think-step active";
                    } else if (idx + 1 < currentStep) {
                        s.className = "think-step done";
                    } else {
                        s.className = "think-step";
                    }
                }
            });
        }, 3500);
    } else {
        clearInterval(aiThinkingInterval);
        indicator.style.display = "none";
        if (resultContainer) resultContainer.style.opacity = "1";
    }
}

function renderAIOutput(typeLabel, content, reasoning = "") {
    const typeEl = document.getElementById("ai-output-type");
    const container = document.getElementById("ai-result-container");
    const reasoningContainer = document.getElementById("ai-reasoning-container");
    const reasoningText = document.getElementById("ai-reasoning-text");

    if (typeEl) typeEl.textContent = typeLabel;
    AppState.currentAIOutput = content || "";

    if (container) {
        container.innerHTML = `<div class="ai-formatted-output">${formatMarkdown(content || "Không có kết quả trả về.")}</div>`;
    }

    if (reasoning && reasoning.trim()) {
        if (reasoningContainer) reasoningContainer.style.display = "block";
        if (reasoningText) {
            reasoningText.innerHTML = `<div class="reasoning-inner">${formatMarkdown(reasoning)}</div>`;
        }
    } else {
        if (reasoningContainer) reasoningContainer.style.display = "none";
    }
}

function formatMarkdown(text) {
    if (!text) return "";
    let html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h4 class="ai-md-h4">$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3 class="ai-md-h3">$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2 class="ai-md-h2">$1</h2>');

    // Bold / italic
    html = html.replace(/\*\*\*(.*?)\*\*\*/gim, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Inline code & pre
    html = html.replace(/```([a-z]*)\n([\s\S]*?)```/gim, '<pre class="ai-code-block"><code>$2</code></pre>');
    html = html.replace(/`([^`]+)`/gim, '<code class="ai-inline-code">$1</code>');

    // Lists
    html = html.replace(/^\s*[-*]\s+(.*$)/gim, '<div class="ai-bullet"><i class="fa-solid fa-angle-right text-cyan"></i> <span>$1</span></div>');
    html = html.replace(/^\s*(\d+)\.\s+(.*$)/gim, '<div class="ai-num-item"><span class="num-badge">$1</span> <span>$2</span></div>');

    // Paragraphs
    html = html.replace(/\n\n+/g, '</p><p class="ai-md-p">');
    html = html.replace(/\n/g, '<br>');

    return `<div class="ai-markdown-body"><p class="ai-md-p">${html}</p></div>`;
}

function initAIStudioModule() {
    // 1. Sub-panel switching
    document.querySelectorAll(".ai-pill-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const action = btn.dataset.action;
            document.querySelectorAll(".ai-pill-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            document.querySelectorAll(".ai-subpanel").forEach((p) => (p.style.display = "none"));
            const activePanel = document.getElementById(`ai-panel-${action}`);
            if (activePanel) activePanel.style.display = "block";
        });
    });

    // 2. Quick suggestion chips
    document.querySelectorAll(".ai-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            const targetId = chip.dataset.target;
            const val = chip.dataset.val;
            const targetInput = document.getElementById(targetId);
            if (targetInput) {
                targetInput.value = val;
                targetInput.focus();
            }
        });
    });

    // 3. Generate 5 Viral Hooks
    const btnHooks = document.getElementById("btn-generate-hooks");
    if (btnHooks) {
        btnHooks.addEventListener("click", () => {
            const topic = document.getElementById("ai-hooks-topic")?.value?.trim();
            if (!topic) {
                showToast("Vui lòng nhập chủ đề hoặc tiêu đề video!", "error");
                return;
            }

            btnHooks.disabled = true;
            btnHooks.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang suy luận...`;
            setAIThinking(true, "Atria AI đang xây dựng 5 Hook tâm lý giữ chân 3s đầu...");

            fetch("/api/ai/hooks", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic }),
            })
                .then((r) => r.json())
                .then((res) => {
                    btnHooks.disabled = false;
                    btnHooks.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Sinh 5 Hook Bằng Atria AI`;
                    setAIThinking(false);

                    if (res.ok) {
                        renderAIOutput("5 Hook Câu View 3 Giây Đầu", res.content, res.reasoning);
                        showToast("Đã tạo 5 Hook thành công!", "success");
                    } else {
                        showToast(res.error || "Lỗi khi gọi Atria AI!", "error");
                    }
                })
                .catch(() => {
                    btnHooks.disabled = false;
                    btnHooks.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Sinh 5 Hook Bằng Atria AI`;
                    setAIThinking(false);
                    showToast("Lỗi kết nối máy chủ Atria AI!", "error");
                });
        });
    }

    // 4. Generate Shorts Script
    const btnScript = document.getElementById("btn-generate-script");
    if (btnScript) {
        btnScript.addEventListener("click", () => {
            const topic = document.getElementById("ai-script-topic")?.value?.trim();
            const style = document.getElementById("ai-script-style")?.value || "kịch tính, dồn dập, giật gân";
            const duration = parseInt(document.getElementById("ai-script-duration")?.value || "60", 10);

            if (!topic) {
                showToast("Vui lòng nhập ý tưởng kịch bản Shorts/TikTok!", "error");
                return;
            }

            btnScript.disabled = true;
            btnScript.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang viết kịch bản...`;
            setAIThinking(true, `Atria AI đang sáng tạo kịch bản ${duration}s phong cách ${style}...`);

            fetch("/api/ai/script", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic, style, duration_seconds: duration }),
            })
                .then((r) => r.json())
                .then((res) => {
                    btnScript.disabled = false;
                    btnScript.innerHTML = `<i class="fa-solid fa-pen-nib"></i> Viết Kịch Bản Chi Tiết`;
                    setAIThinking(false);

                    if (res.ok) {
                        renderAIOutput(`Kịch Bản Shorts (${duration}s)`, res.content, res.reasoning);
                        showToast("Đã sinh kịch bản Shorts thành công!", "success");
                    } else {
                        showToast(res.error || "Lỗi khi tạo kịch bản!", "error");
                    }
                })
                .catch(() => {
                    btnScript.disabled = false;
                    btnScript.innerHTML = `<i class="fa-solid fa-pen-nib"></i> Viết Kịch Bản Chi Tiết`;
                    setAIThinking(false);
                    showToast("Lỗi kết nối máy chủ Atria AI!", "error");
                });
        });
    }

    // 5. Video Summarizer
    const btnSummarize = document.getElementById("btn-generate-summary");
    if (btnSummarize) {
        btnSummarize.addEventListener("click", () => {
            const fileSelect = document.getElementById("ai-sum-file-select");
            const manualTitle = document.getElementById("ai-sum-title")?.value?.trim();
            const desc = document.getElementById("ai-sum-desc")?.value?.trim();

            const title = manualTitle || fileSelect?.value || "";
            if (!title) {
                showToast("Vui lòng chọn video từ kho hoặc nhập tiêu đề!", "error");
                return;
            }

            btnSummarize.disabled = true;
            btnSummarize.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang phân tích...`;
            setAIThinking(true, `Atria AI đang phân tích & tóm tắt video: ${title}...`);

            fetch("/api/ai/summarize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, description: desc }),
            })
                .then((r) => r.json())
                .then((res) => {
                    btnSummarize.disabled = false;
                    btnSummarize.innerHTML = `<i class="fa-solid fa-brain"></i> Phân Tích & Tóm Tắt Bằng AI`;
                    setAIThinking(false);

                    if (res.ok) {
                        renderAIOutput("Tóm Tắt & Phân Tích Video", res.content, res.reasoning);
                        showToast("Đã phân tích tóm tắt xong!", "success");
                    } else {
                        showToast(res.error || "Lỗi tóm tắt video!", "error");
                    }
                })
                .catch(() => {
                    btnSummarize.disabled = false;
                    btnSummarize.innerHTML = `<i class="fa-solid fa-brain"></i> Phân Tích & Tóm Tắt Bằng AI`;
                    setAIThinking(false);
                    showToast("Lỗi kết nối máy chủ Atria AI!", "error");
                });
        });
    }

    // 6. SEO & Tags Generator
    const btnSeo = document.getElementById("btn-generate-seo");
    if (btnSeo) {
        btnSeo.addEventListener("click", () => {
            const topic = document.getElementById("ai-seo-topic")?.value?.trim();
            const platform = document.getElementById("ai-seo-platform")?.value || "tiktok";

            if (!topic) {
                showToast("Vui lòng nhập chủ đề nội dung video!", "error");
                return;
            }

            btnSeo.disabled = true;
            btnSeo.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang tối ưu...`;
            setAIThinking(true, `Atria AI đang phân tích xu hướng SEO & bộ thẻ cho ${platform}...`);

            fetch("/api/ai/seo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic, platform }),
            })
                .then((r) => r.json())
                .then((res) => {
                    btnSeo.disabled = false;
                    btnSeo.innerHTML = `<i class="fa-solid fa-tags"></i> Tối Ưu Bộ Thẻ & Tiêu Đề`;
                    setAIThinking(false);

                    if (res.ok) {
                        renderAIOutput(`Tối Ưu SEO & Bộ Thẻ (${platform.toUpperCase()})`, res.content, res.reasoning);
                        showToast("Đã tạo bộ thẻ SEO thành công!", "success");
                    } else {
                        showToast(res.error || "Lỗi tối ưu SEO!", "error");
                    }
                })
                .catch(() => {
                    btnSeo.disabled = false;
                    btnSeo.innerHTML = `<i class="fa-solid fa-tags"></i> Tối Ưu Bộ Thẻ & Tiêu Đề`;
                    setAIThinking(false);
                    showToast("Lỗi kết nối máy chủ Atria AI!", "error");
                });
        });
    }

    // 7. AI Creative Chat
    const btnSendChat = document.getElementById("btn-send-chat");
    const chatInput = document.getElementById("ai-chat-input");
    const chatWindow = document.getElementById("ai-chat-window");

    function sendChatMessage() {
        const msg = chatInput?.value?.trim();
        if (!msg) return;

        // Append user bubble
        const userBubble = document.createElement("div");
        userBubble.className = "ai-chat-bubble user";
        userBubble.innerHTML = `<div class="chat-avatar"><i class="fa-solid fa-user"></i></div><div class="chat-msg">${msg.replace(/&/g, "&amp;").replace(/</g, "&lt;")}</div>`;
        chatWindow.appendChild(userBubble);
        chatInput.value = "";
        chatWindow.scrollTop = chatWindow.scrollHeight;

        // Append loading bot bubble
        const botBubble = document.createElement("div");
        botBubble.className = "ai-chat-bubble bot";
        botBubble.innerHTML = `<div class="chat-avatar"><i class="fa-solid fa-robot"></i></div><div class="chat-msg"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang suy nghĩ...</div>`;
        chatWindow.appendChild(botBubble);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        fetch("/api/ai/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg }),
        })
            .then((r) => r.json())
            .then((res) => {
                if (res.ok) {
                    botBubble.querySelector(".chat-msg").innerHTML = formatMarkdown(res.content);
                    if (res.reasoning) {
                        const rDiv = document.createElement("div");
                        rDiv.className = "chat-reasoning-snippet";
                        rDiv.innerHTML = `<small style="color: var(--violet); font-size: 11px;"><i class="fa-solid fa-microchip"></i> Reasoning Preview: ${res.reasoning.slice(0, 140)}...</small>`;
                        botBubble.querySelector(".chat-msg").appendChild(rDiv);
                    }
                } else {
                    botBubble.querySelector(".chat-msg").textContent = res.error || "Lỗi phản hồi từ AI.";
                }
                chatWindow.scrollTop = chatWindow.scrollHeight;
            })
            .catch(() => {
                botBubble.querySelector(".chat-msg").textContent = "Lỗi kết nối máy chủ AI.";
                chatWindow.scrollTop = chatWindow.scrollHeight;
            });
    }

    if (btnSendChat) btnSendChat.addEventListener("click", sendChatMessage);
    if (chatInput) {
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendChatMessage();
        });
    }

    // 8. Reasoning Accordion Toggle
    const btnToggleReasoning = document.getElementById("btn-toggle-reasoning");
    const reasoningText = document.getElementById("ai-reasoning-text");
    if (btnToggleReasoning && reasoningText) {
        btnToggleReasoning.addEventListener("click", () => {
            const isHidden = reasoningText.style.display === "none";
            reasoningText.style.display = isHidden ? "block" : "none";
            btnToggleReasoning.querySelector(".toggle-arrow").classList.toggle("rotated", isHidden);
        });
    }

    // 9. Copy AI Output
    const btnCopyOutput = document.getElementById("btn-copy-ai-output");
    if (btnCopyOutput) {
        btnCopyOutput.addEventListener("click", () => {
            const textToCopy = AppState.currentAIOutput || document.getElementById("ai-result-container")?.innerText;
            if (!textToCopy || textToCopy.includes("Không Gian Sáng Tạo")) {
                showToast("Chưa có kết quả để sao chép!", "error");
                return;
            }
            navigator.clipboard.writeText(textToCopy);
            showToast("Đã sao chép nội dung AI vào Clipboard!", "success");
        });
    }

    // 10. Download AI Script as .txt
    const btnDownloadScript = document.getElementById("btn-download-ai-script");
    if (btnDownloadScript) {
        btnDownloadScript.addEventListener("click", () => {
            const textToSave = AppState.currentAIOutput || document.getElementById("ai-result-container")?.innerText;
            if (!textToSave || textToSave.includes("Không Gian Sáng Tạo")) {
                showToast("Chưa có kết quả để lưu file!", "error");
                return;
            }
            const blob = new Blob([textToSave], { type: "text/plain;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `atria_ai_script_${Date.now()}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast("Đã lưu tệp kịch bản .txt thành công!", "success");
        });
    }
}

// ─────────────────────────────────────────────────────────── 10C. RE-UP STUDIO MODULE
function formatDuration(sec) {
    if (sec === null || sec === undefined || isNaN(sec)) return "Hết video";
    const s = Math.floor(sec);
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}:${rem.toString().padStart(2, "0")}`;
}

function initReupStudioModule() {
    // 1. Preset 1-Click Anti-Copyright
    const btnPreset = document.getElementById("btn-preset-anti-copyright");
    if (btnPreset) {
        btnPreset.addEventListener("click", () => {
            const flip = document.getElementById("reup-flip-h");
            const speedRange = document.getElementById("reup-speed-range");
            const speedVal = document.getElementById("reup-speed-val");
            const zoom = document.getElementById("reup-zoom");
            const strip = document.getElementById("reup-strip-meta");
            const blur916 = document.getElementById("reup-blur-916");

            if (flip) flip.checked = true;
            if (speedRange) {
                speedRange.value = "1.04";
                if (speedVal) speedVal.textContent = "1.04x";
            }
            if (zoom) zoom.checked = true;
            if (strip) strip.checked = true;
            if (blur916) blur916.checked = false;

            showToast("🛡️ Đã kích hoạt Preset Lách Bản Quyền Toàn Diện!", "success");
        });
    }

    // 2. Speed Slider
    const speedRange = document.getElementById("reup-speed-range");
    const speedVal = document.getElementById("reup-speed-val");
    if (speedRange && speedVal) {
        speedRange.addEventListener("input", () => {
            const val = parseFloat(speedRange.value).toFixed(2);
            speedVal.textContent = `${val}x`;
        });
    }

    // 3. Re-Up File Select & Video Preview
    const fileSelect = document.getElementById("reup-file-select");
    const playerContainer = document.getElementById("reup-player-container");
    const videoPreview = document.getElementById("reup-video-preview");

    if (fileSelect) {
        fileSelect.addEventListener("change", () => {
            const filename = fileSelect.value;
            if (!filename) {
                if (playerContainer) playerContainer.style.display = "none";
                return;
            }

            if (playerContainer) playerContainer.style.display = "block";
            if (videoPreview) {
                videoPreview.src = `/api/files/stream/${encodeURIComponent(filename)}`;
                AppState.reupStart = 0;
                AppState.reupEnd = null;
                const startDisplay = document.getElementById("scrub-start-display");
                const endDisplay = document.getElementById("scrub-end-display");
                if (startDisplay) startDisplay.textContent = "0:00";
                if (endDisplay) endDisplay.textContent = "Hết video";
            }
        });
    }

    // 4. Scrubber Set Start / Set End
    const btnSetStart = document.getElementById("btn-set-start");
    const btnSetEnd = document.getElementById("btn-set-end");
    if (btnSetStart) {
        btnSetStart.addEventListener("click", () => {
            if (!videoPreview || !videoPreview.duration) {
                showToast("Vui lòng phát video để chọn thời điểm!", "error");
                return;
            }
            AppState.reupStart = Math.floor(videoPreview.currentTime);
            const startDisplay = document.getElementById("scrub-start-display");
            if (startDisplay) startDisplay.textContent = formatDuration(AppState.reupStart);
            showToast(`Đã đặt điểm bắt đầu: ${formatDuration(AppState.reupStart)}`, "info");
        });
    }

    if (btnSetEnd) {
        btnSetEnd.addEventListener("click", () => {
            if (!videoPreview || !videoPreview.duration) {
                showToast("Vui lòng phát video để chọn thời điểm!", "error");
                return;
            }
            AppState.reupEnd = Math.ceil(videoPreview.currentTime);
            const endDisplay = document.getElementById("scrub-end-display");
            if (endDisplay) endDisplay.textContent = formatDuration(AppState.reupEnd);
            showToast(`Đã đặt điểm kết thúc: ${formatDuration(AppState.reupEnd)}`, "info");
        });
    }

    // 5. Execute Re-Up Process
    const btnProcess = document.getElementById("btn-process-reup");
    const progressBox = document.getElementById("reup-progress-box");
    const progressBar = document.getElementById("reup-progress-bar");
    const progressMsg = document.getElementById("reup-progress-msg");

    if (btnProcess) {
        btnProcess.addEventListener("click", () => {
            const filename = document.getElementById("reup-file-select")?.value;
            if (!filename) {
                showToast("Vui lòng chọn video cần xử lý!", "error");
                return;
            }

            const flipH = document.getElementById("reup-flip-h")?.checked ?? false;
            const speed = parseFloat(document.getElementById("reup-speed-range")?.value || "1.00");
            const blur916 = document.getElementById("reup-blur-916")?.checked ?? false;
            const zoom = document.getElementById("reup-zoom")?.checked ?? false;
            const stripMeta = document.getElementById("reup-strip-meta")?.checked ?? true;
            const watermark = document.getElementById("reup-watermark-text")?.value?.trim() || "";

            const payload = {
                filename,
                flip_h: flipH,
                speed,
                blur_canvas_916: blur916,
                zoom: zoom ? 1.02 : 1.00,
                strip_metadata: stripMeta,
                watermark_text: watermark,
                cut_start: AppState.reupStart > 0 ? AppState.reupStart : null,
                cut_end: AppState.reupEnd || null,
            };

            btnProcess.disabled = true;
            btnProcess.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang xử lý video bằng FFmpeg Master...`;
            if (progressBox) progressBox.style.display = "block";
            if (progressBar) progressBar.style.width = "15%";
            if (progressMsg) progressMsg.textContent = "Khởi tạo bộ lọc FFmpeg & đọc khung hình...";

            let prog = 15;
            const pInterval = setInterval(() => {
                if (prog < 88) {
                    prog += Math.floor(Math.random() * 12) + 5;
                    if (prog > 88) prog = 88;
                    if (progressBar) progressBar.style.width = `${prog}%`;
                    if (progressMsg) {
                        if (prog < 40) progressMsg.textContent = "Đang lật gương & điều chỉnh tốc độ vi mô...";
                        else if (prog < 70) progressMsg.textContent = "Đang kết xuất phông nền & chuẩn hóa âm thanh...";
                        else progressMsg.textContent = "Làm mới Metadata & xuất tệp video mới...";
                    }
                }
            }, 1200);

            fetch("/api/reup/process", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
                .then((r) => r.json())
                .then((res) => {
                    clearInterval(pInterval);
                    btnProcess.disabled = false;
                    btnProcess.innerHTML = `<i class="fa-solid fa-bolt"></i> BẮT ĐẦU TÁI TẠO VIDEO LÁCH BẢN QUYỀN`;

                    if (res.ok) {
                        if (progressBar) progressBar.style.width = "100%";
                        if (progressMsg) progressMsg.textContent = `Thành công: ${res.output_file} (${res.size_str})`;
                        showToast(`⚡ Tái tạo thành công: ${res.output_file}!`, "success");
                        loadVaultFiles();
                        setTimeout(() => {
                            if (progressBox) progressBox.style.display = "none";
                            switchTab("tab-vault");
                        }, 1800);
                    } else {
                        if (progressBar) progressBar.style.width = "0%";
                        if (progressMsg) progressMsg.textContent = "Lỗi xử lý!";
                        showToast(res.error || "Lỗi khi xử lý video!", "error");
                    }
                })
                .catch(() => {
                    clearInterval(pInterval);
                    btnProcess.disabled = false;
                    btnProcess.innerHTML = `<i class="fa-solid fa-bolt"></i> BẮT ĐẦU TÁI TẠO VIDEO LÁCH BẢN QUYỀN`;
                    if (progressBar) progressBar.style.width = "0%";
                    showToast("Lỗi kết nối máy chủ khi xử lý video!", "error");
                });
        });
    }
}

function populateAIFileSelects() {
    const select = document.getElementById("ai-sum-file-select");
    if (!select) return;
    const cur = select.value;
    select.innerHTML = '<option value="">-- Chọn video trong kho media --</option>';
    AppState.vaultFiles
        .filter((f) => f.type === "video")
        .forEach((f) => {
            const opt = new Option(`${f.filename} (${f.size_str})`, f.filename);
            select.add(opt);
        });
    if (cur) select.value = cur;
}

function populateReupFileSelects() {
    const select = document.getElementById("reup-file-select");
    if (!select) return;
    const cur = select.value;
    select.innerHTML = '<option value="">-- Chọn video cần lách bản quyền / tái tạo --</option>';
    AppState.vaultFiles
        .filter((f) => f.type === "video")
        .forEach((f) => {
            const opt = new Option(`${f.filename} (${f.size_str})`, f.filename);
            select.add(opt);
        });
    if (cur) select.value = cur;
}

// ─────────────────────────────────────────────────────────── 11. TOOLBOX MODULE
function initToolboxModule() {
    const btnCut = document.getElementById("btn-tool-cut");
    const btnConvert = document.getElementById("btn-tool-convert");

    if (btnCut) {
        btnCut.addEventListener("click", () => {
            const file = document.getElementById("tool-cut-file").value;
            const start = parseFloat(document.getElementById("tool-cut-start").value) || 0;
            const end = parseFloat(document.getElementById("tool-cut-end").value) || 10;

            if (!file) {
                showToast("Vui lòng chọn tệp cần cắt!", "error");
                return;
            }

            btnCut.disabled = true;
            btnCut.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang cắt tệp...`;

            fetch("/api/toolbox/cut", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: file, start, end }),
            })
                .then((r) => r.json())
                .then((res) => {
                    btnCut.disabled = false;
                    btnCut.innerHTML = `<i class="fa-solid fa-scissors"></i> Bắt đầu cắt tệp`;
                    if (res.ok) {
                        showToast(`Đã cắt thành công: ${res.output_file} (${res.size_str})`, "success");
                        loadVaultFiles();
                        switchTab("tab-vault");
                    } else {
                        showToast(res.error || "Lỗi khi cắt tệp!", "error");
                    }
                });
        });
    }

    if (btnConvert) {
        btnConvert.addEventListener("click", () => {
            const file = document.getElementById("tool-conv-file").value;
            const format = document.getElementById("tool-conv-format").value;
            const bitrate = document.getElementById("tool-conv-bitrate").value;

            if (!file) {
                showToast("Vui lòng chọn tệp cần chuyển đổi!", "error");
                return;
            }

            btnConvert.disabled = true;
            btnConvert.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang chuyển đổi...`;

            fetch("/api/toolbox/convert", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: file, target_format: format, bitrate }),
            })
                .then((r) => r.json())
                .then((res) => {
                    btnConvert.disabled = false;
                    btnConvert.innerHTML = `<i class="fa-solid fa-repeat"></i> Chuyển đổi định dạng`;
                    if (res.ok) {
                        showToast(`Chuyển đổi thành công: ${res.output_file}`, "success");
                        loadVaultFiles();
                        switchTab("tab-vault");
                    } else {
                        showToast(res.error || "Lỗi chuyển đổi tệp!", "error");
                    }
                });
        });
    }
}

function populateToolboxFileSelects() {
    const cutSelect = document.getElementById("tool-cut-file");
    const convSelect = document.getElementById("tool-conv-file");

    if (!cutSelect || !convSelect) return;

    cutSelect.innerHTML = "";
    convSelect.innerHTML = "";

    AppState.vaultFiles.forEach((f) => {
        const opt1 = new Option(`${f.filename} (${f.size_str})`, f.filename);
        const opt2 = new Option(`${f.filename} (${f.size_str})`, f.filename);
        cutSelect.add(opt1);
        convSelect.add(opt2);
    });
}

// ─────────────────────────────────────────────────────────── 12. SHARE & CLOUDFLARE MODULE
function initShareModule() {
    const btnCopyLan = document.getElementById("btn-copy-lan");
    const btnCopyPublic = document.getElementById("btn-copy-public");
    const btnToggleTunnel = document.getElementById("btn-toggle-tunnel");

    if (btnCopyLan) {
        btnCopyLan.addEventListener("click", () => {
            const txt = document.getElementById("lan-ip-display").textContent;
            navigator.clipboard.writeText(txt);
            showToast("Đã sao chép link mạng LAN!", "success");
        });
    }

    if (btnCopyPublic) {
        btnCopyPublic.addEventListener("click", () => {
            const txt = document.getElementById("public-url-display").textContent;
            navigator.clipboard.writeText(txt);
            showToast("Đã sao chép link công khai toàn cầu!", "success");
        });
    }

    if (btnToggleTunnel) {
        btnToggleTunnel.addEventListener("click", () => {
            const isRunning = btnToggleTunnel.classList.contains("active");
            btnToggleTunnel.disabled = true;

            if (isRunning) {
                fetch("/api/system/tunnel/stop", { method: "POST" })
                    .then((r) => r.json())
                    .then(() => {
                        btnToggleTunnel.disabled = false;
                        btnToggleTunnel.classList.remove("active");
                        btnToggleTunnel.innerHTML = `<i class="fa-solid fa-play"></i> Bật Link Công Khai`;
                        document.getElementById("tunnel-status-label").textContent = "Chưa kích hoạt";
                        document.getElementById("public-url-row").style.display = "none";
                        showToast("Đã dừng link công khai.", "info");
                    });
            } else {
                btnToggleTunnel.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang tạo link...`;
                fetch("/api/system/tunnel/start", { method: "POST" })
                    .then((r) => r.json())
                    .then((res) => {
                        btnToggleTunnel.disabled = false;
                        if (res.ok) {
                            btnToggleTunnel.classList.add("active");
                            btnToggleTunnel.innerHTML = `<i class="fa-solid fa-stop"></i> Tắt Link Công Khai`;
                            document.getElementById("tunnel-status-label").textContent = "Đang phát trực tuyến";
                            document.getElementById("public-url-display").textContent = res.public_url;
                            document.getElementById("public-url-row").style.display = "flex";
                            showToast("Link công khai Cloudflare HTTPS đã sẵn sàng!", "success");
                        } else {
                            btnToggleTunnel.innerHTML = `<i class="fa-solid fa-play"></i> Bật Link Công Khai`;
                            showToast(res.error || "Không thể tạo tunnel!", "error");
                        }
                    });
            }
        });
    }
}

// ─────────────────────────────────────────────────────────── 13. SETTINGS & SYSTEM MODULE
function initSettingsModule() {
    const btnSave = document.getElementById("btn-save-settings");
    const btnUpdateFfmpeg = document.getElementById("btn-update-ffmpeg");
    const btnUpdateYtdlp = document.getElementById("btn-update-ytdlp");
    const btnToggleKeyVis = document.getElementById("btn-toggle-key-vis");
    const btnPingAtria = document.getElementById("btn-ping-atria");

    if (btnToggleKeyVis) {
        btnToggleKeyVis.addEventListener("click", () => {
            const keyInput = document.getElementById("cfg-atria-key");
            if (keyInput) {
                const isPass = keyInput.type === "password";
                keyInput.type = isPass ? "text" : "password";
                btnToggleKeyVis.innerHTML = isPass ? `<i class="fa-regular fa-eye-slash"></i>` : `<i class="fa-regular fa-eye"></i>`;
            }
        });
    }

    if (btnPingAtria) {
        btnPingAtria.addEventListener("click", () => {
            const keyInput = document.getElementById("cfg-atria-key");
            const key = keyInput?.value?.trim() || "";
            const statusLabel = document.getElementById("setting-ai-status");

            btnPingAtria.disabled = true;
            btnPingAtria.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang test...`;

            fetch("/api/ai/ping", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: key }),
            })
                .then((r) => r.json())
                .then((res) => {
                    btnPingAtria.disabled = false;
                    btnPingAtria.innerHTML = `<i class="fa-solid fa-wifi"></i> Ping AI`;

                    if (res.ok) {
                        if (statusLabel) {
                            statusLabel.innerHTML = `<span style="color: var(--emerald); font-weight: 600;"><i class="fa-solid fa-circle-check"></i> Kết nối Atria AI OK! Độ trễ: ${res.latency_ms}ms (Atria-Dawn-Preview)</span>`;
                        }
                        showToast(`⚡ Kết nối Atria AI thành công! Độ trễ: ${res.latency_ms}ms`, "success");
                    } else {
                        if (statusLabel) {
                            statusLabel.innerHTML = `<span style="color: var(--red);"><i class="fa-solid fa-circle-xmark"></i> Lỗi: ${res.error || "Không kết nối được"}</span>`;
                        }
                        showToast(res.error || "Không thể kết nối Atria AI!", "error");
                    }
                })
                .catch(() => {
                    btnPingAtria.disabled = false;
                    btnPingAtria.innerHTML = `<i class="fa-solid fa-wifi"></i> Ping AI`;
                    showToast("Lỗi kết nối máy chủ khi ping AI!", "error");
                });
        });
    }

    if (btnSave) {
        btnSave.addEventListener("click", () => {
            const payload = {
                merge_mp4: document.getElementById("cfg-merge-mp4").checked,
                embed_thumbnail: document.getElementById("cfg-embed-thumb").checked,
                auto_open_folder: document.getElementById("cfg-auto-open").checked,
                concurrent_fragments: parseInt(document.getElementById("cfg-threads").value, 10) || 16,
                atria_api_key: document.getElementById("cfg-atria-key")?.value?.trim() || "",
            };

            fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ settings: payload }),
            })
                .then((r) => r.json())
                .then((res) => {
                    if (res.ok) {
                        showToast("Đã lưu tất cả cài đặt hệ thống v3.0.0 ULTRA!", "success");
                    }
                });
        });
    }

    if (btnUpdateFfmpeg) {
        btnUpdateFfmpeg.addEventListener("click", () => {
            btnUpdateFfmpeg.disabled = true;
            btnUpdateFfmpeg.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang tải FFmpeg...`;
            fetch("/api/system/ffmpeg/download", { method: "POST" })
                .then((r) => r.json())
                .then(() => {
                    showToast("Đang tải FFmpeg Essentials vào thư mục bin/...", "info");
                });
        });
    }

    if (btnUpdateYtdlp) {
        btnUpdateYtdlp.addEventListener("click", () => {
            btnUpdateYtdlp.disabled = true;
            btnUpdateYtdlp.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang cập nhật...`;
            fetch("/api/system/ytdlp/update", { method: "POST" })
                .then((r) => r.json())
                .then((res) => {
                    btnUpdateYtdlp.disabled = false;
                    btnUpdateYtdlp.innerHTML = `<i class="fa-solid fa-rotate"></i> Cập nhật Lõi`;
                    showToast(res.message || "Đã cập nhật engine yt-dlp!", res.ok ? "success" : "error");
                });
        });
    }
}

// ─────────────────────────────────────────────────────────── 14. WEBSOCKET REAL-TIME SYNC
function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
        AppState.ws = new WebSocket(wsUrl);

        AppState.ws.onopen = () => {
            AppState.wsConnected = true;
            const wsPill = document.getElementById("pill-ws");
            if (wsPill) {
                wsPill.querySelector(".pill-dot").className = "pill-dot success";
                wsPill.querySelector(".pill-text").textContent = "Online";
            }
        };

        AppState.ws.onmessage = (evt) => {
            try {
                const msg = JSON.parse(evt.data);
                handleWebSocketMessage(msg);
            } catch {}
        };

        AppState.ws.onclose = () => {
            AppState.wsConnected = false;
            const wsPill = document.getElementById("pill-ws");
            if (wsPill) {
                wsPill.querySelector(".pill-dot").className = "pill-dot warning";
                wsPill.querySelector(".pill-text").textContent = "Reconnecting";
            }
            setTimeout(connectWebSocket, 3000);
        };
    } catch {
        setTimeout(connectWebSocket, 5000);
    }
}

function handleWebSocketMessage(msg) {
    if (msg.type === "init") {
        updateSystemPills(msg.system);
    } else if (msg.type === "task_progress") {
        renderTasks();
    } else if (msg.type === "task_completed") {
        renderTasks();
        loadVaultFiles();
        if (msg.ok) {
            showToast(`Tải thành công: ${msg.result?.title || "Video"}!`, "success");
        } else {
            showToast(`Tải thất bại: ${msg.result?.error || "Lỗi"}`, "error");
        }
    } else if (msg.type === "ffmpeg_download_completed") {
        const btnUpdateFfmpeg = document.getElementById("btn-update-ffmpeg");
        if (btnUpdateFfmpeg) {
            btnUpdateFfmpeg.disabled = false;
            btnUpdateFfmpeg.innerHTML = `<i class="fa-solid fa-download"></i> Tải FFmpeg vào bin/`;
        }
        showToast(msg.message, msg.ok ? "success" : "error");
        loadSystemStatus();
    } else if (msg.type === "tunnel_status") {
        const btn = document.getElementById("btn-toggle-tunnel");
        if (btn && msg.active) {
            btn.classList.add("active");
            btn.innerHTML = `<i class="fa-solid fa-stop"></i> Tắt Link Công Khai`;
            document.getElementById("tunnel-status-label").textContent = "Đang phát trực tuyến";
            document.getElementById("public-url-display").textContent = msg.public_url;
            document.getElementById("public-url-row").style.display = "flex";
        }
    }
}

// ─────────────────────────────────────────────────────────── 15. INITIAL DATA LOADERS
function loadInitialData() {
    loadSystemStatus();
    loadVaultFiles();
    renderTasks();
}

function loadSystemStatus() {
    fetch("/api/system/status")
        .then((r) => r.json())
        .then((res) => {
            if (res.ok) updateSystemPills(res.data);
        });
}

function updateSystemPills(sys) {
    if (!sys) return;
    const ffmpegPill = document.getElementById("pill-ffmpeg");
    const settingFfmpeg = document.getElementById("setting-ffmpeg-path");
    const isFfmpegOk = Boolean(sys.ffmpeg_ok || sys.ffmpeg_ready || (sys.ffmpeg_status && sys.ffmpeg_status !== "Chưa cài đặt"));

    if (ffmpegPill) {
        const dot = ffmpegPill.querySelector(".pill-dot");
        const txt = ffmpegPill.querySelector(".pill-text");
        if (isFfmpegOk) {
            dot.className = "pill-dot success";
            txt.textContent = "FFmpeg OK";
            ffmpegPill.title = `FFmpeg đã sẵn sàng (${sys.ffmpeg_version || "Master Build"})`;
        } else {
            dot.className = "pill-dot warning";
            txt.textContent = "Thiếu FFmpeg";
            ffmpegPill.title = "Chưa có FFmpeg - Bấm vào Cài đặt để tải";
        }
    }

    if (settingFfmpeg) {
        if (isFfmpegOk) {
            settingFfmpeg.innerHTML = `<span style="color: var(--emerald); font-weight: 600;"><i class="fa-solid fa-circle-check"></i> Sẵn sàng: ${sys.ffmpeg_path || "bin/ffmpeg.exe"} (${sys.ffmpeg_version || "Master Build"})</span>`;
        } else {
            settingFfmpeg.textContent = "Chưa có FFmpeg (Nhấn tải bên dưới)";
        }
    }

    // Update LAN IP and QR
    const lanDisplay = document.getElementById("lan-ip-display");
    const qrBox = document.getElementById("lan-qr-code");
    const lanUrl = sys.web_url_lan || sys.lan_url;
    if (lanDisplay && lanUrl) {
        lanDisplay.textContent = lanUrl;
        if (qrBox && typeof QRCode !== "undefined" && !qrBox.children.length) {
            new QRCode(qrBox, {
                text: lanUrl,
                width: 140,
                height: 140,
                colorDark: "#08090d",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H,
            });
        }
    }
}

// ─────────────────────────────────────────────────────────── 16. TOAST NOTIFICATION UTILITY
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-item ${type}`;

    let icon = "fa-circle-info text-cyan";
    if (type === "success") icon = "fa-circle-check text-emerald";
    if (type === "error") icon = "fa-circle-exclamation text-red";

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(40px)";
        toast.style.transition = "all 0.3s";
        setTimeout(() => toast.remove(), 300);
    }, 3800);
}
