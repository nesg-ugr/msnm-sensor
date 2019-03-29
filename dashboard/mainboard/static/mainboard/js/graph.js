function set_current_datetime() {
    var currentdate = new Date();
    var datetime = addZero(currentdate.getDate()) + "/"
                    + addZero((currentdate.getMonth()+1))  + "/"
                    + currentdate.getFullYear() + " - "
                    + addZero(currentdate.getHours()) + ":"
                    + addZero(currentdate.getMinutes()) + ":"
                    + addZero(currentdate.getSeconds());
    $(".last_updated").html('<br/>Last sync: ' + datetime);
}

function reload_graphs() {
    if ($selected_sid !== '') {
        var url = $url.replace('none', $selected_sid);
        generate_router_graph(url);
    }
}


function generate_graph(div_id, data, layout) {
    var d3 = Plotly.d3;
    var gd3 = d3.select('#' + div_id);
    var gd = gd3.node();
    Plotly.newPlot(gd, data, layout, {responsive: true});
}

function generate_router_graph(url) {
    $.ajax({
        type: "GET",
        url: url,
        cache: false,
        processData: false,
        contentType: false,
        async: true,
        beforeSend: function () {},
        success: function (out, ajaxOptions, thrownError) {
            var qst = {
                x: out.ts,
                y: out.Qst,
                type: 'scatter',
                name: 'Qst',
                mode: 'markers',
            };
            var dst = {
                x: out.ts,
                y: out.Dst,
                type: 'scatter',
                name: 'Dst',
                mode: 'markers',
            };
            var uclq = {
                x: out.ts,
                y: out.UCLq,
                type: 'scatter',
                name: 'UCLq',
                mode: 'lines',
            };
            var ucld = {
                x: out.ts,
                y: out.UCLd,
                type: 'scatter',
                name: 'UCLd',
                mode: 'lines',
            };
            var data = [qst, dst, uclq, ucld];
            var layout = {
                titlefont: {"size": 14,},
                title: '<b>' + out.sid + ' graph</b>',
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                yaxis: {
                    type: 'log',
                    autorange: true,
                }
            };
            set_current_datetime();
            $("#graph1").html('');
            generate_graph('graph1', data, layout);
            $(".last_updated").show();
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $("#graph1").html('Unable to load');
            var err = xhr.responseText;
            console.log(err);
        }
    });
}

var $selected_sid = '';
var $interval_id = null;

$(document).ready(function() {
    var $interval = 1000 * $sync_seconds;
    $(".router").on("click", function(){
        var sid = $(this).attr('id');
        $("#graph1").show();
        if ($selected_sid !== sid) {
            $("#graph1").html('<img style="position: relative; top: 180px; width: 20%;" src="' + $loading_url + '">');
            $(".last_updated").hide();
            $("#pause_sync").hide();
            $("#resume_sync").hide();
            $("#expand_graph").hide();
            $("#compress_graph").hide();
            $selected_sid = sid;
        }
        setTimeout(function() {
            var url = $url.replace('none', sid);
            generate_router_graph(url);
        }, 500);
        $("#pause_sync").show();
        $("#expand_graph").show();
        window.clearInterval($interval_id);
        $interval_id = window.setInterval(reload_graphs, $interval);
    });
    $("#pause_sync").on("click", function() {
        $(this).hide();
        $("#resume_sync").show();
        window.clearInterval($interval_id);
    });
    $("#resume_sync").on("click", function() {
        $(this).hide();
        $("#pause_sync").show();
        $interval_id = window.setInterval(reload_graphs, $interval);
    });
    $("#expand_graph").on("click", function() {
        $("body").children().each(function() {
            $(this).hide();
        });
        var graph_side = $("#graph_side");
        graph_side.css("width", '100%');
        graph_side.css("height", '100%');
        graph_side.css("position", 'absolute');
        graph_side.css("top", '0');
        graph_side.css("left", '0');
        graph_side.removeClass('col-sm-6');
        graph_side.detach().appendTo("body");
        reload_graphs();
        $("body").css("background-color", "white");
        $(this).hide();
        $("#compress_graph").show();
    });
    $("#compress_graph").on("click", function() {
        $("body").children().each(function() {
            $(this).show();
        });
        var graph_side = $("#graph_side");
        graph_side.css("width", 'auto');
        graph_side.css("height", 'auto');
        graph_side.css("position", 'relative');
        graph_side.addClass('col-sm-6');
        graph_side.detach().appendTo("#routers_and_graph");
        reload_graphs();
        $("body").css("background", "rgba(46, 53, 61, 0.6) no-repeat fixed");
        $(this).hide();
        $("#expand_graph").show();
    });
});

function addZero(i) {
    if (i < 10) {
        i = "0" + i;
    }
    return i;
}

