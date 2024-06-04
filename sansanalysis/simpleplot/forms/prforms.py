from django import forms

class FormattedInput(forms.TextInput):
     input_type = 'text'
 
     def __init__(self, *args, **kwargs):
         super(FormattedInput, self).__init__(*args, **kwargs)
 
     def render(self, name, value, attrs=None):
         
         try:
             formatted_value = "%g" % value
         except:
             formatted_value = value
         return super(FormattedInput, self).render(name, formatted_value, attrs)
     
class PrForm(forms.Form):
    ## If True, the background level will be a floating parameter in the fit
    has_bck     = forms.BooleanField(required=False)
    
    ## Slit height
    slit_height = forms.FloatField(required=False, 
                                   widget=forms.TextInput(attrs={'title':"Beam slit height in units of Q",
                                                                 'onchange':"get_estimates()"}))
    ## Slit width
    slit_width  = forms.FloatField(required=False, widget=forms.TextInput(attrs={'title':"Beam slit width in units of Q",
                                                                                 'onchange':"get_estimates()"}))

    ## Number of terms in the expansion
    #TODO: set min_value and max_value
    n_terms     = forms.IntegerField(widget=forms.TextInput(attrs={'title':"Number of terms in the expansion of P(r)"}))
    ## Regularization paraemter
    alpha       = forms.FloatField(widget=FormattedInput(attrs={'title':"Enter a value for the regularization term"}))
    ## Max distance
    d_max       = forms.FloatField(widget=forms.TextInput(attrs={'title':"D_max is the largest distance between two points in the sample",
                                                                 'onchange':"get_estimates()"}))
    
    # Minimum Q-value
    q_min       = forms.FloatField(required=False, widget=forms.TextInput(attrs={'title':"Minimum Q-value of the data used in the inversion",
                                                                                 'onchange':"get_estimates()"}))
    # Maximum Q-value
    q_max       = forms.FloatField(required=False, widget=forms.TextInput(attrs={'title':"Maximum Q-value of the data used in the inversion",
                                                                                 'onchange':"get_estimates()"})) 
    