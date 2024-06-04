
function create_plot($, id, scale, data, options) {

	var placeholder = $('#'+id);

	if (options==null) {
		var options = {
			               series: {
			                   lines: { show: true },
			                   points: { show: true },
			                   shadowSize: 0
			               },
			               grid: { hoverable: true, clickable: false },
			               zoom: {
			                   interactive: true,
			                   amount: 1.05
			               },
			               pan: {
			                   interactive: true
			               },
			               yaxis : {
			               			tickFormatter: gettick
			               },
			               legend: {
			               		margin: [10,10]
			               }
			               
			          };
	};   

    var plot = $.plot($('#'+id), data, options);

 	function gettick(val) {
 		return val.toPrecision(3);
 	}
 
    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }


    var previousPoint = null;
	function plothover(event, pos, item) {
    	if (scale=='linear'){
        	$("#x").text(pos.x.toPrecision(3));
        	$("#y").text(pos.y.toPrecision(3));
        } else {
        	$("#x").text(Math.pow(10,pos.x).toPrecision(3));
        	$("#y").text(Math.pow(10,pos.y).toPrecision(3));        
        };

        if (item) {
            if (previousPoint != item.datapoint) {
                previousPoint = item.datapoint;
                
                $("#tooltip").remove();
                var x = item.datapoint[0].toPrecision(3);
                var y = item.datapoint[1];
                
                if (scale=='linear'){
                	showTooltip(item.pageX, item.pageY,
                            item.series.label + " of " + x + " = " + y.toPrecision(3));
				} else {
                	showTooltip(item.pageX, item.pageY,
                            item.series.label + " of " + x + " = " + Math.pow(10,y).toPrecision(3));
                };

            }
        }
        else {
            $("#tooltip").remove();
            previousPoint = null;            
        }
    }    
    $('#'+id).bind("plothover", plothover);
    

};

function create_plot_new($, id, data, options, xlabel, point_hover) {

	var placeholder = $('#'+id);

	if (options==null) {
		var options = {
			               series: {
			                   lines: { show: true },
			                   points: { show: true },
			                   shadowSize: 0
			               },
			               grid: { hoverable: true, clickable: false },
			               zoom: {
			                   interactive: true,
			                   amount: 1.05
			               },
			               pan: {
			                   interactive: true
			               },
			               yaxis : {
			               			tickFormatter: gettick
			               },
			               legend: {
			               		margin: [10,10]
			               }
			               
			          };
	};   
	
	if (options.yaxis.ticks==null) {
		options.yaxis.tickFormatter = gettick;
	}

    var plot = $.plot($('#'+id), data, options);

 	function gettick(val) {
 		return val.toPrecision(3);
 	}
 
    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #ddd',
            padding: '2px',
            'background-color': '#eee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }


    var previousPoint = null;
	function plothover(event, pos, item) {
    	
        if (item) {
            if (previousPoint != item.datapoint) {
                previousPoint = item.datapoint;
                
                $("#tooltip").remove();
                var _x = item.datapoint[0];
                var _y = item.datapoint[1];
                var x = _x.toPrecision(3);
                var y = _y.toPrecision(3);
                
                if (options.app_options != null && options.app_options.scale_x=='linear' && options.app_options.scale_y=='log') {
                	y = Math.pow(10,_y).toPrecision(3);
                } else if (options.app_options != null && options.app_options.scale_x=='log' && options.app_options.scale_y=='linear') {
                	x = Math.pow(10,_x).toPrecision(3);
                } else if (options.app_options != null && options.app_options.scale_x=='log' && options.app_options.scale_y=='log') {
                	x = Math.pow(10,_x).toPrecision(3);
                	y = Math.pow(10,_y).toPrecision(3);
                }
                showTooltip(item.pageX, item.pageY,
                            item.series.label + " of " + x + " = " + y);
            }
        }
        else {
            $("#tooltip").remove();
            previousPoint = null;            
        }
    }    
    $('#'+id).bind("plothover", plothover);

	if (xlabel!=null){
		value = '<div id="x_label">'+xlabel+'</div>';
    	$(value).appendTo(placeholder);
	};


    // add zoom buttons 
    $('<img class="button" src="/media/zoom_out.png" style="right:-15px;top:35px" title="click to zoom out">').appendTo(placeholder).click(function (e) {
        e.preventDefault();
        plot.zoomOut();
    });
    $('<img class="button" src="/media/zoom_in.png" style="right:-15px;top:10px" title="Click to zoom in">').appendTo(placeholder).click(function (e) {
        e.preventDefault();
        plot.zoom();
    });

    // and add panning buttons
    
    // little helper for taking the repetitive work out of placing
    // panning arrows
    function addArrow(dir, right, top, offset) {
        $('<img class="button" src="/media/arrow_' + dir + '.png" style="right:' + right + 'px;top:' + top + 'px" title="Click to move '+ dir +'"/>').appendTo(placeholder).click(function (e) {
            e.preventDefault();
            plot.pan(offset);
        });
    }

    addArrow('left',  -5, 70, { left: -10 });
    addArrow('right', -16, 70, { left: 10 });
    addArrow('up',    -14, 100, { top: -10 });
    addArrow('down',  -14, 111, { top: 10 });
    
    
};