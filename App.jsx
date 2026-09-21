import { createSignal, Show, For } from "solid-js";

const i18n = {
  id: {
    subTitle: "Tempel link YouTube lu di bawah ini.",
    checkBtn: "Cek Link & Lanjut",
    emptyLinkErr: "Link gak boleh kosong bro!",
    checking: "Mengecek info...",
    optionsTitle: "Opsi Unduhan",
    mediaFormat: "Format Media",
    videoQuality: "Kualitas Video",
    audioQuality: "Kualitas Audio",
    estimation: "Estimasi Ukuran:",
    cancel: "Kembali",
    startDl: "Mulai Download",
    downloadingTitle: "Mengunduh...",
    successTitle: "Berhasil!",
    successDesc: "File lu udah tersimpan di folder Downloads.",
    dlAnother: "Download Video Lain",
    checkUpdateBtn: "Cek Pembaruan",
    checkingUpdate: "Mengecek GitHub...",
    noUpdateMsg: "Aplikasi kamu sudah versi terbaru!",
    updateAvailableMsg: "Versi {ver} tersedia!",
    downloadUpdateBtn: "Update Sekarang",
    downloadingUpdate: "Mengunduh update...",
    updateError: "Gagal mengecek pembaruan.",
    backendErr: "Backend Python belum nyala bro!"
  },
  en: {
    subTitle: "Paste your YouTube link below.",
    checkBtn: "Check Link & Continue",
    emptyLinkErr: "Link cannot be empty!",
    checking: "Checking info...",
    optionsTitle: "Download Options",
    mediaFormat: "Media Format",
    videoQuality: "Video Quality",
    audioQuality: "Audio Quality",
    estimation: "Estimated Size:",
    cancel: "Back",
    startDl: "Start Download",
    downloadingTitle: "Downloading...",
    successTitle: "Success!",
    successDesc: "Your file has been saved to Downloads folder.",
    dlAnother: "Download Another Video",
    checkUpdateBtn: "Check Updates",
    checkingUpdate: "Checking GitHub...",
    noUpdateMsg: "App is up to date!",
    updateAvailableMsg: "Version {ver} available!",
    downloadUpdateBtn: "Update Now",
    downloadingUpdate: "Downloading update...",
    updateError: "Failed to check updates.",
    backendErr: "Python Backend is offline!"
  }
};

function App() {
  const [lang, setLang] = createSignal("id");
  const [step, setStep] = createSignal(1);
  const [url, setUrl] = createSignal("");
  const [videoInfo, setVideoInfo] = createSignal(null);
  
  const [format, setFormat] = createSignal("Video");
  const [resolution, setResolution] = createSignal("1080p");
  
  const [progress, setProgress] = createSignal("0%");
  const [speed, setSpeed] = createSignal("Mempersiapkan...");
  const [isError, setIsError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false); // State untuk animasi loading

  const [updateStatus, setUpdateStatus] = createSignal("");
  const [updateData, setUpdateData] = createSignal(null);

  const t = () => i18n[lang()];
  const API_URL = "http://127.0.0.1:8000";

  const checkLink = async () => {
    if (!url()) return setIsError(t().emptyLinkErr);
    setIsError("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/info?url=${encodeURIComponent(url())}`);
      const data = await res.json();

      if (data.status === "success") {
        setVideoInfo(data);
        setResolution(data.available_resolutions[0]);
        setStep(2);
      } else {
        setIsError(data.message || "Gagal baca link.");
      }
    } catch (err) {
      setIsError(t().backendErr);
    } finally {
      setIsLoading(false);
    }
  };

  const checkAppUpdate = async () => {
    setUpdateStatus(t().checkingUpdate);
    try {
      const res = await fetch(`${API_URL}/api/check-update`);
      const data = await res.json();

      if (data.update_available) {
        setUpdateData(data);
        setUpdateStatus(t().updateAvailableMsg.replace("{ver}", data.latest_version));
      } else {
        setUpdateStatus(t().noUpdateMsg);
      }
    } catch (err) {
      setUpdateStatus(t().updateError);
    }
  };

  const triggerUpdateDownload = async () => {
    if (!updateData()) return;
    setUpdateStatus(t().downloadingUpdate);
    try {
      await fetch(`${API_URL}/api/do-update?url=${encodeURIComponent(updateData().download_url)}&version=${updateData().latest_version}`);
    } catch (err) {
      setUpdateStatus(t().updateError);
    }
  };

  const startDownload = () => {
    setStep(3);
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/download");

    ws.onopen = () => {
      ws.send(JSON.stringify({ url: url(), type: format(), resolution: resolution(), fps: "60 FPS" }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.status === "downloading") {
        setProgress(data.progress);
        setSpeed(`Kecepatan: ${data.speed}`);
      } else if (data.status === "merging") {
        setSpeed(data.message);
      } else if (data.status === "completed") {
        ws.close();
        setStep(4);
      } else if (data.status === "error") {
        ws.close();
        setIsError("Error: " + data.message);
        setStep(1);
      }
    };
  };

  return (
    // FULL FRAME LAYOUT: Hapus margin/padding berlebih, penuhi layar
    <div class="min-h-screen bg-[#0F172A] text-gray-100 flex flex-col font-sans">
      
      {/* HEADER BAR */}
      <div class="flex justify-between items-center px-6 py-4 bg-[#1E293B] border-b border-gray-800 shadow-sm">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
            YT
          </div>
          <h1 class="text-sm font-bold tracking-wider text-gray-200 uppercase">Downloader</h1>
        </div>
        <button 
          onClick={() => setLang(lang() === "id" ? "en" : "id")} 
          class="text-xs bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg font-bold border border-gray-700 transition flex items-center gap-2"
        >
          🌐 {lang().toUpperCase()}
        </button>
      </div>

      {/* MAIN CONTENT AREA */}
      <div class="flex-1 flex flex-col px-8 py-8 w-full max-w-2xl mx-auto">
        <Show when={isError()}>
          <div class="mb-6 p-4 bg-red-500/10 text-red-400 rounded-xl text-sm border border-red-500/20 flex items-center gap-3">
            ⚠️ {isError()}
          </div>
        </Show>

        {/* STEP 1 */}
        <Show when={step() === 1}>
          <div class="flex-1 flex flex-col justify-center">
            <h2 class="text-3xl font-bold mb-2">Mulai Unduh</h2>
            <p class="text-gray-400 mb-8">{t().subTitle}</p>
            
            <input 
              type="text" 
              placeholder="https://youtube.com/watch?v=..." 
              value={url()} 
              onInput={(e) => setUrl(e.target.value)} 
              class="w-full px-5 py-4 bg-[#1E293B] rounded-xl mb-6 border border-gray-700 outline-none focus:border-blue-500 transition shadow-inner"
            />
            
            <button 
              onClick={checkLink} 
              disabled={isLoading()}
              class="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed py-4 rounded-xl font-bold transition flex justify-center items-center gap-3 shadow-lg shadow-blue-900/50 text-lg"
            >
              <Show when={isLoading()}>
                {/* ANIMASI SPINNER */}
                <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </Show>
              {isLoading() ? t().checking : t().checkBtn}
            </button>
          </div>

          {/* FOOTER: Check Update */}
          <div class="mt-auto border-t border-gray-800 pt-6 flex items-center justify-between">
            <button onClick={checkAppUpdate} class="text-sm text-gray-400 hover:text-white transition">{t().checkUpdateBtn}</button>
            <Show when={updateStatus()}>
              <span class="text-sm text-blue-400 font-semibold">{updateStatus()}</span>
            </Show>
            <Show when={updateData() && updateData().update_available}>
              <button onClick={triggerUpdateDownload} class="text-sm bg-[#1E293B] border border-blue-500/50 hover:bg-blue-600 px-4 py-2 rounded-lg font-bold text-white transition">{t().downloadUpdateBtn}</button>
            </Show>
          </div>
        </Show>

        {/* STEP 2 */}
        <Show when={step() === 2 && videoInfo()}>
          <h2 class="text-2xl font-bold mb-6">{t().optionsTitle}</h2>
          
          <div class="mb-8 bg-[#1E293B] p-5 rounded-xl border border-gray-700 flex items-center gap-4">
            <div class="w-12 h-12 bg-gray-800 rounded-lg flex items-center justify-center text-xl">🎬</div>
            <div class="overflow-hidden">
              <p class="text-base font-semibold text-gray-100 truncate mb-1">{videoInfo().title}</p>
              <p class="text-sm text-gray-400">{videoInfo().channel} • ⏱️ {videoInfo().duration}</p>
            </div>
          </div>
          
          <div class="space-y-6 mb-8">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="text-sm font-semibold text-gray-400 block mb-2">{t().mediaFormat}</label>
                <select value={format()} onChange={(e) => {setFormat(e.target.value); setResolution(e.target.value === "Video" ? videoInfo().available_resolutions[0] : "192 kbps");}} class="w-full px-4 py-3 bg-[#1E293B] rounded-xl border border-gray-700 outline-none focus:border-blue-500">
                  <option value="Video">Video (MP4)</option>
                  <option value="Audio (MP3)">Audio Only (MP3)</option>
                </select>
              </div>
              
              <Show when={format() === "Video"}>
                <div>
                  <label class="text-sm font-semibold text-gray-400 block mb-2">{t().videoQuality}</label>
                  <select value={resolution()} onChange={(e) => setResolution(e.target.value)} class="w-full px-4 py-3 bg-[#1E293B] rounded-xl border border-gray-700 outline-none focus:border-blue-500">
                    <For each={videoInfo().available_resolutions}>{(res) => <option value={res}>{res}</option>}</For>
                  </select>
                </div>
              </Show>
              <Show when={format() === "Audio (MP3)"}>
                <div>
                  <label class="text-sm font-semibold text-gray-400 block mb-2">{t().audioQuality}</label>
                  <select value={resolution()} onChange={(e) => setResolution(e.target.value)} class="w-full px-4 py-3 bg-[#1E293B] rounded-xl border border-gray-700 outline-none focus:border-blue-500">
                    <option value="320 kbps">320 kbps</option>
                    <option value="256 kbps">256 kbps</option>
                    <option value="192 kbps">192 kbps</option>
                    <option value="128 kbps">128 kbps</option>
                  </select>
                </div>
              </Show>
            </div>
          </div>
          
          <div class="mb-8 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl flex justify-between items-center">
             <span class="text-gray-400 text-sm font-medium">{t().estimation}</span>
             <span class="text-blue-400 font-bold text-lg">{format() === "Video" ? videoInfo().estimations.video[resolution()] : videoInfo().estimations.audio[resolution()]}</span>
          </div>

          <div class="flex gap-4 mt-auto">
            {/* Tombol dimodifikasi serasi dengan tema */}
            <button onClick={() => setStep(1)} class="w-1/3 bg-[#1E293B] hover:bg-gray-700 border border-gray-700 py-4 rounded-xl font-bold transition text-gray-300">{t().cancel}</button>
            <button onClick={startDownload} class="w-2/3 bg-blue-600 hover:bg-blue-500 py-4 rounded-xl font-bold transition shadow-lg shadow-blue-900/50">{t().startDl}</button>
          </div>
        </Show>

        {/* STEP 3 */}
        <Show when={step() === 3}>
          <div class="flex-1 flex flex-col justify-center items-center text-center">
            <div class="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-6"></div>
            <h2 class="text-2xl font-bold mb-2">{t().downloadingTitle}</h2>
            <p class="text-gray-400 mb-8">{speed()}</p>
            <div class="w-full bg-[#1E293B] h-4 rounded-full overflow-hidden mb-4 border border-gray-800">
              <div class="bg-blue-500 h-full transition-all duration-300 ease-out" style={{ width: progress().replace('%', '') + '%' }}></div>
            </div>
            <p class="text-3xl font-bold text-blue-400">{progress()}</p>
          </div>
        </Show>

        {/* STEP 4 */}
        <Show when={step() === 4}>
          <div class="flex-1 flex flex-col justify-center items-center text-center">
            <div class="w-20 h-20 bg-green-500/10 text-green-400 rounded-full flex items-center justify-center text-4xl mb-6 border border-green-500/20">
              ✓
            </div>
            <h2 class="text-3xl font-bold mb-3">{t().successTitle}</h2>
            <p class="text-gray-400 mb-10">{t().successDesc}</p>
            <button onClick={() => {setUrl(""); setStep(1);}} class="w-full max-w-sm bg-[#1E293B] border border-gray-700 hover:bg-gray-800 py-4 rounded-xl font-bold transition">
              {t().dlAnother}
            </button>
          </div>
        </Show>

      </div>
    </div>
  );
}

export default App;