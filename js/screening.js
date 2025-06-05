// js/screening.js

import { config, showLoading, formatValue, formatPercentage } from "./core.js";

const API_BASE_URL = config.API_BASE_URL;

let currentPage = 1;
const itemsPerPage = 50; // Corresponds to the 'limit' in the API
let totalResults = 0;
let currentFilters = {}; // Objek untuk menyimpan state filter saat ini

// Deklarasi variabel DOM, tapi inisialisasinya akan dilakukan di dalam init()
let filterElements = {};
let resultsBody;
let resultsCountSpan;
let loadingResultsDiv;
let noResultsMessage;
let prevPageBtn;
let nextPageBtn;
let paginationInfo;

export async function init() {
  // Re-query all DOM elements here to get references to the newly loaded HTML
  filterElements = {
    ticker: document.getElementById("ticker-filter"),
    sector: document.getElementById("sector-filter"),
    minMarketCap: document.getElementById("min-market-cap"),
    maxMarketCap: document.getElementById("max-market-cap"),
    maxTrailingPe: document.getElementById("max-trailing-pe"),
    maxForwardPe: document.getElementById("max-forward-pe"),
    maxPb: document.getElementById("max-pb"),
    maxPs: document.getElementById("max-ps"),
    minDividendYield: document.getElementById("min-dividend-yield"),
    maxPayoutRatio: document.getElementById("max-payout-ratio"),
    minProfitMargins: document.getElementById("min-profit-margins"),
    minGrossMargins: document.getElementById("min-gross-margins"),
    minOperatingMargins: document.getElementById("min-operating-margins"),
    minRoe: document.getElementById("min-roe"),
    minRoa: document.getElementById("min-roa"),
    minRevenueGrowth: document.getElementById("min-revenue-growth"),
    minEarningsGrowth: document.getElementById("min-earnings-growth"),
    minEarningsQuarterlyGrowth: document.getElementById(
      "min-earnings-quarterly-growth"
    ),
    minCurrentRatio: document.getElementById("min-current-ratio"),
    maxDebtToEquity: document.getElementById("max-debt-to-equity"),
    minTrailingEps: document.getElementById("min-trailing-eps"),
  };

  // Re-assign other global DOM references
  resultsBody = document.getElementById("screener-results-body");
  resultsCountSpan = document.getElementById("results-count");
  loadingResultsDiv = document.getElementById("loading-results");
  noResultsMessage = document.getElementById("no-results-message");
  prevPageBtn = document.getElementById("prev-page-btn");
  nextPageBtn = document.getElementById("next-page-btn");
  paginationInfo = document.getElementById("pagination-info");

  await populateSectors();
  setupEventListeners();
  loadFilterState(); // Memuat state filter yang tersimpan
  await fetchScreenedStocks(currentPage); // Menggunakan currentPage yang dimuat
}

async function populateSectors() {
  try {
    const response = await fetch(`${API_BASE_URL}/company-info/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    const sectors = [
      ...new Set(
        data.map((company) => company.sector).filter((sector) => sector)
      ),
    ].sort();

    // Pastikan filterElements.sector sudah ada saat ini
    if (filterElements.sector) {
      filterElements.sector.innerHTML = '<option value="">All Sectors</option>';
      sectors.forEach((sector) => {
        const option = document.createElement("option");
        option.value = sector;
        option.textContent = sector;
        filterElements.sector.appendChild(option);
      });
    }
  } catch (error) {
    // console.error("Error fetching sectors:", error); // Menjaga error ini untuk debugging
  }
}

function setupEventListeners() {
  // Pastikan tombol-tombol ada sebelum menambahkan event listener
  const applyBtn = document.getElementById("apply-filters-btn");
  const resetBtn = document.getElementById("reset-filters-btn");

  if (applyBtn) {
    applyBtn.addEventListener("click", () => fetchScreenedStocks(1));
  }
  if (resetBtn) {
    resetBtn.addEventListener("click", resetFilters);
  }

  if (prevPageBtn) {
    prevPageBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        fetchScreenedStocks(currentPage);
      }
    });
  }

  if (nextPageBtn) {
    nextPageBtn.addEventListener("click", () => {
      if (totalResults === 0 || currentPage * itemsPerPage < totalResults) {
        currentPage++;
        fetchScreenedStocks(currentPage);
      }
    });
  }

  // Event listeners for Enter key on filter inputs
  for (const key in filterElements) {
    if (filterElements[key]) {
      if (
        filterElements[key].tagName === "INPUT" ||
        filterElements[key].tagName === "SELECT"
      ) {
        if (
          filterElements[key].type !== "text" &&
          filterElements[key].type !== "number"
        ) {
          filterElements[key].addEventListener("change", () => {
            fetchScreenedStocks(1);
          });
        }
        filterElements[key].addEventListener("keypress", (e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            fetchScreenedStocks(1);
          }
        });
      }
    }
  }
}

function getFilterParams() {
  const params = new URLSearchParams();
  const filters = {};

  // General Filters
  if (filterElements.sector && filterElements.sector.value) {
    params.append("sector", filterElements.sector.value);
    filters.sector = filterElements.sector.value;
  }
  if (filterElements.minMarketCap && filterElements.minMarketCap.value) {
    params.append(
      "min_market_cap",
      parseFloat(filterElements.minMarketCap.value) * 1_000_000_000
    );
    filters.minMarketCap = filterElements.minMarketCap.value;
  }
  if (filterElements.maxMarketCap && filterElements.maxMarketCap.value) {
    params.append(
      "max_market_cap",
      parseFloat(filterElements.maxMarketCap.value) * 1_000_000_000
    );
    filters.maxMarketCap = filterElements.maxMarketCap.value;
  }

  // Valuation Filters
  if (filterElements.maxTrailingPe && filterElements.maxTrailingPe.value) {
    params.append(
      "max_trailing_pe",
      parseFloat(filterElements.maxTrailingPe.value)
    );
    filters.maxTrailingPe = filterElements.maxTrailingPe.value;
  }
  if (filterElements.maxForwardPe && filterElements.maxForwardPe.value) {
    params.append(
      "max_forward_pe",
      parseFloat(filterElements.maxForwardPe.value)
    );
    filters.maxForwardPe = filterElements.maxForwardPe.value;
  }
  if (filterElements.maxPb && filterElements.maxPb.value) {
    params.append("max_pb", parseFloat(filterElements.maxPb.value));
    filters.maxPb = filterElements.maxPb.value;
  }
  if (filterElements.maxPs && filterElements.maxPs.value) {
    params.append("max_ps", parseFloat(filterElements.maxPs.value));
    filters.maxPs = filterElements.maxPs.value;
  }
  if (filterElements.minTrailingEps && filterElements.minTrailingEps.value) {
    params.append(
      "min_trailing_eps",
      parseFloat(filterElements.minTrailingEps.value)
    );
    filters.minTrailingEps = filterElements.minTrailingEps.value;
  }

  // Dividend Filters
  if (
    filterElements.minDividendYield &&
    filterElements.minDividendYield.value
  ) {
    params.append(
      "min_dividend_yield",
      parseFloat(filterElements.minDividendYield.value)
    );
    filters.minDividendYield = filterElements.minDividendYield.value;
  }
  if (filterElements.maxPayoutRatio && filterElements.maxPayoutRatio.value) {
    params.append(
      "max_payout_ratio",
      parseFloat(filterElements.maxPayoutRatio.value)
    );
    filters.maxPayoutRatio = filterElements.maxPayoutRatio.value;
  }

  // Profitability Filters
  if (
    filterElements.minProfitMargins &&
    filterElements.minProfitMargins.value
  ) {
    params.append(
      "min_profit_margins",
      parseFloat(filterElements.minProfitMargins.value)
    );
    filters.minProfitMargins = filterElements.minProfitMargins.value;
  }
  if (filterElements.minGrossMargins && filterElements.minGrossMargins.value) {
    params.append(
      "min_gross_margins",
      parseFloat(filterElements.minGrossMargins.value)
    );
    filters.minGrossMargins = filterElements.minGrossMargins.value;
  }
  if (
    filterElements.minOperatingMargins &&
    filterElements.minOperatingMargins.value
  ) {
    params.append(
      "min_operating_margins",
      parseFloat(filterElements.minOperatingMargins.value)
    );
    filters.minOperatingMargins = filterElements.minOperatingMargins.value;
  }
  if (filterElements.minRoe && filterElements.minRoe.value) {
    params.append("min_roe", parseFloat(filterElements.minRoe.value));
    filters.minRoe = filterElements.minRoe.value;
  }
  if (filterElements.minRoa && filterElements.minRoa.value) {
    params.append("min_roa", parseFloat(filterElements.minRoa.value));
    filters.minRoa = filterElements.minRoa.value;
  }

  // Growth Filters
  if (
    filterElements.minRevenueGrowth &&
    filterElements.minRevenueGrowth.value
  ) {
    params.append(
      "min_revenue_growth",
      parseFloat(filterElements.minRevenueGrowth.value)
    );
    filters.minRevenueGrowth = filterElements.minRevenueGrowth.value;
  }
  if (
    filterElements.minEarningsGrowth &&
    filterElements.minEarningsGrowth.value
  ) {
    params.append(
      "min_earnings_growth",
      parseFloat(filterElements.minEarningsGrowth.value)
    );
    filters.minEarningsGrowth = filterElements.minEarningsGrowth.value;
  }
  if (
    filterElements.minEarningsQuarterlyGrowth &&
    filterElements.minEarningsQuarterlyGrowth.value
  ) {
    params.append(
      "min_earnings_quarterly_growth",
      parseFloat(filterElements.minEarningsQuarterlyGrowth.value)
    );
    filters.minEarningsQuarterlyGrowth =
      filterElements.minEarningsQuarterlyGrowth.value;
  }

  // Liquidity & Debt Filters
  if (filterElements.minCurrentRatio && filterElements.minCurrentRatio.value) {
    params.append(
      "min_current_ratio",
      parseFloat(filterElements.minCurrentRatio.value)
    );
    filters.minCurrentRatio = filterElements.minCurrentRatio.value;
  }
  if (filterElements.maxDebtToEquity && filterElements.maxDebtToEquity.value) {
    params.append(
      "max_debt_to_equity",
      parseFloat(filterElements.maxDebtToEquity.value)
    );
    filters.maxDebtToEquity = filterElements.maxDebtToEquity.value;
  }

  // Simpan filter ke currentFilters (termasuk ticker untuk client-side filtering)
  if (filterElements.ticker) {
    filters.ticker = filterElements.ticker.value.trim();
  }
  currentFilters = filters; // Update state global
  return params;
}

async function fetchScreenedStocks(page = 1) {
  showLoading(true);
  if (loadingResultsDiv) loadingResultsDiv.classList.remove("hidden");
  if (noResultsMessage) noResultsMessage.classList.add("hidden");

  currentPage = page;
  if (resultsBody) resultsBody.innerHTML = "";

  const apiParams = getFilterParams();
  const clientSideTicker = currentFilters.ticker;

  apiParams.append("limit", itemsPerPage);
  apiParams.append("offset", (currentPage - 1) * itemsPerPage);

  const queryString = apiParams.toString();
  const url = `${API_BASE_URL}/stock-screener?${queryString}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    let data = await response.json();

    let filteredData = data;
    if (clientSideTicker) {
      const lowerCaseTicker = clientSideTicker.toLowerCase();
      filteredData = data.filter((stock) =>
        stock.ticker.toLowerCase().includes(lowerCaseTicker)
      );
    }

    if (data.length === itemsPerPage) {
      totalResults = currentPage * itemsPerPage + 1;
    } else {
      totalResults = (currentPage - 1) * itemsPerPage + filteredData.length;
    }

    if (resultsCountSpan) {
      resultsCountSpan.textContent =
        totalResults > currentPage * itemsPerPage
          ? `${(currentPage - 1) * itemsPerPage + 1}-${endItem(
              filteredData.length
            )}+`
          : `${(currentPage - 1) * itemsPerPage + 1}-${endItem(
              filteredData.length
            )} of ${totalResults}`;
      if (filteredData.length === 0 && currentPage === 1) {
        resultsCountSpan.textContent = "0";
      }
    }

    renderTable(filteredData);
    updatePaginationControls(filteredData.length);

    if (noResultsMessage) {
      if (filteredData.length === 0 && currentPage === 1) {
        noResultsMessage.classList.remove("hidden");
      } else {
        noResultsMessage.classList.add("hidden");
      }
    }

    saveFilterStateAndPage();
  } catch (error) {
    // console.error("Error fetching screened stocks:", error); // Menjaga error ini untuk debugging
    if (resultsBody)
      resultsBody.innerHTML = `<tr><td colspan="21" class="text-center py-4 text-red-500">Failed to load results. Please try again.</td></tr>`;
    if (resultsCountSpan) resultsCountSpan.textContent = "0";
    if (noResultsMessage) noResultsMessage.classList.remove("hidden");
    updatePaginationControls(0);
  } finally {
    showLoading(false);
    if (loadingResultsDiv) loadingResultsDiv.classList.add("hidden");
  }
}

function renderTable(stocks) {
  if (!resultsBody) {
    return;
  }
  resultsBody.innerHTML = "";
  if (stocks.length === 0) {
    return;
  }

  stocks.forEach((stock) => {
    const row = document.createElement("tr");
    row.classList.add(
      "bg-white",
      "border-b",
      "hover:bg-gray-50",
      "transition-colors",
      "duration-150",
      "ease-in-out"
    );
    row.innerHTML = `
            <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${
              stock.ticker || "N/A"
            }</td>
            <td class="px-6 py-4">${stock.name || "N/A"}</td>
            <td class="px-6 py-4">${stock.sector || "N/A"}</td>
            <td class="px-6 py-4">${formatValue(stock.marketcap, true)}</td>
            <td class="px-6 py-4">${formatValue(stock.trailingpe)}</td>
            <td class="px-6 py-4">${formatValue(stock.forwardpe)}</td>
            <td class="px-6 py-4">${formatValue(stock.pricetobook)}</td>
            <td class="px-6 py-4">${formatValue(
              stock.pricetosalestrailing12months
            )}</td>
            <td class="px-6 py-4">${formatPercentage(stock.dividendyield)}</td>
            <td class="px-6 py-4">${formatPercentage(stock.payoutratio)}</td>
            <td class="px-6 py-4">${formatPercentage(stock.profitmargins)}</td>
            <td class="px-6 py-4">${formatPercentage(stock.grossmargins)}</td>
            <td class="px-6 py-4">${formatPercentage(
              stock.operatingmargins
            )}</td>
            <td class="px-6 py-4">${formatPercentage(stock.returnonequity)}</td>
            <td class="px-6 py-4">${formatPercentage(stock.returnonassets)}</td>
            <td class="px-6 py-4">${formatPercentage(stock.revenuegrowth)}</td>
            <td class="px-6 py-4">${formatPercentage(stock.earningsgrowth)}</td>
            <td class="px-6 py-4">${formatPercentage(
              stock.earningsquarterlygrowth
            )}</td>
            <td class="px-6 py-4">${formatValue(stock.currentratio)}</td>
            <td class="px-6 py-4">${formatValue(stock.debttoequity)}</td>
            <td class="px-6 py-4">${formatValue(stock.trailingeps)}</td>
        `;
    resultsBody.appendChild(row);
  });
}

function endItem(currentLength) {
  return (currentPage - 1) * itemsPerPage + currentLength;
}

function updatePaginationControls(currentResultsLength) {
  if (!paginationInfo || !prevPageBtn || !nextPageBtn) {
    return;
  }

  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const currentEnd = (currentPage - 1) * itemsPerPage + currentResultsLength;

  let infoText = "";
  if (totalResults === 0 || currentResultsLength === 0) {
    infoText = "No results";
  } else {
    if (
      currentResultsLength < itemsPerPage &&
      currentPage * itemsPerPage >= totalResults
    ) {
      infoText = `Showing ${startItem}-${currentEnd} of ${totalResults} stocks`;
    } else {
      infoText = `Showing ${startItem}-${currentEnd} (approx. ${totalResults}+ stocks)`;
    }
  }
  paginationInfo.textContent = infoText;

  prevPageBtn.disabled = currentPage === 1;
  nextPageBtn.disabled = currentResultsLength < itemsPerPage;
}

function saveFilterStateAndPage() {
  sessionStorage.setItem("screeningFilters", JSON.stringify(currentFilters));
  sessionStorage.setItem("screeningCurrentPage", currentPage.toString());
}

function loadFilterState() {
  const savedFilters = sessionStorage.getItem("screeningFilters");
  const savedPage = sessionStorage.getItem("screeningCurrentPage");

  if (savedFilters) {
    const filters = JSON.parse(savedFilters);
    currentFilters = filters;
    for (const key in filters) {
      if (filterElements[key]) {
        filterElements[key].value = filters[key];
      }
    }
  } else {
    currentFilters = {};
  }

  if (savedPage) {
    currentPage = parseInt(savedPage);
  } else {
    currentPage = 1;
  }
}

function resetFilters() {
  for (const key in filterElements) {
    if (filterElements[key]) {
      if (filterElements[key].tagName === "INPUT") {
        filterElements[key].value = "";
      } else if (filterElements[key].tagName === "SELECT") {
        filterElements[key].value = "";
      }
    }
  }
  sessionStorage.removeItem("screeningFilters");
  sessionStorage.removeItem("screeningCurrentPage");

  currentFilters = {};

  fetchScreenedStocks(1);
}
