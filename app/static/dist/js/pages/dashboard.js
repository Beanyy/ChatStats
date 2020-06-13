/*
 * Author: Abdullah A Almsaeed
 * Date: 4 Jan 2014
 * Description:
 *      This is a demo file used only for the main dashboard (index.html)
 **/

/* global moment:false, Chart:false, Sparkline:false */

  function renderChart(canvas, data, labels) {
    var chartData = {
      labels: labels,
      datasets: [

        {
          label: 'Count',
          backgroundColor: 'rgba(60,141,188,0.9)',
          borderColor: 'rgba(60,141,188,0.8)',
          pointRadius: false,
          pointColor: '#3b8bba',
          pointStrokeColor: 'rgba(60,141,188,1)',
          pointHighlightFill: '#fff',
          pointHighlightStroke: 'rgba(60,141,188,1)',
          data: data
        }
      ]
    }
  
    var chartOptions = {
      maintainAspectRatio: false,
      responsive: true,
      legend: {
        display: false
      },
      scales: {
        xAxes: [{
          gridLines: {
            display: false
          }
        }],
        yAxes: [{
          gridLines: {
            display: false
          }
        }]
      }
    }
  
    // This will get the first returned node in the jQuery collection.
    // eslint-disable-next-line no-unused-vars
    var salesChart = new Chart(canvas, {
      type: 'bar',
      data: chartData,
      options: chartOptions
    })
  }
  function getChartData(canvasDiv, userId, chartType) {
    url = (userId > 0) ? userChartDataURL(userId, chartType) : channelChartDataURL(chartType)
    $.ajax({
        url: url,
        success: function (result) {
          var data = [];
          var labels = [];
          $.each(result, function(index,item) {
            data.push(item.data);       
            labels.push(item.label);       
          });
          canvasDiv.find('img').hide()
          renderChart(canvasDiv.find('canvas')[0].getContext('2d'), data, labels);
        },
    });
  }

  function channelChartDataURL(chartType) {
      return "/" + activeType + "/" + activeId + "/_chart/" + chartType
  }
  function userChartDataURL(userId, chartType) {
    return "/" + activeType + "/" + activeId + "/_user_chart/" + userId + "/" + chartType
  }
  function userWordDataURL(userId, chartType) {
    return "/" + activeType + "/" + activeId + "/_user_words/" + userId + "/" + chartType
  }

  var itemsPerPage = 10
  function getWordData(table, userId, chartType) {
    $.ajax({
        url: userWordDataURL(userId, chartType),
        success: function (result) {
          $.each(result, function(index,item) {
              var myUrl = ['/messages', 'search', activeType, activeId, userId, item.label.replace("#", "HASHTAG")].join('/')
              var entry = $('<tr>').append(
                $('<td>').append($('<a>').attr("href", myUrl).text(item.label)),
                $('<td>').text(item.data),
              ).appendTo(table);  
          });
          setTimeout(function () {
              var catagory = table.attr("id").split("-")[0]
              var userName = table.attr("id").split("-")[1]
              $("#" + catagory + "-holder-" + userName).jPages({
                containerID : table.attr("id"),
                perPage : itemsPerPage,
                delay : 0
              });
            }, 500)
        }
    });
  }

$(function () {
  $(".usertab").click(function() {
    var userName = $(this).attr("id").split("-")[2];
    var userId = userIds[userName];

    $(".wordTable-" + userName).each(function(){
      var chartType = parseInt($(this).attr("id").split("-")[2]);
      getWordData($(this).empty(), userId, chartType)
    })

    $(".chart-user-" + userName).each(function(){
      var chartType = parseInt($(this).data("charttype"));
      getChartData($(this), userId, chartType)
    })
  });

  $(".table-search").on("input", function() {
    var userName = $(this).attr("id").split("-")[2];
    var catagory = $(this).attr("id").split("-")[0];
    var val = $(this).val()
    var page = 0
    $(".search-success").removeClass("search-success")
    $("#" + $(this).attr("id").replace('search-', '') + ' > tr > td:first-child').each(function(index) {
       if ($(this).text() == val) {
        $(this).parent().addClass("search-success")
        return page = (index/itemsPerPage + 1)
       }
    });
    if (page > 0) {
      $("#" + catagory + "-holder-" + userName).jPages(Math.floor(page))
      $(this).css("background-color", "#d6ffdb")
    } else {
      $(this).css("background-color", "#ffd6d6")
    }
  });

  $(".chart-channel-nav").click(function() {
    var linkDiv = $($(this).attr("href"))
    var chartType = parseInt($(linkDiv).data("charttype"));
    getChartData(linkDiv, -1, chartType)
  })

  /* initiate plugin */
  $("div.imglist-holder").each(function(index) {
    var userName = $(this).attr("id").split("-")[2];
    $(this).jPages({
      containerID : "imglist-" + userName,
      animation   : "fadeInUp",
      perPage     : 10,
    });
  })
  
  lazyload();
  $( ".chart-channel-nav.active").trigger( "click" );
  $( ".usertab.active").trigger( "click" );
})
  /* Chart.js Charts */
