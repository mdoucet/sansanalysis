/*
TODO: write the fit_problem data as a class
*/

function smearing_clicked(choice){
	switch(choice) {
	case 0:
		document.getElementById('smearing_params').innerHTML = "";
		window.fit_problem.smear_option_id = 0;
		window.fit_problem.smear_fixed = true;
		window.fit_problem.smear_model_id = 0;
		window.fit_problem.smear_pars = new Array();
		process_par_change();
		break;
	case 1:
		$.ajax({
			url: '/analysis/' + window.fit_problem.iq_id + '/smearing',
			cache: false,
			success: function(htmldata){
				document.getElementById('smearing_params').innerHTML = htmldata;
				window.fit_problem.smear_option_id = 1;
				window.fit_problem.smear_fixed = true;
				window.fit_problem.smear_model_id = 1;
				window.fit_problem.smear_pars = new Array();
				//process_par_change();
				update_smearing_parameter_list();

			}
		});
		document.getElementById('smearing_params').innerHTML = "";
		break;
	case 2:
		$.ajax({
			url: '/analysis/' + window.fit_problem.iq_id + '/smearing/?&type=point',
			cache: false,
			success: function(htmldata){
				window.fit_problem.smear_option_id = 2;
				window.fit_problem.smear_fixed = false;
				window.fit_problem.smear_model_id = 2;
				document.getElementById('smearing_params').innerHTML = htmldata;
				update_smearing_parameter_list();
			}
		});
		
		document.getElementById('smearing_params').innerHTML = "";
		break;
	case 3:
		$.ajax({
			url: '/analysis/' + window.fit_problem.iq_id + '/smearing/?&type=slit',
			cache: false,
			success: function(htmldata){
				window.fit_problem.smear_option_id = 3;
				window.fit_problem.smear_fixed = false;
				window.fit_problem.smear_model_id = 3;
				document.getElementById('smearing_params').innerHTML = htmldata;
				update_smearing_parameter_list();
			}
		});
		
		document.getElementById('smearing_params').innerHTML = "";
		break;
	}
}

function update_smearing_parameter_list() {
	var smear_name = '';
	if (document.getElementById("id_smear_type") != null) {
		smear_name = document.getElementById("id_smear_type").value;
	}
	$.ajax({
	  url: '/analysis/smearing/'+window.fit_problem.smear_model_id+'/parameters/?&fixed='+window.fit_problem.smear_fixed+'&id='+smear_name,
	  cache: false,
	  success: function(xmldata){
	  	window.fit_problem.smear_pars = new Array();
	  	var params = xmldata.getElementsByTagName("par");
		document.getElementById('model_pars_errors').innerHTML = "";
		if (params.length > 0) {
			for (i = 0; i < params.length; i++) {
				var html_name = params[i].childNodes[0].nodeValue;
				window.fit_problem.smear_pars[i] = html_name;
			}
			process_par_change();
		} else {
			var errs = xmldata.getElementsByTagName("error");
			var err_html = "";
			if (errs.length > 0) {
				err_html = "<div class='error'><ul class='errorlist'><li>"+errs[0].childNodes[0].nodeValue+"</li></ul></div>";
			}
			document.getElementById('model_pars_errors').innerHTML = err_html;
		}
		
	  }
	});
}

function process_par_change(){
	var params = "&model=" + window.fit_problem.model_id;
	document.getElementById('chi2').innerHTML = "";
	
	for (i = 0; i < window.fit_problem.model_pars.length; i++) {
		params = params + "&" + window.fit_problem.model_pars[i] + "=" + Number(document.getElementById("id_" + window.fit_problem.model_pars[i]).value);
		if (document.getElementById('id_err_' + window.fit_problem.model_pars[i]) != null) {
			document.getElementById('id_err_' + window.fit_problem.model_pars[i]).innerHTML = "<span class='spacer'></span>";
		};
			}
	
	// Q range
	params += "&q_min=" + Number(document.getElementById("id_q_min").value);
	params += "&q_max=" + Number(document.getElementById("id_q_max").value);
	
	// Smearing parameters
	if (document.getElementById("id_smear_type") != null) {
		params += "&smear_type=" + document.getElementById("id_smear_type").value;
	};

	params += "&smearing="+window.fit_problem.smear_option_id;
	//if (!window.fit_problem.smear_fixed) {
		for (i = 0; i < window.fit_problem.smear_pars.length; i++) {
			params = params + "&" + window.fit_problem.smear_pars[i] + "=" + Number(document.getElementById("id_" + window.fit_problem.smear_pars[i]).value);
			if (document.getElementById('id_err_' + window.fit_problem.smear_pars[i]) != null) {
				document.getElementById('id_err_' + window.fit_problem.smear_pars[i]).innerHTML = "<span class='spacer'></span>";
			};
		}
	//}
	
	$.ajax({
	  url: '/analysis/'+window.fit_problem.iq_id+'/model/'+window.fit_problem.model_id+'/?'+params,
	  cache: false,
	  success: function(xmldata){
	    	window.iq_calc = new Array();
	      	points=xmldata.getElementsByTagName("point");
	      	if (points.length>0) {
				  for (i=0;i<points.length;i++) {
				  	  var x = parseFloat(points[i].getElementsByTagName("x")[0].childNodes[0].nodeValue);
				  	  var y = parseFloat(points[i].getElementsByTagName("y")[0].childNodes[0].nodeValue);
					  window.iq_calc[i] = new Array(x,y,0,0,0);
				  }
				  document.getElementById('model_pars_errors').innerHTML = "";
			} else {
				var errs = xmldata.getElementsByTagName("error");
				var err_html = "";
				if (errs.length > 0) {
					err_html = "<div class='error'>"
					for (i = 0; i < errs.length; i++) {
						err_html += errs[i].getElementsByTagName("par")[0].childNodes[0].nodeValue;
						err_html += ":<ul class='errorlist'><li>"+errs[i].getElementsByTagName("value")[0].childNodes[0].nodeValue+"</li></ul>"
					}
					err_html += "</div>";
				}
				
				document.getElementById('model_pars_errors').innerHTML = err_html;
			};
			iq_plot();
	  }
	});
	
	
}

function show_parameters(){
	var model_id = document.getElementById('id_model').value;
	window.fit_problem.model_id = model_id;
	
	$.ajax({
		url: '/analysis/model/' + model_id + '/table',
		cache: false,
		success: function(htmldata){
			document.getElementById('parameters').innerHTML = htmldata;
			update_parameter_list();
		}
	});
}

function update_parameter_list() {
	$.ajax({
	  url: '/analysis/model/'+window.fit_problem.model_id+'/parameters',
	  cache: false,
	  success: function(xmldata){
	  	var model_list = xmldata.getElementsByTagName("model");
		if(model_list.length > 0) {
			var model_name = model_list[0].childNodes[0].nodeValue;
			document.getElementById('model_name').innerHTML = model_list[0].childNodes[0].nodeValue;
		}
		
		
	  	window.fit_problem.model_pars = new Array();
	  	var params = xmldata.getElementsByTagName("par");
		document.getElementById('model_pars_errors').innerHTML = "";
		if (params.length > 0) {
			for (i = 0; i < params.length; i++) {
				var html_name = params[i].childNodes[0].nodeValue;
				window.fit_problem.model_pars[i] = html_name;
			}
		} else {
			var errs = xmldata.getElementsByTagName("error");
			var err_html = "";
			if (errs.length > 0) {
				err_html = "<div class='error'><ul class='errorlist'><li>"+errs[0].childNodes[0].nodeValue+"</li></ul></div>";
			}
			document.getElementById('model_pars_errors').innerHTML = err_html;
		}
		process_par_change();
	  }
	});
}

function get_fit_shared_key(data_name, iq_id, fit_id) { 
	$.ajax({
	  url: '/analysis/'+iq_id+'/fit/'+fit_id+'/share',
	  cache: false,
	  success: function(xmldata){
	  	var key   = xmldata.getElementsByTagName("key");
	    var key_value = key[0].childNodes[0].nodeValue;
	    message = "To share your data, send the link below to the person your want to share the data with.<br><br><a href='"+key_value+"' target='_blank'>"+key_value+"</a><br><br>Note that only this particular data will be visible to the person receiving your link.";
		if (document.getElementById('share_fit_dialog')==null) {$("body").append("<div id='share_fit_dialog'> </div>");}
		document.getElementById('share_fit_dialog').innerHTML = message;
		$("#share_fit_dialog").dialog({ draggable: false, height: 200, modal: true, resizable: false, title: 'Share fit results for '+data_name });
		$("#share_fit_dialog").dialog('open');
	  }
	});
};  

function show_fit_model_dialog() {
	window.fit_problem.model_id_unconfirmed = window.fit_problem.model_id;
	$.ajax({
	  url: '/analysis/model/dialog',
	  cache: false,
	  success: function(hlmldata){
		if (document.getElementById('fit_model_dialog')==null) {$("body").append("<div id='fit_model_dialog'> </div>");}
		document.getElementById('fit_model_dialog').innerHTML = hlmldata;
		//$("#fit_model_dialog").dialog({ draggable: false, height: 300, modal: true, resizable: false, title: 'Select fit model' });
		$("#fit_model_dialog").dialog({ draggable: false, modal: true, resizable: false, title: 'Select fit model' });
		$("#fit_model_dialog").dialog('option', 'buttons', 
		{
			Cancel: function() {
				$(this).dialog('close');
			}
		});
		$("#fit_model_dialog").dialog('open');	
		$("#accordion").accordion();

	  }
	});
}

function select_fit_model(model_id) {
	document.getElementById('id_model').value = model_id;
	window.fit_problem.model_id = model_id;
	$("#fit_model_dialog").dialog('close');	
	show_parameters();
}



