from django import forms
from django.http import HttpResponseRedirect, HttpResponse

# Application imports
from sansanalysis.commenting.models import Page, UserComment
from sansanalysis.settings import APP_VERSION

def post_comment(request):
    """
        Post a comment
    """   
    # Upload form
    if request.method == 'POST':
        user = request.user
        text = request.POST['text']
        
        # Store the page if needed
        url = request.POST['url']
        try:
            page = Page.objects.get(url=url)
        except Page.DoesNotExist:
            page = Page(url=url)
            page.save()
        
        # Store the comment
        comment = UserComment(user=user, text=text, is_comment=False, page_id=page.id, build=APP_VERSION)
        comment.save()

    return HttpResponse()

