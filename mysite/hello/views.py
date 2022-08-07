from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def myview(request):
    # use sessions
    num_visits = request.session.get('num_visits', 0) + 1
    
    request.session['num_visits'] = num_visits 
    
    if num_visits > 4 :
        del(request.session['num_visits'])
    
    response = HttpResponse('view count=' + str(num_visits))
    
    # use cookies
    response.set_cookie('dj4e_cookie', '3cb7e8f6', max_age=1000)
    
    return response