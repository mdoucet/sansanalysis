# Django imports
from django.core.urlresolvers import reverse

def get_data_actions(iq_id):
    inversion_url = reverse('sansanalysis.modeling.views.fit', args=(iq_id,))
    inversion_title = 'Click to fit this data to theoritical models.'
    return {'name': 'Perform modeling fit',
                    'url': inversion_url,
                    'attrs': [{'name' : 'title',
                               'value': "\"%s\"" % inversion_title}]}
    
def get_recent_data_computations_by_iqdata(user_id, iq_id):
    """
        Get latest five data sets visited by the user
        
        Make sure that all links are available and that the user
        is either the owner of the file or has access through
        a stored link.
        
        @param user_id: user id
        @param iq_id: IqData ojbect PK
    """
    from data_manipulations import get_recent_fits_by_iqdata
    return get_recent_fits_by_iqdata(user_id, iq_id)

def get_recent_data_computations_by_user(user_id):
    """
        Get latest five data sets visited by the user
        
        Make sure that all links are available and that the user
        is either the owner of the file or has access through
        a stored link.
        
        @param user_id: user id
    """
    from data_manipulations import get_recent_fits_by_user
    return get_recent_fits_by_user(user_id)
          