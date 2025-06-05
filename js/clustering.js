// js/clustering.js

// API Base URL untuk backend clustering (berjalan di port 5003)
const API_BASE_URL_CLUSTERING = 'http://localhost:5003/api'; 

// Fungsi untuk mengganti tab dan menyimpan status ke localStorage
function switchTabClustering(tabName, saveToLocalStorage = false) {
    console.log(`Switching to clustering tab: ${tabName}`);
    document.querySelectorAll('#content-container .tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('#content-container .tab-btn').forEach(btn => {
        btn.classList.remove('tab-active');
    });

    const contentElement = document.getElementById('content-' + tabName); 
    const tabButtonElement = document.getElementById('tab-' + tabName); 

    if (contentElement) contentElement.classList.add('active');
    if (tabButtonElement) tabButtonElement.classList.add('tab-active');

    if (saveToLocalStorage) {
        localStorage.setItem('activeStockClusteringTab', tabName); 
    }
}
window.switchTabClustering = switchTabClustering;


function updateDataAvailability(epsLoaded, roeLoaded) {
    // ... (kode fungsi ini tetap sama) ...
    console.log(`Updating data availability: EPS Loaded - ${epsLoaded}, ROE Loaded - ${roeLoaded}`);
    const epsIndicator = document.getElementById('eps-data-status-indicator');
    const epsText = document.getElementById('eps-data-status-text');
    const roeIndicator = document.getElementById('roe-data-status-indicator');
    const roeText = document.getElementById('roe-data-status-text');

    if (!epsIndicator || !epsText || !roeIndicator || !roeText) {
        console.warn("Data availability status elements not found.");
        return;
    }

    [epsIndicator, roeIndicator].forEach(el => el.classList.remove('bg-yellow-400', 'animate-pulse'));

    if (epsLoaded) {
        epsIndicator.className = 'w-3 h-3 rounded-full mr-2 bg-green-500';
        epsText.textContent = 'Data EPS: Tersedia';
    } else {
        epsIndicator.className = 'w-3 h-3 rounded-full mr-2 bg-red-500';
        epsText.textContent = 'Data EPS: Tidak Tersedia (Data Dummy)';
    }

    if (roeLoaded) {
        roeIndicator.className = 'w-3 h-3 rounded-full mr-2 bg-green-500';
        roeText.textContent = 'Data ROE: Tersedia';
    } else {
        roeIndicator.className = 'w-3 h-3 rounded-full mr-2 bg-red-500';
        roeText.textContent = 'Data ROE: Tidak Tersedia (Data Dummy)';
    }
}

function renderClusterStats(containerId, statsList, metricName) {
    // ... (kode fungsi ini tetap sama) ...
    console.log(`Rendering cluster stats for ${metricName} in #${containerId}`);
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container #${containerId} not found for cluster stats.`);
        return;
    }
    container.innerHTML = ''; // Clear previous content

    if (!statsList || statsList.length === 0) {
        container.innerHTML = `<p class="text-center text-gray-600 col-span-full">Statistik cluster ${metricName} tidak tersedia.</p>`;
        console.log(`No stats to render for ${metricName}.`);
        return;
    }

    statsList.forEach(stat => {
        const labelColorClass = stat.label.includes('Tinggi') ? 'text-green-600' : (stat.label.includes('Rendah') ? 'text-blue-600' : 'text-gray-500');
        const recomColorClass = stat.recommendation === 'Buy' ? 'text-green-700' : (stat.recommendation === 'Hold' ? 'text-yellow-600' : 'text-gray-500');
        
        const statCard = `
            <div class="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 flex flex-col justify-between">
                <div>
                    <h3 class="text-xl font-semibold text-gray-800 mb-1">
                        Cluster ${stat.id}: <span class="font-bold ${labelColorClass}">${stat.label}</span>
                    </h3>
                    <span class="inline-block bg-indigo-100 text-indigo-700 text-xs font-semibold px-3 py-1 rounded-full mb-4">
                        ${stat.count} saham
                    </span>
                </div>
                <div class="space-y-3 mt-auto">
                    <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span class="text-sm font-medium text-gray-600">Rata-rata ${metricName}:</span>
                        <span class="text-md font-bold text-gray-800">${stat.avg_metric}</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span class="text-sm font-medium text-gray-600">Rekomendasi:</span>
                        <span class="text-md font-bold ${recomColorClass}">
                            ${stat.recommendation}
                        </span>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', statCard);
    });
    console.log(`Finished rendering ${statsList.length} stats for ${metricName}.`);
}

// Fungsi renderPlotlyChart tetap ada, karena mungkin digunakan di masa depan
// atau oleh modul lain, tapi tidak akan dipanggil untuk scatter plot di sini.
function renderPlotlyChart(containerId, plotHtml) {
    // ... (kode fungsi ini tetap sama) ...
    console.log(`Rendering Plotly chart in #${containerId}`);
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container #${containerId} not found for Plotly chart.`);
        return;
    }
    // console.log(`Plot HTML received for #${containerId}:`, plotHtml); 
    if (plotHtml && plotHtml.trim() !== "") {
        container.innerHTML = plotHtml;
        if (typeof Plotly !== 'undefined' && container.querySelector('.js-plotly-plot')) {
            try {
                const plotDiv = container.querySelector('.js-plotly-plot');
                if (plotDiv) {
                    Plotly.Plots.resize(plotDiv);
                }
            } catch (e) {
                console.warn(`Plotly resize error for ${containerId}:`, e);
            }
        }
    } else {
        container.innerHTML = `<p class="text-center text-gray-600">Plot tidak tersedia.</p>`;
        console.log(`No Plotly HTML to render for #${containerId}.`);
    }
}

function renderMatplotlibChart(containerId, base64Image, altText = "Bar Chart") {
    // ... (kode fungsi ini tetap sama) ...
    console.log(`Rendering Matplotlib chart in #${containerId}`);
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container #${containerId} not found for Matplotlib chart.`);
        return;
    }
    if (base64Image) {
        container.innerHTML = `<img src="data:image/png;base64,${base64Image}" alt="${altText}" class="mx-auto max-w-full h-auto" />`;
    } else {
        container.innerHTML = `<p class="text-center text-gray-600">Chart tidak tersedia.</p>`;
        console.log(`No base64 image to render for #${containerId}.`);
    }
}

function renderTable(headers, rows) {
    // ... (kode fungsi ini tetap sama) ...
    console.log(`Rendering table with ${headers ? headers.length : 0} headers and ${rows ? rows.length : 0} rows.`);
    const tableHead = document.getElementById('mainDataTableHeadClustering');
    const tableBody = document.getElementById('mainDataTableBodyClustering');
    const tableStatus = document.getElementById('tableStatusClustering');

    if (!tableHead || !tableBody) {
        console.error("Table head or body element for clustering not found.");
        return;
    }

    tableHead.innerHTML = ''; 
    tableBody.innerHTML = ''; 
    if (tableStatus) tableStatus.textContent = '';

    if (!headers || headers.length === 0) {
        tableHead.innerHTML = '<tr><th class="text-center p-4 text-gray-600">Header tabel tidak tersedia.</th></tr>';
        tableBody.innerHTML = `<tr><td colspan="1" class="text-center p-4 text-gray-600">Data tabel tidak tersedia karena header tidak ada.</td></tr>`;
        console.log("Table headers are missing.");
        return;
    }

    const headerRow = document.createElement('tr');
    headers.forEach((headerText, headerIndex) => {
        const th = document.createElement('th');
        th.scope = 'col';
        th.className = 'px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sortable';
        
        th.textContent = headerText;
        th.dataset.columnIndex = headerIndex; 
        th.dataset.columnKey = headerText; 

        const span = document.createElement('span');
        span.className = 'sort-indicator';
        th.appendChild(span);
        headerRow.appendChild(th);
    });
    tableHead.appendChild(headerRow);

    if (!rows || rows.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="${headers.length}" class="text-center p-4 text-gray-600">Tidak ada data untuk ditampilkan.</td></tr>`;
        if (tableStatus) tableStatus.textContent = 'Tidak ada data.';
        console.log("No rows to render in table.");
        return;
    }

    rows.forEach(rowDataDict => {
        const tr = document.createElement('tr');
        headers.forEach((headerKeyFromList) => { 
            const td = document.createElement('td');
            td.className = 'px-4 py-4 whitespace-nowrap text-sm';
            if (headerKeyFromList === headers[0]) { 
                 td.classList.add('text-gray-900', 'font-medium');
            } else {
                 td.classList.add('text-gray-700');
            }
            const cellValue = rowDataDict[headerKeyFromList];
            td.textContent = cellValue !== undefined && cellValue !== null ? String(cellValue) : 'N/A';
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });
    if (tableStatus) tableStatus.textContent = `Menampilkan ${rows.length} baris data.`;
    console.log(`Finished rendering table.`);
    initializeTableSortingClustering(); 
}

async function fetchDashboardData() {
    console.log("Fetching clustering dashboard data...");
    try {
        const response = await fetch(`${API_BASE_URL_CLUSTERING}/dashboard-data`);
        if (!response.ok) {
            let errorDetail = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || errorDetail;
            } catch (e) { /* Ignore if response is not JSON */ }
            throw new Error(errorDetail);
        }
        const data = await response.json();
        console.log("Clustering dashboard data received:", data);

        const headerTitleEl = document.getElementById('headerTitle');
        if (headerTitleEl) headerTitleEl.textContent = data.page_title || "Analisis Clustering Saham";

        updateDataAvailability(data.eps_data_loaded, data.roe_data_loaded);
        
        const epsClusterStatsTitleEl = document.getElementById('epsClusterStatsTitle');
        if (epsClusterStatsTitleEl) epsClusterStatsTitleEl.textContent = `Statistik Cluster ${data.eps_metric} (${data.num_eps_clusters} Cluster)`;
        
        // PENGATURAN JUDUL UNTUK SCATTER PLOT DIHAPUS/DIKOMENTARI
        // const epsScatterPlotTitleEl = document.getElementById('epsScatterPlotTitle');
        // if (epsScatterPlotTitleEl) epsScatterPlotTitleEl.textContent = `Visualisasi Cluster ${data.eps_metric} (${data.num_eps_clusters} Cluster)`;

        const roeClusterStatsTitleEl = document.getElementById('roeClusterStatsTitle');
        if (roeClusterStatsTitleEl) roeClusterStatsTitleEl.textContent = `Statistik Cluster ${data.roe_metric} (${data.num_roe_clusters} Cluster)`;
        
        // PENGATURAN JUDUL UNTUK SCATTER PLOT DIHAPUS/DIKOMENTARI
        // const roeScatterPlotTitleEl = document.getElementById('roeScatterPlotTitle');
        // if (roeScatterPlotTitleEl) roeScatterPlotTitleEl.textContent = `Visualisasi Cluster ${data.roe_metric} (${data.num_roe_clusters} Cluster)`;

        renderClusterStats('epsClusterStatsContainer', data.eps_cluster_stats_list, data.eps_metric);
        // PANGGILAN RENDER PLOTLY CHART UNTUK EPS DIHAPUS/DIKOMENTARI
        // renderPlotlyChart('epsScatterPlotContainer', data.eps_scatter_plot_html);
        renderMatplotlibChart('epsBarChartContainer', data.eps_bar_chart_base64, `Top 15 ${data.eps_metric}`);
        
        renderClusterStats('roeClusterStatsContainer', data.roe_cluster_stats_list, data.roe_metric);
        // PANGGILAN RENDER PLOTLY CHART UNTUK ROE DIHAPUS/DIKOMENTARI
        // renderPlotlyChart('roeScatterPlotContainer', data.roe_scatter_plot_html);
        renderMatplotlibChart('roeBarChartContainer', data.roe_bar_chart_base64, `Top 15 ${data.roe_metric}`);

        renderTable(data.table_headers, data.table_rows);

    } catch (error) {
        console.error("Error fetching or processing clustering dashboard data:", error);
        const errorMessage = `Gagal memuat data clustering: ${error.message}. Pastikan backend clustering (port 5003) berjalan.`;
        // Container untuk scatter plot tidak lagi ada, jadi hapus dari daftar ini jika perlu
        ['epsClusterStatsContainer', 'roeClusterStatsContainer', 
         'epsBarChartContainer', 'roeBarChartContainer'] // Dihapus: 'epsScatterPlotContainer', 'roeScatterPlotContainer'
        .forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<p class="text-red-500 text-center p-4 col-span-full">${errorMessage}</p>`;
        });
        const tableBody = document.getElementById('mainDataTableBodyClustering');
        if (tableBody) tableBody.innerHTML = `<tr><td colspan="9" class="text-center p-4 text-red-500">${errorMessage}</td></tr>`;
        const tableStatus = document.getElementById('tableStatusClustering');
        if (tableStatus) tableStatus.textContent = errorMessage;
    }
}

// ... (sisa kode untuk table sorting dan init tetap sama) ...
let tableSortDirectionsClustering = {};

function initializeTableSortingClustering() {
    // ... (kode fungsi ini tetap sama) ...
    console.log("Initializing clustering table sorting...");
    const mainTable = document.getElementById('mainDataTableClustering');
    if (!mainTable) {
        console.error("mainDataTableClustering not found for sorting initialization.");
        return;
    }

    if (!mainTable.sortDirections) {
        mainTable.sortDirections = {}; 
    }

    const headers = mainTable.querySelectorAll('thead th.sortable');
    console.log(`Found ${headers.length} sortable headers for clustering table.`);

    headers.forEach(header => {
        const newHeader = header.cloneNode(true); 
        header.parentNode.replaceChild(newHeader, header);

        const columnIndex = parseInt(newHeader.dataset.columnIndex);
        const columnKey = newHeader.dataset.columnKey; 

        if (columnKey === undefined || isNaN(columnIndex)) {
            console.warn("Clustering table header missing data-column-key or data-column-index:", newHeader);
            return;
        }

        if (mainTable.sortDirections[columnKey] === undefined) {
            mainTable.sortDirections[columnKey] = ''; 
        }

        newHeader.addEventListener('click', () => {
            console.log(`Clustering table header clicked: ${columnKey}, Index: ${columnIndex}`);
            const currentSortDir = mainTable.sortDirections[columnKey];
            let newSortDir = (currentSortDir === 'asc') ? 'desc' : 'asc';
            
            Object.keys(mainTable.sortDirections).forEach(key => {
                if (key !== columnKey) mainTable.sortDirections[key] = '';
            });
            mainTable.sortDirections[columnKey] = newSortDir;

            sortTableClustering(mainTable, columnIndex, newSortDir);

            const allHeadersForIndicator = mainTable.querySelectorAll('thead th.sortable');
            allHeadersForIndicator.forEach(h => {
                const indicator = h.querySelector('.sort-indicator');
                const hKey = h.dataset.columnKey;
                if (indicator && hKey) {
                    indicator.innerHTML = (hKey === columnKey) ? (newSortDir === 'asc' ? '▲' : '▼') : '';
                }
            });
        });

        const indicator = newHeader.querySelector('.sort-indicator');
        if (indicator) {
            const storedDir = mainTable.sortDirections[columnKey];
            if (storedDir === 'asc') indicator.innerHTML = '▲';
            else if (storedDir === 'desc') indicator.innerHTML = '▼';
            else indicator.innerHTML = '';
        }
    });
}

function sortTableClustering(table, columnIndex, direction) {
    // ... (kode fungsi ini tetap sama) ...
    console.log(`Sorting clustering table by column index ${columnIndex}, direction ${direction}`);
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error("Clustering table body not found for sorting.");
        return;
    }
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((rowA, rowB) => {
        const cellA = rowA.querySelectorAll('td')[columnIndex];
        const cellB = rowB.querySelectorAll('td')[columnIndex];

        if (!cellA || !cellB) return 0;

        let valA = cellA.textContent.trim();
        let valB = cellB.textContent.trim();
        
        const numRegex = /^-?\s*([0-9,]+(\.[0-9]+)?)\s*%?\s*$/;
        const matchA = valA.match(numRegex);
        const matchB = valB.match(numRegex);
        let numA = NaN, numB = NaN;

        if (matchA) numA = parseFloat(matchA[1].replace(/,/g, ''));
        if (matchB) numB = parseFloat(matchB[1].replace(/,/g, ''));
        
        let comparison = 0;
        if (!isNaN(numA) && !isNaN(numB)) {
            if (numA < numB) comparison = -1;
            if (numA > numB) comparison = 1;
        } else if (!isNaN(numA)) { 
            comparison = -1; 
        } else if (!isNaN(numB)) { 
            comparison = 1;  
        } else { 
            valA = valA.toLowerCase();
            valB = valB.toLowerCase();
            if (valA < valB) comparison = -1;
            if (valA > valB) comparison = 1;
        }
        return direction === 'asc' ? comparison : -comparison;
    });

    rows.forEach(row => tbody.appendChild(row));
    console.log("Clustering table sorting complete.");
}


export async function init() {
    // ... (kode fungsi ini tetap sama) ...
    console.log("Clustering section initialized.");

    await fetchDashboardData(); 

    const savedTab = localStorage.getItem('activeStockClusteringTab');
    if (savedTab && document.getElementById('content-' + savedTab) && document.getElementById('tab-' + savedTab)) {
        switchTabClustering(savedTab, false); 
    } else {
        const defaultTab = 'eps'; 
        const epsTabButton = document.getElementById(`tab-${defaultTab}`);
        const epsContent = document.getElementById(`content-${defaultTab}`);
        if (epsTabButton && epsContent) {
            switchTabClustering(defaultTab, true); 
        } else {
            console.warn(`Default clustering tab '${defaultTab}' or content not found for initialization.`);
            const firstTabButton = document.querySelector('#content-container .tab-btn');
            if (firstTabButton) {
                const firstTabName = firstTabButton.id.replace('tab-', '');
                switchTabClustering(firstTabName, true);
            }
        }
    }

    const searchInput = document.getElementById('tableSearchInputClustering');
    if (searchInput) {
        searchInput.addEventListener('keyup', function (e) {
            const searchTerm = e.target.value.toLowerCase();
            const mainTable = document.getElementById('mainDataTableClustering');
            const tableStatus = document.getElementById('tableStatusClustering');
            let visibleRows = 0;
            if (mainTable) {
                const tableRows = mainTable.querySelectorAll('tbody tr');
                tableRows.forEach(row => {
                    const rowText = row.textContent.toLowerCase();
                    if (rowText.includes(searchTerm)) {
                        row.style.display = '';
                        visibleRows++;
                    } else {
                        row.style.display = 'none';
                    }
                });
                if (tableStatus) {
                    if (visibleRows === 0 && tableRows.length > 0) {
                        tableStatus.textContent = 'Tidak ada data yang cocok dengan pencarian.';
                    } else if (tableRows.length === 0) {
                        tableStatus.textContent = 'Tidak ada data untuk ditampilkan.';
                    } else {
                         tableStatus.textContent = `Menampilkan ${visibleRows} dari ${tableRows.length} baris.`;
                    }
                }
            }
        });
    } else {
        console.warn("Table search input 'tableSearchInputClustering' not found.");
    }
}