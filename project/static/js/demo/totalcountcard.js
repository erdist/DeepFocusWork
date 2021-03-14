function updateDistractionCount() {
  var monthlyDistractionCount;
  var totalDistractionCount;
  var monthlyProgressPercentage;
    var callbackData = $.get('/totalDistractionCount');
    callbackData.done(function (results) {
     totalDistractionCount = document.getElementById('totalDistractionCount');

     totalDistractionCount.innerHTML = results.data

    })
    var callbackData1 = $.get('/monthlyDistractionCount');
    callbackData1.done(function (results) {
        monthlyDistractionCount = document.getElementById('monthlyDistractionCount');
        monthlyProgressPercentage = document.getElementById('monthlyProgressPercentage');
        monthlyDistractionCount.innerHTML = results.data;
        monthlyProgressPercentage.innerHTML = results.data;
      if(document.getElementById('limitOption').dataset.value != 0){
         monthlyProgressPercentage.innerHTML = results.data;
         var limit = document.getElementById('limitOption').dataset.value;
         var percentage = Math.round((results.data/limit)*100);
         console.log(percentage);
         document.getElementById('monthlyProgressBar').innerHTML = percentage.toString() + "%";
         if(percentage>100){
           percentage=100;
         }
         document.getElementById('monthlyProgressBar').style.width = percentage.toString() + "%";

      }
      else{
        document.getElementById('monthlyProgressBar').innerHTML =  "Infinity";
        document.getElementById('monthlyProgressBar').style.width = "100%";
      }
    })


}
updateDistractionCount();
setInterval(updateDistractionCount,3000);
