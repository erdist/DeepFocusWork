// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

// Area Chart Example
var ctx = document.getElementById("AreaChart");
var myLineChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
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
      data: [0,0,0,0,0,0,0,0,0,0,0,0],
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
        label: function(tooltipItem, chart) {
          var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
          return datasetLabel +": "+ tooltipItem.yLabel;
        }
      }
    }
  }
});
updateLineData();
function yearly(){
  document.getElementById("optionID").dataset.value = "yearly";
  updateLineData();
}
function daily(){
  document.getElementById("optionID").dataset.value = "daily";
  updateLineData();
}
function random() {
  document.getElementById("optionID").dataset.value = "random";
  updateLineData();
}

function updateLineData(){
  var option = document.getElementById("optionID").dataset.value;

  var callbackData;
  if(option == "yearly"){
    console.log(option);
    callbackData = $.get('/lineChartData/' + option);
    callbackData.done(function(results){
      myLineChart.data.labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      myLineChart.data.datasets[0].data = results.data;
      myLineChart.update();
    });
  }
  else if(option == "daily"){
    console.log(option);
    callbackData = $.get('/lineChartData/' + option);
    callbackData.done(function(results){
      myLineChart.data.labels = ["8.00", "9.00", "10.00", "11.00", "12.00", "13.00", "14.00", "15.00", "16.00", "17.00", "18.00", "19.00"];
      myLineChart.data.datasets[0].data = results.data;
      myLineChart.update();
    });
  }
  else if(option == "random"){
    console.log(option);
    callbackData = $.get('/lineChartData/' + option);
    callbackData.done(function(results){
      myLineChart.data.labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      myLineChart.data.datasets[0].data = results.data;
      myLineChart.update();
    });
  }

}

setInterval(updateLineData,3000);
