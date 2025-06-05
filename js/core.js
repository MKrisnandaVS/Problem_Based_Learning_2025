// js/core.js

// --- KONFIGURASI DAN STATE GLOBAL ---
const API_BASE_URL = "http://localhost:5001";
const USD_TO_IDR = 1; // Example rate
const pageTitles = {
  home: "Home Dashboard",
  clustering: "Stock Clustering",
  forecasting: "Stock Forecasting",
  screening: "Stock Screening",
};

// --- FUNGSI UTILITAS (DI-EXPORT) ---
export const config = { API_BASE_URL, USD_TO_IDR };

export function showLoading(show) {
  const loadingElement = document.getElementById("loading");
  if (loadingElement) {
    // Tambahkan pengecekan null
    loadingElement.classList.toggle("active", show);
  } else {
    console.warn(
      "Loading element not found. Cannot show/hide loading spinner."
    );
  }
}

export function formatPriceIndonesian(value) {
  if (value === null || value === undefined || isNaN(value)) return "N/A";
  // **PENTING**: Pastikan data OHLC Anda dari API memang perlu dibagi 10000.
  // Jika API mengembalikan harga sebenarnya (misal 8701.875), HAPUS baris ini.
  const adjustedValue = value / 1;
  return adjustedValue.toLocaleString("id-ID", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
}

export function formatVolume(value) {
  if (value === null || value === undefined || isNaN(value)) return "N/A";
  if (value >= 1.0e9) return (value / 1.0e9).toFixed(1) + "B";
  if (value >= 1.0e6) return (value / 1.0e6).toFixed(1) + "M";
  if (value >= 1.0e3) return (value / 1.0e3).toFixed(1) + "K";
  return value.toLocaleString();
}

export function formatPercentage(value) {
  if (value === null || value === undefined || isNaN(value)) return "N/A";
  return (value * 100).toFixed(2) + "%";
}

export function formatValue(value, isCurrency = false) {
  if (value === null || value === undefined || isNaN(value)) return "N/A";
  if (isCurrency) {
    const idrValue = value * USD_TO_IDR;
    if (Math.abs(idrValue) >= 1.0e12)
      return "Rp " + (idrValue / 1.0e12).toFixed(2) + "T";
    if (Math.abs(idrValue) >= 1.0e9)
      return "Rp " + (idrValue / 1.0e9).toFixed(2) + "B";
    if (Math.abs(idrValue) >= 1.0e6)
      return "Rp " + (idrValue / 1.0e6).toFixed(2) + "M";
    return "Rp " + idrValue.toLocaleString("id-ID");
  }
  return typeof value.toFixed === "function" ? value.toFixed(2) : value;
}

// --- FUNGSI INTI APLIKASI ---

async function checkApiConnection() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const statusEl = document.getElementById("api-status");
    if (response.ok) {
      if (statusEl) statusEl.innerHTML = "🟢 Connected";
    } else {
      throw new Error("API not responding");
    }
  } catch (error) {
    const statusEl = document.getElementById("api-status");
    if (statusEl) statusEl.innerHTML = "🔴 Disconnected";
    const container = document.getElementById("content-container");
    if (container) {
      container.innerHTML = `<div class="error-message">❌ Cannot connect to backend API. Please ensure the backend server is running.</div>`;
    }
    console.error("API connection error:", error);
  }
}

async function showSection(section) {
  showLoading(true);
  document
    .querySelectorAll(".sidebar-item")
    .forEach((item) => item.classList.remove("active"));
  const activeLink = document.querySelector(
    `[onclick*="showSection('${section}')"]`
  );
  if (activeLink) {
    activeLink.closest(".sidebar-item").classList.add("active");
  }
  document.getElementById("page-title").textContent =
    pageTitles[section] || "Dashboard";

  try {
    const response = await fetch(`./sections/${section}.html`);
    if (!response.ok)
      throw new Error(`Section HTML not found: ${section}.html`);
    const htmlContent = await response.text();
    document.getElementById("content-container").innerHTML = htmlContent;

    // Dynamically import the section's JavaScript module
    const module = await import(`./${section}.js`);
    if (module.init) {
      // Call the init function of the loaded module
      module.init();
    }
  } catch (error) {
    console.error(`Error loading section '${section}':`, error);
    document.getElementById(
      "content-container"
    ).innerHTML = `<div class="error-message">❌ Failed to load section: ${section}. Please check the console for details.</div>`;
  } finally {
    showLoading(false);
  }
}

window.showSection = showSection;

// --- INISIALISASI SAAT HALAMAN DIMUAT ---
document.addEventListener("DOMContentLoaded", async () => {
  await checkApiConnection();

  // Muat seksi 'home' sebagai default jika API terhubung
  if (document.getElementById("api-status").innerHTML.includes("Connected")) {
    await showSection("home");
  }

  // --- HAPUS Event Listener untuk Search Bar dan Refresh Button di SINI ---
  // Logika pencarian sekarang hanya ada di home.js setelah home.html dimuat.
  // Ini adalah penyebab utama request berulang.
  // const searchInput = document.getElementById("ticker-search");
  // const searchButton = document.getElementById("refresh-button");
  // if (searchInput && searchButton) {
  //   searchButton.addEventListener("click", handleTickerSearch);
  //   searchInput.addEventListener("keypress", (event) => {
  //     if (event.key === "Enter") {
  //       event.preventDefault();
  //       handleTickerSearch();
  //     }
  //   });
  // }
});
