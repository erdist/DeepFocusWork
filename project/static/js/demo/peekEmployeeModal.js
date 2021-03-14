var myLineChart;
var myPieChart;

var loadCharts = function (employee, name) {
$('#peekModal').on('shown.bs.modal',function () {
  document.getElementById("peekModalTitle").innerHTML = name;
  var ctx = document.getElementById("AreaChart");
  myLineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ["8.00", "9.00", "10.00", "11.00", "12.00", "13.00", "14.00", "15.00", "16.00", "17.00", "18.00", "19.00"],
      datasets: [{
        label: "Distractions",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "rgba(78, 115, 223, 1)",
        pointRadius: 3,
        pointBackgroundColor: "rgba(78, 115, 223, 1)",
        pointBorderColor: "rgba(78, 115, 223, 1)",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
        pointHoverBorderColor: "rgba(78, 115, 223, 1)",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      }],
    },
    options: {
      maintainAspectRatio: false,
      responsive: true,
      layout: {
        padding: {
          left: 10,
          right: 25,
          top: 25,
          bottom: 0
        }
      },
      scales: {
        xAxes: [{
          time: {
            unit: 'date'
          },
          gridLines: {
            display: false,
            drawBorder: false
          },
          ticks: {
            maxTicksLimit: 7
          }
        }],
        yAxes: [{
          ticks: {
            maxTicksLimit: 5,
            padding: 10,
          },
          gridLines: {
            color: "rgb(234, 236, 244)",
            zeroLineColor: "rgb(234, 236, 244)",
            drawBorder: false,
            borderDash: [2],
            zeroLineBorderDash: [2]
          }
        }],
      },
      legend: {
        display: false
      },
      tooltips: {
        backgroundColor: "rgb(255,255,255)",
        bodyFontColor: "#858796",
        titleMarginBottom: 10,
        titleFontColor: '#6e707e',
        titleFontSize: 14,
        borderColor: '#dddfeb',
        borderWidth: 1,
        xPadding: 15,
        yPadding: 15,
        displayColors: false,
        intersect: false,
        mode: 'index',
        caretPadding: 10,
        callbacks: {
          label: function (tooltipItem, chart) {
            var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
            return datasetLabel + ": " + tooltipItem.yLabel;
          }
        }
      }
    }
  });

  var cty = document.getElementById("myPieChart");
  myPieChart = new Chart(cty, {
    type: 'pie',
    data: {
      datasets: [{
        data: [0, 0, 0, 0, 0], // This data list will be filled with our data
        backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'],
        hoverBackgroundColor: ['#2e59d9', '#17a673', '#2c9faf'],
        hoverBorderColor: "rgba(234, 236, 244, 1)",
      }],
      labels: ["Colleague", "Social", "Personal", "Noise", "Depression"],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      tooltips: {
        backgroundColor: "rgb(255,255,255)",
        bodyFontColor: "#858796",
        borderColor: '#dddfeb',
        borderWidth: 1,
        xPadding: 15,
        yPadding: 15,
        displayColors: true,
        caretPadding: 10,
      },
      legend: {
        display: true
      },
    },
  });


});
  var callbackData = $.get('/peekEmployee/' + employee);
    callbackData.done(function (results) {
      console.log("Done");
      myLineChart.data.datasets[0].data = results.linedata;
      myPieChart.data.datasets[0].data = results.piedata;
      myLineChart.update();
      myPieChart.update();
    });
  var callBackRecommendation = $.get('/giveMeARecommendation/' + employee);
    callBackRecommendation.done(function (results) {
      console.log("Recommendation Data fetched.")

      if(results.colleagueId != "")
      {
        document.getElementById('colleagueId').innerHTML = results.colleagueId;
        document.getElementById('colleagueId').style.display = "block"
      }
      else{
        document.getElementById('colleagueId').style.display = "none";
      }
      if(results.socialId != "")
      {
        document.getElementById('socialId').innerHTML = results.socialId;
        document.getElementById('socialId').style.display = "block"
      }
      else{
        document.getElementById('socialId').style.display = "none";
      }
      if(results.personalId != "")
      {
        document.getElementById('personalId').innerHTML = results.personalId;
        document.getElementById('personalId').style.display = "block"
      }
      else{
        document.getElementById('personalId').style.display = "none";
      }
      if(results.noiseId1 != "")
      {
        document.getElementById('noiseId1').innerHTML = results.noiseId1;
        document.getElementById('noiseId1').style.display = "block"
      }
      else{
        document.getElementById('noiseId1').style.display = "none";
      }
      if(results.noiseId2 != "")
      {
        document.getElementById('noiseId2').innerHTML = results.noiseId2;
        document.getElementById('noiseId2').style.display = "block"
      }
      else{
        document.getElementById('noiseId2').style.display = "none";
      }
      if(results.depressionId != "")
      {
        document.getElementById('depressionId').innerHTML = results.depressionId;
        document.getElementById('depressionId').style.display = "block"
      }
      else{
        document.getElementById('depressionId').style.display = "none";
      }

    })
};

function destroyCharts() {
  console.log("Etti")
  myLineChart.destroy();
  myPieChart.destroy();
  document.getElementById('depressionId').style.display = "none";
  document.getElementById('noiseId2').style.display = "none";
  document.getElementById('noiseId1').style.display = "none";
  document.getElementById('socialId').style.display = "none";
  document.getElementById('personalId').style.display = "none";
  document.getElementById('colleagueId').style.display = "none";
}