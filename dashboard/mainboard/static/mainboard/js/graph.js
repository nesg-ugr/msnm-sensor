function set_current_datetime() {
    var currentdate = new Date();
    var datetime = addZero(currentdate.getDate()) + "/"
                    + addZero((currentdate.getMonth()+1))  + "/"
                    + currentdate.getFullYear() + " - "
                    + addZero(currentdate.getHours()) + ":"
                    + addZero(currentdate.getMinutes()) + ":"
                    + addZero(currentdate.getSeconds());
    for(var key in $interval_id) {
        $("#last_updated_" + key).html('<br/>Last sync: ' + datetime);
    }
}

function reload_graphs(sid=null) {
    if ($selected_sid !== '') {
        if (sid) {
            var url = $url.replace('none', sid);
            generate_router_graph(url, sid);
        }
        else {
            for (key in $interval_id) {
                var url = $url.replace('none', key);
                generate_router_graph(url, key);
            }
        }
    }
}


function generate_graph(div_id, data, layout) {
    var d3 = Plotly.d3;
    var gd3 = d3.select('#' + div_id);
    var gd = gd3.node();
    Plotly.newPlot(gd, data, layout, {responsive: true});
}

function generate_router_graph(url, sid) {
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
                },
                modebar: {
                    orientation: 'v',
                    bgcolor: 'rgba(255 ,255 ,255 ,0.7)',
                    iconColor: 'rgba(0, 31, 95, 0.3);'
                },
            };
            set_current_datetime();
            var graph = $("#graph" + sid);
            graph.html('');
            generate_graph('graph' + sid, data, layout);
            graph.parent().children(".last_updated").show();
            if (graph.parent().children(".resume_sync").is(":hidden")) {
                graph.parent().children(".pause_sync").show();
            }
            if (graph.parent().children(".compress_graph").is(":hidden")) {
                graph.parent().children(".expand_graph").show();
                if ( graph.parent().children(".close_graph").length) {
                    graph.parent().children(".close_graph").show();
                }
            }
            $token_loader = null;
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $("#graph" + sid).html('<br/><br/>Unable to load');
            var err = xhr.responseText;
            console.log(err);
        }
    });
}

$(document).ready(function() {
    var $interval = 1000 * $sync_seconds;
    $(".pause_sync").on("click", function() {
        $(this).hide();
        var graph_side = $(this).parent();
        graph_side.children(".resume_sync").show();
        $sid = graph_side.children(".graph").prop('id').replace('graph', '');
        if ($interval_id) {
            window.clearInterval($interval_id[$sid]);
            delete $interval_id[$sid];
        }
    });
    $(".resume_sync").on("click", function() {
        $(this).hide();
        var graph_side = $(this).parent();
        graph_side.children(".pause_sync").show();
        $sid = graph_side.children(".graph").prop('id').replace('graph', '');
        $interval_id[$sid] = window.setInterval(reload_graphs, $interval);
    });
    $(".expand_graph").on("click", function() {
        $("body").children().each(function() {
            $(this).hide();
        });
        var graph_side = $(this).parents(".graph-container");
        graph_side.children(".close_graph").hide();
        graph_side.css("width", '100%');
        graph_side.css("height", '100%');
        graph_side.css("position", 'absolute');
        graph_side.css("top", '0');
        graph_side.css("left", '0');
        graph_side.css("padding", '20px');
        if (graph_side.hasClass("col-sm-6")) {
            $col_class = "col-sm-6";
            graph_side.removeClass('col-sm-6');
        }
        else {
            $col_class = "col-sm-4";
            graph_side.removeClass('col-sm-4');
        }
        graph_side.detach().appendTo("body");
        reload_graphs($sid);
        $("body").css("background-color", "white");
        $(this).hide();
        graph_side.children(".compress_graph").show();
    });
    $(".compress_graph").on("click", function() {
        $("body").children().each(function() {
            $(this).show();
        });
        var graph_side = $(this).parents(".graph-container");
        graph_side.css("width", 'auto');
        graph_side.css("height", 'auto');
        graph_side.css("position", 'relative');
        graph_side.css("padding", '10px 15px');
        graph_side.addClass($col_class);
        graph_side.detach().appendTo("#routers_and_graph");
        reload_graphs($sid);
        $("body").css("background", "rgba(46, 53, 61, 0.6) no-repeat fixed");
        $(this).hide();
        graph_side.children(".expand_graph").show();
        graph_side.children(".close_graph").show();
    });

    $("#hide-network").on("click", function() {
        $("#network-container").slideToggle();
        var arrow = $("#arrow-hide");
        if (arrow.hasClass("fa-angle-up")) {
            arrow.removeClass("fa-angle-up");
            arrow.addClass("fa-angle-down");
        }
        else {
            arrow.removeClass("fa-angle-down");
            arrow.addClass("fa-angle-up");
        }
    });
});

function addZero(i) {
    if (i < 10) {
        i = "0" + i;
    }
    return i;
}

