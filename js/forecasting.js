// js/forecasting.js

// Tidak perlu lagi mengimpor showLoading/hideLoading karena core.js
// sudah menyediakannya secara global melalui window.showLoading dan window.hideLoading.
// const { showLoading, hideLoading } = await import('./core.js'); // HAPUS BARIS INI ATAU PASTIKAN TIDAK ADA

const API_BASE_URL_FORECASTING = "http://localhost:5002"; // Port untuk API forecasting

let forecastChartInstance = null; // Untuk menyimpan instance Chart.js

// Fungsi ini akan dipanggil oleh core.js saat bagian 'forecasting' dimuat
export function init() {
  // Nama fungsi diubah menjadi `init`
  // core.js sudah menangani injeksi HTML dan menampilkan/menyembunyikan loading global
  // untuk pemuatan bagian. Jadi, kita tidak perlu memuat HTML lagi di sini.

  // Ambil referensi elemen-elemen UI setelah HTML dipastikan sudah dimuat
  const runForecastBtn = document.getElementById("run-forecast-btn");
  if (runForecastBtn) {
    runForecastBtn.addEventListener("click", handleForecastSubmit);
  } else {
    console.error("Run Forecast button not found in forecasting.html.");
    // Anda mungkin ingin menampilkan pesan error ke user di sini
  }

  // Ambil daftar model yang tersedia dan isi dropdown timeframe
  fetchAvailableModels();
}

async function fetchAvailableModels() {
  const timeframeSelect = document.getElementById("forecast-timeframe");
  const forecastLoading = document.getElementById("forecast-loading");

  if (!timeframeSelect || !forecastLoading) {
    console.error(
      "Forecasting UI elements (timeframe select or loading indicator) not found."
    );
    return;
  }

  forecastLoading.classList.add("active"); // Tampilkan loading spesifik untuk model

  try {
    const response = await fetch(
      `${API_BASE_URL_FORECASTING}/models/available`
    );
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    const availableModels = data.available_models;

    timeframeSelect.innerHTML = '<option value="">Select a timeframe</option>'; // Bersihkan opsi yang ada
    const uniqueTimeframes = [
      ...new Set(availableModels.map((m) => m.timeframe)),
    ];

    uniqueTimeframes.forEach((timeframe) => {
      const option = document.createElement("option");
      option.value = timeframe;
      option.textContent = timeframe;
      timeframeSelect.appendChild(option);
    });

    if (uniqueTimeframes.length === 0) {
      timeframeSelect.innerHTML =
        '<option value="">No models available</option>';
    }
  } catch (error) {
    console.error("Error fetching available models:", error);
    timeframeSelect.innerHTML =
      '<option value="">Error loading timeframes</option>';
    displayMessage(
      "error",
      `Failed to load available timeframes: ${error.message}`
    );
  } finally {
    forecastLoading.classList.remove("active"); // Sembunyikan loading spesifik
  }
}

async function handleForecastSubmit() {
  const tickerInput = document.getElementById("forecast-ticker");
  const timeframeSelect = document.getElementById("forecast-timeframe");
  const forecastMessage = document.getElementById("forecast-message");
  const forecastResults = document.getElementById("forecast-results");
  const runForecastBtn = document.getElementById("run-forecast-btn");

  // Pastikan semua elemen UI ada sebelum melanjutkan
  if (
    !tickerInput ||
    !timeframeSelect ||
    !forecastMessage ||
    !forecastResults ||
    !runForecastBtn
  ) {
    console.error(
      "One or more forecasting UI elements are missing during submission."
    );
    displayMessage(
      "error",
      "Critical UI elements missing. Please refresh the page."
    );
    return;
  }

  const ticker = tickerInput.value.trim().toUpperCase();
  const timeframe = timeframeSelect.value;

  if (!ticker) {
    displayMessage("error", "Please enter a stock ticker.");
    return;
  }
  if (!timeframe) {
    displayMessage("error", "Please select a timeframe.");
    return;
  }

  displayMessage("hide"); // Bersihkan pesan sebelumnya
  forecastResults.classList.add("hidden"); // Sembunyikan hasil sampai sukses
  runForecastBtn.disabled = true;
  runForecastBtn.innerHTML =
    '<i class="fas fa-spinner fa-spin"></i> <span>Forecasting...</span>';

  // Panggil showLoading global dari core.js
  if (typeof showLoading === "function") {
    // Cek apakah showLoading tersedia secara global
    showLoading(true);
  }

  try {
    const response = await fetch(`${API_BASE_URL_FORECASTING}/forecast`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ticker, timeframe }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "An unknown error occurred during forecasting."
      );
    }

    displayMessage(
      "success",
      `Forecast generated successfully for ${ticker} (${timeframe})!`
    );
    document.getElementById("forecast-ticker-display").innerText = ticker;
    document.getElementById("forecast-timeframe-display").innerText = timeframe;

    renderForecastChart(
      data.actual_history_dates,
      data.actual_history,
      data.forecast
    );
    displayForecastDetails(data.forecast);
    displayEvaluationMetrics(data.mae, data.mse, data.mape);

    forecastResults.classList.remove("hidden"); // Tampilkan bagian hasil
  } catch (error) {
    console.error("Error during forecast:", error);
    displayMessage("error", `Forecasting failed: ${error.message}`);
  } finally {
    runForecastBtn.disabled = false;
    runForecastBtn.innerHTML =
      '<i class="fas fa-magic"></i> <span>Run Forecast</span>';
    // Panggil hideLoading global dari core.js
    if (typeof hideLoading === "function") {
      // Cek apakah hideLoading tersedia secara global
      hideLoading(false);
    }
  }
}

function renderForecastChart(actualDates, actualPrices, predictions) {
  const ctx = document.getElementById("forecastChart");
  if (!ctx) {
    console.error("Forecast chart canvas not found.");
    return;
  }
  const chartCtx = ctx.getContext("2d");

  // Hancurkan instance chart yang ada jika ada
  if (forecastChartInstance) {
    forecastChartInstance.destroy();
  }

  // Siapkan label untuk chart
  // Untuk prediksi, kita menambahkan label generik 'T+1', 'T+2', dst.
  const combinedLabels = [...actualDates];
  for (let i = 1; i <= predictions.length; i++) {
    combinedLabels.push(`T+${i}`);
  }

  // Siapkan data untuk chart
  // Garis prediksi dimulai dari titik terakhir data aktual
  const predictionData = Array(actualPrices.length - 1)
    .fill(null)
    .concat([actualPrices[actualPrices.length - 1]])
    .concat(predictions);

  forecastChartInstance = new Chart(chartCtx, {
    type: "line",
    data: {
      labels: combinedLabels,
      datasets: [
        {
          label: "Actual Price",
          data: actualPrices,
          borderColor: "#4CAF50", // Hijau
          backgroundColor: "rgba(76, 175, 80, 0.2)",
          fill: false,
          tension: 0.1,
          pointRadius: 2,
          pointBackgroundColor: "#4CAF50",
        },
        {
          label: "Predicted Price",
          data: predictionData,
          borderColor: "#3B82F6", // Biru
          backgroundColor: "rgba(59, 130, 246, 0.2)",
          fill: false,
          tension: 0.1,
          pointRadius: 4,
          pointBackgroundColor: "#3B82F6",
          borderDash: [5, 5], // Garis putus-putus untuk prediksi
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          mode: "index",
          intersect: false,
        },
        title: {
          display: true,
          text: "Stock Price Actual vs. Forecast",
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Time",
          },
          grid: {
            display: false,
          },
        },
        y: {
          title: {
            display: true,
            text: "Price",
          },
          grid: {
            color: "rgba(0, 0, 0, 0.05)",
          },
        },
      },
    },
  });
}

function displayForecastDetails(predictions) {
  document.getElementById("pred-h1").innerText = predictions[0]
    ? predictions[0].toFixed(2)
    : "--";
  document.getElementById("pred-h2").innerText = predictions[1]
    ? predictions[1].toFixed(2)
    : "--";
  document.getElementById("pred-h3").innerText = predictions[2]
    ? predictions[2].toFixed(2)
    : "--";
}

function displayEvaluationMetrics(mae, mse, mape) {
  document.getElementById("metric-mae").innerText =
    mae !== null ? mae.toFixed(4) : "--";
  document.getElementById("metric-mse").innerText =
    mse !== null ? mse.toFixed(4) : "--";
  document.getElementById("metric-mape").innerText =
    mape !== null ? `${mape.toFixed(2)}%` : "--";
}

function displayMessage(type, message = "") {
  const forecastMessage = document.getElementById("forecast-message");
  if (!forecastMessage) {
    console.error("Forecast message element not found.");
    return;
  }
  forecastMessage.classList.remove(
    "hidden",
    "error-message",
    "success-message"
  );

  if (type === "error") {
    forecastMessage.classList.add("error-message");
    forecastMessage.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
  } else if (type === "success") {
    forecastMessage.classList.add("success-message");
    forecastMessage.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
  } else if (type === "hide") {
    forecastMessage.classList.add("hidden");
  }
}
