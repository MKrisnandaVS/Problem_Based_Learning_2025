$(document).ready(function () {
    $.getJSON("cyber_data_sample.json", function (data) {
      const originalData = data;
  
      function populateFilters(data) {
        const years = [...new Set(data.map((row) => row.Year))].sort();
        const countries = [...new Set(data.map((row) => row.Country))].sort();
        const attacks = [...new Set(data.map((row) => row["Attack Type"]))].sort();
        const industries = [...new Set(data.map((row) => row["Target Industry"]))].sort();
  
        years.forEach((year) =>
          $("#yearFilter").append(`<option value="${year}">${year}</option>`)
        );
        countries.forEach((country) =>
          $("#countryFilter").append(`<option value="${country}">${country}</option>`)
        );
        attacks.forEach((attack) =>
          $("#attackFilter").append(`<option value="${attack}">${attack}</option>`)
        );
        industries.forEach((industry) =>
          $("#industryFilter").append(`<option value="${industry}">${industry}</option>`)
        );
      }
  
      function renderTableAndChart(filteredData) {
        let tableBody = "";
        let categories = [];
        let financialLoss = [],
          affectedUsers = [],
          resolutionTime = [];
        let totalLoss = 0,
          totalUsers = 0,
          totalTime = 0;
  
        filteredData.forEach((row) => {
          tableBody += `<tr>
            <td>${row.Country}</td>
            <td>${row.Year}</td>
            <td>${row["Attack Type"]}</td>
            <td>${row["Target Industry"]}</td>
            <td>${row["Financial Loss (in Million $)"]}</td>
            <td>${row["Number of Affected Users"]}</td>
            <td>${row["Attack Source"]}</td>
            <td>${row["Security Vulnerability Type"]}</td>
            <td>${row["Defense Mechanism Used"]}</td>
            <td>${row["Incident Resolution Time (in Hours)"]}</td>
          </tr>`;
  
          categories.push(`${row.Country} ${row.Year}`);
          financialLoss.push(row["Financial Loss (in Million $)"]);
          affectedUsers.push(row["Number of Affected Users"]);
          resolutionTime.push(row["Incident Resolution Time (in Hours)"]);
  
          totalLoss += row["Financial Loss (in Million $)"];
          totalUsers += row["Number of Affected Users"];
          totalTime += row["Incident Resolution Time (in Hours)"];
        });
  
        const avgLoss = (totalLoss / filteredData.length).toFixed(2);
        const avgUsers = Math.round(totalUsers / filteredData.length);
        const avgTime = (totalTime / filteredData.length).toFixed(2);
  
        $("#cyberTable").DataTable().clear().destroy();
        $("#cyberTable tbody").html(tableBody);
        $("#cyberTable").DataTable();
  
        $("#chart-summary").remove();
        $("#chart-container").before(
          `<div id="chart-summary" class="mt-6 text-center bg-white shadow rounded p-4">
            <p class="text-lg font-semibold">📊 Summary:</p>
            <p>💸 Average Financial Loss: <strong>$${avgLoss}M</strong></p>
            <p>👥 Average Affected Users: <strong>${avgUsers}</strong></p>
            <p>⏱️ Average Resolution Time: <strong>${avgTime} hours</strong></p>
          </div>`
        );
  
        const avgLossLine = Array(filteredData.length).fill(parseFloat(avgLoss));
        const avgUsersLine = Array(filteredData.length).fill(avgUsers);
        const avgTimeLine = Array(filteredData.length).fill(parseFloat(avgTime));
  
        Highcharts.chart("chart-container", {
          chart: { zoomType: 'xy' },
          title: { text: "Cyber Threat Metrics Overview" },
          xAxis: { categories: categories, crosshair: true },
          yAxis: [{ title: { text: "Amount / Count" } }],
          tooltip: { shared: true },
          series: [
            { name: "Financial Loss (M $)", type: 'column', data: financialLoss },
            { name: "Affected Users", type: 'column', data: affectedUsers },
            { name: "Resolution Time (Hours)", type: 'line', data: resolutionTime, marker: { enabled: true } },
            { name: "Avg Financial Loss", type: 'line', data: avgLossLine, dashStyle: 'ShortDot', color: '#888' },
            { name: "Avg Affected Users", type: 'line', data: avgUsersLine, dashStyle: 'ShortDot', color: '#555' },
            { name: "Avg Resolution Time", type: 'line', data: avgTimeLine, dashStyle: 'ShortDot', color: '#333' }
          ],
        });
      }
  
      function applyFilters() {
        const year = $("#yearFilter").val();
        const country = $("#countryFilter").val();
        const attack = $("#attackFilter").val();
        const industry = $("#industryFilter").val();
  
        const filteredData = originalData.filter((row) => {
          return (
            (year === "All" || row.Year == year) &&
            (country === "All" || row.Country == country) &&
            (attack === "All" || row["Attack Type"] === attack) &&
            (industry === "All" || row["Target Industry"] === industry)
          );
        });
  
        renderTableAndChart(filteredData);
      }
  
      populateFilters(originalData);
      renderTableAndChart(originalData);
  
      $("#yearFilter, #countryFilter, #attackFilter, #industryFilter").on("change", applyFilters);
    });
  });