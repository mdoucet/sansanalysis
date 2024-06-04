# Django imports
from django.core.urlresolvers import reverse

def get_data_actions(iq_id):
    """
        Returns the data action for this django "application"
    """
    inversion_url = reverse('sansanalysis.simpleplot.views.invert', args=(iq_id,))
    inversion_title = 'Click to perform a P(r) inversion fit.'
    return {'name': 'Perform P(r) inversion',
                    'url': inversion_url,
                    'attrs': [{'name' : 'title',
                               'value': "\"%s\"" % inversion_title}]}

    
def get_recent_data_computations_by_iqdata(user_id, iq_id):
    """
        Returns the most recent P(r) inversions for the given data set and user
    """
    from view_util import get_recent_prfits_by_iqdata
    return get_recent_prfits_by_iqdata(user_id, iq_id)


def get_recent_data_computations_by_user(user_id):
    """
        Returns the most recent P(r) inversions for the given user
    """
    from view_util import get_recent_prfits_by_user
    return get_recent_prfits_by_user(user_id)