// js/home.js

// Impor fungsi dan konfigurasi yang dibutuhkan dari core.js
import {
  config,
  showLoading,
  formatPriceIndonesian,
  formatValue,
  formatVolume,
  formatPercentage,
} from "./core.js";

// --- STATE DAN VARIABEL KHUSUS HALAMAN HOME ---
let charts = {};
let currentPage = 1;
let rowsPerPage = 25;
let totalRows = 0;
let allPriceData = [];
let currentTicker = null; // Inisialisasi null, penting!
let isLoadingMore = false;
const INITIAL_PRICE_DATA_LIMIT = 100; // Batas awal data harga yang diambil untuk tabel/chart

// --- FUNGSI-FUNGSI LOGIKA HALAMAN HOME ---

// Fungsi untuk mereset UI ke kondisi awal (sebelum ada data ticker)
function resetHomeUI() {
  document.getElementById("market-cap-display").textContent = "N/A";
  document.getElementById("current-price-display").textContent = "N/A";
  document.getElementById("pe-ratio-display").textContent = "N/A";
  document.getElementById("volume-display").textContent = "N/A";

  // Set default texts for company info, financial, valuation, etc.
  document.getElementById("company-info").innerHTML = `<p class="text-gray-500">Enter a ticker symbol to view company information</p>`;
  document.getElementById("financial-metrics").innerHTML = `<p class="text-gray-500">Financial data will appear here</p>`;
  document.getElementById("valuation-metrics").innerHTML = `<p class="text-gray-500">Valuation metrics will appear here</p>`;
  document.getElementById("growth-metrics").innerHTML = `<p class="text-gray-500">Growth data will appear here</p>`;
  document.getElementById("profitability-liquidity").innerHTML = `<p class="text-gray-500">Profitability & liquidity data will appear here</p>`;


  // Hancurkan chart jika ada data sebelumnya
  if (charts.priceChart) charts.priceChart.destroy();
  if (charts.volumeChart) charts.volumeChart.destroy();
  charts = {}; // Reset chart references

  allPriceData = []; // Kosongkan data harga
  currentPage = 1; // Reset halaman
  totalRows = 0; // Reset total baris
  updatePriceTable(); // Ini akan menampilkan "No price data available" di tabel
  updatePaginationInfo(); // Reset info pagination

  const loadMoreBtn = document.getElementById("load-more-btn");
  if(loadMoreBtn) loadMoreBtn.style.display = "none"; // Sembunyikan tombol load more
}

/**
 * Fungsi utama untuk memuat semua data dashboard berdasarkan ticker.
 * Ini adalah satu-satunya fungsi yang memicu pengambilan data lengkap untuk dashboard.
 * @param {boolean} forceReload - Jika true, akan memuat ulang data meskipun ticker sama.
 */
async function loadData(forceReload = false) {
  const tickerInput = document.getElementById("ticker-search");
  if (!tickerInput) {
    console.error("Ticker search input not found.");
    return;
  }

  const newTicker = tickerInput.value.trim().toUpperCase();

  // Jika tidak ada ticker yang dimasukkan, reset UI dan keluar
  if (!newTicker) {
    console.warn("No ticker provided. Skipping data load.");
    resetHomeUI();
    showLoading(false);
    const statusContainer = document.getElementById("connection-status");
    if (statusContainer) {
      statusContainer.innerHTML = `<div class="info-message text-blue-600 p-4 rounded-lg bg-blue-50">Please enter a stock ticker in the search bar and press Enter or the 'Enter' button.</div>`;
    }
    return;
  }

  // Poin kunci untuk mencegah request berulang:
  // Jika ticker sama, TIDAK forceReload, dan data sudah ada, JANGAN load ulang.
  if (!forceReload && currentTicker === newTicker && allPriceData.length > 0) {
    console.log(`Data for ${newTicker} already loaded. Skipping re-load.`);
    showLoading(false); // Pastikan loading dinonaktifkan
    return;
  }

  // Jika ticker berubah atau forceReload, Lanjutkan untuk memuat ulang data
  currentTicker = newTicker; // Update ticker yang sedang aktif
  showLoading(true);

  // Reset state untuk ticker baru atau forceReload
  currentPage = 1;
  allPriceData = []; // <--- Ini penting untuk membersihkan data lama sebelum memuat yang baru
  totalRows = 0;

  const statusContainer = document.getElementById("connection-status");
  if (statusContainer) statusContainer.innerHTML = ""; // Clear previous messages

  try {
    // 1. Fetch comprehensive company info (company info, finance, valuation, etc.)
    const companyResponse = await fetch(
      `${config.API_BASE_URL}/company/${currentTicker}`
    );
    if (!companyResponse.ok) {
      if (companyResponse.status === 404) {
        throw new Error(`Ticker '${currentTicker}' not found or no detailed company data available.`);
      }
      throw new Error(`Error fetching company data for ${currentTicker}: ${companyResponse.status} - ${await companyResponse.text()}`);
    }
    const companyData = await companyResponse.json();

    // 2. Load initial price data (100 entries) for the table and charts
    // This will populate `allPriceData`
    await loadPriceData(currentTicker, true); // `true` for initial load, resets `allPriceData`

    // Update all UI elements with the fetched data
    updateQuickStats(companyData, allPriceData); // Pass allPriceData to get latest price/volume
    updateCompanyInfo(companyData.info);
    updateFinancialMetrics(companyData.finance);
    updateValuationMetrics(companyData.valuation);
    updateGrowthMetrics(companyData.growth);
    updateProfitabilityLiquidity(
      companyData.profitabilities,
      companyData.liquidity
    );

    // Update charts and table
    if (allPriceData.length > 0) {
      // For charts, we need data sorted oldest to newest.
      // And typically, charts show a limited number of recent data points (e.g., last 30).
      const chartData = [...allPriceData].sort(
        (a, b) => new Date(a.datetime) - new Date(b.datetime)
      ).slice(-30); // Take the last 30 data points (most recent)
      updatePriceChart(chartData);
      updateVolumeChart(chartData);
    } else {
      // Destroy charts if no price data is available for the ticker
      if (charts.priceChart) charts.priceChart.destroy();
      if (charts.volumeChart) charts.volumeChart.destroy();
      charts = {}; // Reset chart references
    }
    updatePriceTable(); // Update the price table with the loaded data
  } catch (error) {
    console.error("Error loading data:", error);
    resetHomeUI(); // Reset UI on ANY error to clear old data and show error message
    if (statusContainer) {
      statusContainer.innerHTML = `<div class="error-message">❌ ${error.message}</div>`;
    }
  } finally {
    showLoading(false);
  }
}

/**
 * Mengambil data harga saham dari API. Digunakan untuk load awal dan "Load More".
 * @param {string} ticker - Kode saham.
 * @param {boolean} isInitial - Jika true, akan mereset allPriceData. Jika false, akan menambahkannya.
 */
async function loadPriceData(ticker, isInitial = false) {
  try {
    const limit = isInitial ? INITIAL_PRICE_DATA_LIMIT : rowsPerPage; // Fetch more data by 'rowsPerPage' chunks
    const offset = isInitial ? 0 : allPriceData.length; // Start offset from current data length

    console.log(`Fetching price data for ${ticker} with limit=${limit}, offset=${offset}, initial=${isInitial}`);

    const priceResponse = await fetch(
      `${config.API_BASE_URL}/stock-prices/${ticker}?limit=${limit}&offset=${offset}&timeframe=1d`
    );
    if (!priceResponse.ok) {
      const errorText = await priceResponse.text();
      throw new Error(`Error fetching price data: ${priceResponse.status} - ${errorText}`);
    }
    const priceData = await priceResponse.json();

    if (isInitial) {
      allPriceData = priceData; // Overwrite for initial load
    } else {
      allPriceData = [...allPriceData, ...priceData]; // Append for "Load More"
    }
    totalRows = allPriceData.length;

    const loadMoreBtn = document.getElementById("load-more-btn");
    if (loadMoreBtn) {
      // Show "Load More" button only if we received 'limit' number of items,
      // implying there might be more data available beyond the current fetch.
      loadMoreBtn.style.display = priceData.length === limit ? "block" : "none";
    }
    return priceData;
  } catch (error) {
    console.error("Error loading price data:", error);
    throw error; // Re-throw to be caught by loadData()
  }
}

/**
 * Fungsi untuk memuat data harga tambahan saat tombol "Load More" ditekan.
 */
async function loadMorePriceData() {
    if (isLoadingMore || !currentTicker) return; // Prevent multiple clicks or if no ticker is selected
    isLoadingMore = true;
    showLoading(true);

    try {
        const moreData = await loadPriceData(currentTicker, false); // `false` for appending
        
        // If new data was loaded, update the table and pagination info
        if (moreData.length > 0) {
            updatePriceTable();
            // Note: Charts typically don't update with "Load More" data as they show recent trends.
            // If you want charts to show more data, you'd need to re-render them with a larger dataset.
        } else {
            // If no more data was returned, hide the load more button
            const loadMoreBtn = document.getElementById("load-more-btn");
            if (loadMoreBtn) loadMoreBtn.style.display = "none";
        }
    } catch (error) {
        console.error("Error loading more price data:", error);
        const statusContainer = document.getElementById("connection-status");
        if (statusContainer) {
            statusContainer.innerHTML = `<div class="error-message">❌ Failed to load more data: ${error.message}</div>`;
        }
    } finally {
        isLoadingMore = false;
        showLoading(false);
    }
}


function updatePriceTable() {
  const tableBody = document.getElementById("price-table-body");
  if (!tableBody || !allPriceData || allPriceData.length === 0) {
    if (tableBody)
      tableBody.innerHTML = `<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">No price data available for this ticker.</td></tr>`;
    updatePaginationInfo();
    return;
  }

  const startIndex = (currentPage - 1) * rowsPerPage;
  const pageData = allPriceData.slice(startIndex, startIndex + rowsPerPage);
  let html = "";

  pageData.forEach((price, index) => {
    // To calculate change, we need the *previous day's* closing price relative to `price.close`.
    // Since `allPriceData` is sorted DESC by datetime (newest first),
    // the "previous" data point is found by looking at the next element in `allPriceData`.
    const prevPriceIndexInAllData = allPriceData.indexOf(price) + 1;
    const prevPrice =
      prevPriceIndexInAllData < allPriceData.length ? allPriceData[prevPriceIndexInAllData] : null;

    const change = prevPrice
      ? ((price.close - prevPrice.close) / prevPrice.close) * 100
      : 0; // If no previous price, change is 0
    const date = new Date(price.datetime).toLocaleDateString("en-GB");

    html += `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${date}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">Rp ${formatPriceIndonesian(
                  price.open * config.USD_TO_IDR
                )}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600">Rp ${formatPriceIndonesian(
                  price.high * config.USD_TO_IDR
                )}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-red-600">Rp ${formatPriceIndonesian(
                  price.low * config.USD_TO_IDR
                )}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold">Rp ${formatPriceIndonesian(
                  price.close * config.USD_TO_IDR
                )}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">${formatVolume(
                  price.volume
                )}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span class="px-2 py-1 rounded-full text-xs font-medium ${
                      change >= 0
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }">
                        ${change >= 0 ? "+" : ""}${change.toFixed(2)}%
                    </span>
                </td>
            </tr>
        `;
  });
  tableBody.innerHTML = html;
  updatePaginationInfo();
}

function updateQuickStats(companyData, priceData) {
  document.getElementById("market-cap-display").textContent = formatValue(
    companyData.finance?.marketcap,
    true
  );
  // Get the latest price (first element as API sorts DESC)
  const currentPrice = priceData.length > 0 ? priceData[0].close : null;
  document.getElementById(
    "current-price-display"
  ).textContent = currentPrice !== null ? `Rp ${formatPriceIndonesian(
    currentPrice * config.USD_TO_IDR
  )}` : "N/A"; // Handle null case

  document.getElementById("pe-ratio-display").textContent = companyData
    .valuation?.trailingpe
    ? companyData.valuation.trailingpe.toFixed(1)
    : "N/A";

  const volume = priceData.length > 0 ? priceData[0].volume : null;
  document.getElementById("volume-display").textContent = volume !== null ? formatVolume(volume) : "N/A";
}

function updateCompanyInfo(info) {
  const container = document.getElementById("company-info");
  if (!info) {
    container.innerHTML = `<p class="text-red-500">No company info available</p>`;
    return;
  }
  container.innerHTML = `
        <div class="space-y-2">
            <h4 class="font-semibold">${info.longname || "N/A"}</h4>
            <p class="text-sm text-gray-600">${info.sector || "N/A"} | ${
    info.industry || "N/A" // Assuming 'industry' might also be available
  }</p>
            <p class="text-sm">${
              info.longbusinesssummary // Perbaikan typo 'longbussinesssumarry' menjadi 'longbusinesssummary'
                ? info.longbusinesssummary.substring(0, 200) + "..."
                : "No summary available"
            }</p>
            <div class="mt-2 text-sm"><strong>Website:</strong> <a href="${
              info.website
            }" target="_blank" class="text-blue-600">${
    info.website || "N/A"
  }</a></div>
        </div>`;
}

function updateFinancialMetrics(finance) {
  const container = document.getElementById("financial-metrics");
  if (!finance) {
    container.innerHTML = `<p class="text-red-500">No financial data available</p>`;
    return;
  }
  container.innerHTML = `<div class="space-y-3 text-sm">
    <div class="flex justify-between"><span>Market Cap:</span><span class="font-semibold">${formatValue(
      finance.marketcap,
      true
    )}</span></div>
    <div class="flex justify-between"><span>Total Revenue:</span><span class="font-semibold">${formatValue(
      finance.totalrevenue,
      true
    )}</span></div>
    <div class="flex justify-between"><span>Net Income:</span><span class="font-semibold">${formatValue(
      finance.netincometocommon,
      true
    )}</span></div>
    <div class="flex justify-between"><span>Profit Margin:</span><span class="font-semibold">${formatPercentage(
      finance.profitmargins
    )}</span></div>
    </div>`;
}
function updateValuationMetrics(valuation) {
  const container = document.getElementById("valuation-metrics");
  if (!valuation) {
    container.innerHTML = `<p class="text-red-500">No valuation data available</p>`;
    return;
  }
  container.innerHTML = `<div class="space-y-3 text-sm">
    <div class="flex justify-between"><span>P/E Ratio:</span><span class="font-semibold">${formatValue(
      valuation.trailingpe
    )}</span></div>
    <div class="flex justify-between"><span>Forward P/E:</span><span class="font-semibold">${formatValue(
      valuation.forwardpe
    )}</span></div>
    <div class="flex justify-between"><span>Price/Book:</span><span class="font-semibold">${formatValue(
      valuation.pricetobook
    )}</span></div>
    </div>`;
}
function updateGrowthMetrics(growth) {
  const container = document.getElementById("growth-metrics");
  if (!growth) {
    container.innerHTML = `<p class="text-red-500">No growth data available</p>`;
    return;
  }
  container.innerHTML = `<div class="space-y-3 text-sm">
        <div class="flex justify-between"><span>Revenue Growth:</span><span class="font-semibold">${formatPercentage(
          growth.revenuegrowth
        )}</span></div>
        <div class="flex justify-between"><span>Earnings Growth:</span><span class="font-semibold">${formatPercentage(
          growth.earningsgrowth
        )}</span></div>
        <div class="flex justify-between"><span>Quarterly Earnings Growth:</span><span class="font-semibold">${formatPercentage(
          growth.earningsquarterlygrowth
        )}</span></div>
    </div>`;
}
function updateProfitabilityLiquidity(profitabilities, liquidity) {
  const container = document.getElementById("profitability-liquidity");
  if (!profitabilities && !liquidity) {
    container.innerHTML = `<p class="text-red-500">No profitability or liquidity data available</p>`;
    return;
  }
  container.innerHTML = `<div class="space-y-3 text-sm">
        <div class="flex justify-between"><span>Return on Equity:</span><span class="font-semibold">${formatPercentage(
          profitabilities?.returnonequity
        )}</span></div>
        <div class="flex justify-between"><span>Current Ratio:</span><span class="font-semibold">${formatValue(
          liquidity?.currentratio
        )}</span></div>
        <div class="flex justify-between"><span>Debt to Equity:</span><span class="font-semibold">${formatValue(
          liquidity?.debttoequity
        )}</span></div>
    </div>`;
}

// --- FUNGSI PAGINASI ---
function updatePaginationInfo() {
  const totalPages = Math.ceil(totalRows / rowsPerPage);
  document.getElementById("pagination-info").textContent = `Showing ${Math.min(
    (currentPage - 1) * rowsPerPage + 1,
    totalRows
  )} to ${Math.min(currentPage * rowsPerPage, totalRows)} of ${totalRows}`;
  document.getElementById("page-info").textContent = `Page ${currentPage} of ${
    totalPages || 1
  }`;
  document.getElementById("prev-btn").disabled = currentPage === 1;
  document.getElementById("next-btn").disabled =
    currentPage >= totalPages || totalPages === 0; // Adjusted condition for next button
}
function changeRowsPerPage() {
  rowsPerPage = parseInt(document.getElementById("rows-per-page").value, 10);
  currentPage = 1; // Reset to the first page when rows per page changes
  updatePriceTable();
}
function previousPage() {
  if (currentPage > 1) {
    currentPage--;
    updatePriceTable();
  }
}
function nextPage() {
  if (currentPage < Math.ceil(totalRows / rowsPerPage)) {
    currentPage++;
    updatePriceTable();
  }
}

// --- FUNGSI CHART (KRUSIAL) ---
function updatePriceChart(data) {
  const canvas = document.getElementById("price-chart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (charts.priceChart) charts.priceChart.destroy(); // Destroy existing chart

  // Data for charts should already be sorted oldest to newest and sliced (e.g., to 30 elements)
  charts.priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map((d) =>
        new Date(d.datetime).toLocaleDateString("en-GB")
      ),
      datasets: [
        {
          label: "Close Price (IDR)",
          data: data.map((d) => d.close * config.USD_TO_IDR),
          borderColor: "rgb(99, 102, 241)",
          backgroundColor: "rgba(99, 102, 241, 0.1)",
          tension: 0.4,
          fill: true,
          pointRadius: 1,
          pointHoverRadius: 5,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          ticks: { callback: (value) => "Rp " + formatPriceIndonesian(value) },
        },
      },
    },
  });
}

function updateVolumeChart(data) {
  const canvas = document.getElementById("volume-chart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (charts.volumeChart) charts.volumeChart.destroy(); // Destroy existing chart

  // Data for charts should already be sorted oldest to newest and sliced (e.g., to 30 elements)
  charts.volumeChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map((d) =>
        new Date(d.datetime).toLocaleDateString("en-GB")
      ),
      datasets: [
        {
          label: "Volume",
          data: data.map((d) => d.volume),
          backgroundColor: data.map((d, i) => {
            // Compare current close with previous close for volume bar color
            const prevClose = i > 0 ? data[i - 1].close : d.close; // If no previous data, assume no change
            return d.close >= prevClose
              ? "rgba(34, 197, 94, 0.6)" // Green if price increased or stayed same
              : "rgba(239, 68, 68, 0.6)"; // Red if price decreased
          }),
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { ticks: { callback: (value) => formatVolume(value) } } },
    },
  });
}

// --- FUNGSI INISIALISASI MODUL ---
export function init() {
  console.log("Home module initialized.");

  // Get references to elements (they should exist within home.html)
  const refreshButton = document.getElementById("refresh-button");
  const tickerSearchInput = document.getElementById("ticker-search");
  const rowsPerPageSelect = document.getElementById("rows-per-page");
  const prevBtn = document.getElementById("prev-btn");
  const nextBtn = document.getElementById("next-btn");
  const loadMoreBtn = document.getElementById("load-more-btn");

  // Attach event listeners for the home page specific elements
  if (refreshButton) {
    refreshButton.onclick = () => loadData(true); // Always force reload on button click
  } else {
    console.warn("refresh-button not found in home.html context.");
  }

  if (tickerSearchInput) {
    tickerSearchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault(); // Prevent form submission
        loadData(true); // Always force reload on Enter key press
      }
    });
  } else {
    console.warn("ticker-search input not found in home.html context.");
  }

  // Pagination event listeners
  if (rowsPerPageSelect) rowsPerPageSelect.onchange = changeRowsPerPage;
  if (prevBtn) prevBtn.onclick = previousPage;
  if (nextBtn) nextBtn.onclick = nextPage;
  if (loadMoreBtn) loadMoreBtn.onclick = loadMorePriceData;

  // Initial data load when home module is first initialized.
  // This will be called whenever `showSection('home')` is invoked.
  const initialTicker = tickerSearchInput ? tickerSearchInput.value.trim().toUpperCase() : '';
  if (initialTicker) {
    loadData(true); // Force reload to ensure fresh data if ticker is pre-filled
  } else {
    resetHomeUI(); // Clear UI if no ticker is present on initial load
    // Display an initial prompt for the user
    const statusContainer = document.getElementById("connection-status");
    if (statusContainer) {
      statusContainer.innerHTML = `<div class="info-message text-blue-600 p-4 rounded-lg bg-blue-50">Please enter a stock ticker in the search bar and press Enter or the 'Enter' button.</div>`;
    }
  }
}