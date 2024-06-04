function get_pr_shared_key($, data_name, iq_id, pr_id) { 
	$.ajax({
	  url: '/analysis/'+iq_id+'/invert/'+pr_id+'/share',
	  cache: false,
	  success: function(xmldata){
	  	var key   = xmldata.getElementsByTagName("key");
	    var key_value = key[0].childNodes[0].nodeValue;
	    message = "To share your data, send the link below to the person your want to share the data with.<br><br><a href='"+key_value+"' target='_blank'>"+key_value+"</a><br><br>Note that only this particular data will be visible to the person receiving your link.";
		if (document.getElementById('share_pr_dialog')==null) {$("body").append("<div id='share_pr_dialog'> </div>");}
		document.getElementById('share_pr_dialog').innerHTML = message;
		$("#share_pr_dialog").dialog({ draggable: false, height: 200, modal: true, resizable: false, title: 'Share P(r) results for '+data_name });
		$("#share_pr_dialog").dialog('open');
	  }
	});
};      
      
function get_data_shared_key($, data_name, iq_id) { 
	$.ajax({
	  url: '/analysis/'+iq_id+'/share',
	  cache: false,
	  success: function(xmldata){
	  	var key   = xmldata.getElementsByTagName("key");
	    var key_value = key[0].childNodes[0].nodeValue;
	    message = "To share your data, send the link below to the person your want to share the data with.<br><br><a href='"+key_value+"' target='_blank'>"+key_value+"</a><br><br>Note that only this particular data will be visible to the person receiving your link.";
		if (document.getElementById('share_iq_dialog')==null) {$("body").append("<div id='share_iq_dialog'> </div>");}
		document.getElementById('share_iq_dialog').innerHTML = message;
		$("#share_iq_dialog").dialog({ draggable: false, height: 200, modal: true, resizable: false, title: 'Share '+data_name });
		$("#share_iq_dialog").dialog('open');
	  }
	});
};      

function get_help_dialog(url) {
	$.ajax({
	  url: url,
	  cache: false,
	  success: function(hlmldata){
		show_help_dialog(htmldata);
	  }
	});

}

function show_help_dialog(help_content) {
	if (document.getElementById('help_dialog')==null) {$("body").append("<div id='help_dialog'> </div>");}
	document.getElementById('help_dialog').innerHTML = help_content;
	$("#help_dialog").dialog({ draggable: false, modal: true, resizable: false, title: 'Help' });
	$("#help_dialog").dialog('option', 'buttons', 
	{
		Close: function() {
			$(this).dialog('close');
		}
	});
	$("#help_dialog").dialog('open');	
}