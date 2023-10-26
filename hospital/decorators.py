import functools
from django.shortcuts import redirect
from django.contrib import messages

def authentication_required(view_func):
    @functools.wraps(view_func)
    def  wrapper(request, *args, **kwargs):
        if request.session.get('login'):
            messages.error(request, 'You are already logged in')
            if request.session.get('pacient') == True:
                return redirect('/pacient')
            elif request.session.get('metge') == True:
                return redirect('/metge')
            else:
                return redirect('/rol')
        else:
            redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper