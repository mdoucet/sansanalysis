/*
Simple OpenID Plugin
http://code.google.com/p/openid-selector/

This code is licenced under the New BSD License.
*/

var providers_large = {
    google: {
        name: 'Google',
        url: 'https://www.google.com/accounts/o8/id'
    },
    yahoo: {
        name: 'Yahoo',      
        url: 'http://yahoo.com/'
    },    
    openid: {
        name: 'OpenID',     
        label: 'Enter your OpenID.',
        url: null
    }
};
var providers_small = {
};
var providers = $.extend({}, providers_large, providers_small);

var openid = {

	cookie_expires: 6*30,	// 6 months.
	cookie_name: 'openid_provider',
	cookie_path: '/',
	
	// Modified to point to the right location
	img_path: '/media/thirdparty/openid-selector/images/',
	
	input_id: null,
	provider_url: null,
	
    init: function(input_id) {
        
        var openid_btns = $('#openid_btns');
        
        this.input_id = input_id;
        
        $('#openid_choice').show();
        $('#openid_input_area').empty();
        
        // add box for each provider
        for (id in providers_large) {
        
           	openid_btns.append(this.getBoxHTML(providers_large[id], 'large', '.gif'));
        }
        if (providers_small) {
        	openid_btns.append('<br/>');
        	
	        for (id in providers_small) {
	        
	           	openid_btns.append(this.getBoxHTML(providers_small[id], 'small', '.ico'));
	        }
        }
        
        $('#openid_form').submit(this.submit);
        
        //var box_id = this.readCookie();
        //if (box_id) {
        //	this.signin(box_id, true);
        //}  
    },
    getBoxHTML: function(provider, box_size, image_ext) {
            
        var box_id = provider["name"].toLowerCase();
        return '<a title="'+provider["name"]+'" href="javascript: openid.signin(\''+ box_id +'\');"' +
        		' style="background: #FFF url(' + this.img_path + box_id + image_ext+') no-repeat center center" ' + 
        		'class="' + box_id + ' openid_' + box_size + '_btn"></a>';    
    
    },
    /* Provider image click */
    signin: function(box_id, onload) {
    
    	var provider = providers[box_id];
  		if (! provider) {
  			return;
  		}
		
		this.highlight(box_id);
		this.setCookie(box_id);
		
		// prompt user for input?
		if (provider['label']) {
			
			this.useInputBox(provider);
			this.provider_url = provider['url'];
			
		} else {
			this.setOpenIdUrl(provider['url']);
			if (! onload) {
				$('#openid_form').submit();
			}	
		}
    },
    /* Sign-in button click */
    submit: function() {
        
    	var url = openid.provider_url; 
    	if (url) {
    		url = url.replace('{username}', $('#openid_username').val());
    		openid.setOpenIdUrl(url);
    	}
    	return true;
    },
    setOpenIdUrl: function (url) {
    
    	var hidden = $('#'+this.input_id);
    	if (hidden.length > 0) {
    		hidden.value = url;
    	} else {
    		$('#openid_form').append('<input type="hidden" id="' + this.input_id + '" name="' + this.input_id + '" value="'+url+'"/>');
    	}
    },
    highlight: function (box_id) {
    	
    	// remove previous highlight.
    	var highlight = $('#openid_highlight');
    	if (highlight) {
    		highlight.replaceWith($('#openid_highlight a')[0]);
    	}
    	// add new highlight.
    	$('.'+box_id).wrap('<div id="openid_highlight"></div>');
    },
    setCookie: function (value) {
    
		var date = new Date();
		date.setTime(date.getTime()+(this.cookie_expires*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
		
		document.cookie = this.cookie_name+"="+value+expires+"; path=" + this.cookie_path;
    },
    readCookie: function () {
		var nameEQ = this.cookie_name + "=";
		var ca = document.cookie.split(';');
		for(var i=0;i < ca.length;i++) {
			var c = ca[i];
			while (c.charAt(0)==' ') c = c.substring(1,c.length);
			if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
		}
		return null;
    },
    useInputBox: function (provider) {
   	
		var input_area = $('#openid_input_area');
		
		var html = '';
		var id = 'openid_username';
		var value = '';
		var label = provider['label'];
		var style = '';
		
		if (label) {
			html = '<p>' + label + '</p>';
		}
		if (provider['name'] == 'OpenID') {
			id = this.input_id;
			value = 'http://';
			style = 'background:#FFF url('+this.img_path+'openid-inputicon.gif) no-repeat scroll 0 50%; padding-left:18px;';
		}
		html += '<input id="'+id+'" type="text" style="'+style+'" name="'+id+'" value="'+value+'" />' + 
					'<input id="openid_submit" type="submit" value="Sign-In"/>';
		
		input_area.empty();
		input_area.append(html);

		$('#'+id).focus();
    }
};
