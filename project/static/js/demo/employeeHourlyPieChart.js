// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

// Pie Chart Example
var ctx = document.getElementById("myPieChart");
var myPieChart = new Chart(ctx, {
  type: 'pie',
  data: {
    datasets: [{
      data: [0,0,0,0,0], // This data list will be filled with our data
      backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc','#f6c23e','#e74a3b'],
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


function updateData(){
  var callbackData = $.get('/employeeHourlyPieChartData');
  callbackData.done(function(results){

    myPieChart.data.datasets[0].data = results.data;
    myPieChart.update();
  });

}

setInterval(updateData,2000);

