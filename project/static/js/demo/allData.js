function allData() {
    const callbackData = $.get('/allData');
    callbackData.done(function (results) {
     document.getElementById('containerForStage').setAttribute('heat_map_data', JSON.stringify(results.data));
    })
}

setInterval(allData,2000);