
# Application imports
import sansanalysis.settings as settings

def get_data_actions(iq_id):
    """
        Returns all registered data action
    """
    actions = []
    for item in settings.INSTALLED_APPS:
        if item.startswith('sansanalysis'):
            exec "import %s" % item
            exec "has_actions = hasattr(%s, 'get_data_actions')" % item
            if has_actions:
                exec "actions.append(%s.get_data_actions(iq_id))" % item

    # Sort all items by alphabetically
    def _compare(x, y):
        if   x['name']>y['name']: return -1
        elif x['name']<y['name']: return 1
    actions = sorted(actions, _compare )
                
                
    return actions
    
def get_recent_data_computations_by_iqdata(user_id, iq_id):
    """
        Returns recent data computations from all registered apps 
    """
    recent = []
    for item in settings.INSTALLED_APPS:
        if item.startswith('sansanalysis'):
            exec "import %s" % item
            exec "has_recent = hasattr(%s, 'get_recent_data_computations_by_iqdata')" % item
            if has_recent:
                exec "recent.extend(%s.get_recent_data_computations_by_iqdata(user_id, iq_id))" % item
        
    # Sort all items by chronologically
    def _compare(x, y):
        if   x['time']>y['time']: return -1
        elif x['time']<y['time']: return 1
    recent = sorted(recent, _compare )
    
    # Take the top 5 items
    if len(recent)>5:
        return recent[:5]
    
    return recent


def get_recent_data_computations_by_user(user_id):
    """
        Returns recent data computation for a given user
    """
    recent = []
    for item in settings.INSTALLED_APPS:
        if item.startswith('sansanalysis'):
            exec "import %s" % item
            exec "has_recent = hasattr(%s, 'get_recent_data_computations_by_user')" % item
            if has_recent:
                exec "recent.extend(%s.get_recent_data_computations_by_user(user_id))" % item
        
    # Sort all items by chronologically
    def _compare(x, y):
        if   x['time']>y['time']: return -1
        elif x['time']<y['time']: return 1
    recent = sorted(recent, _compare )
    
    # Take the top 5 items
    if len(recent)>5:
        return recent[:5]
    
    return recent
