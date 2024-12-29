from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class RoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # List of URLs that don't need role checking
            exempt_urls = [
                reverse('logout'),
                reverse('login'),
            ]
            
            if request.path not in exempt_urls:
                if 'admin' in request.path and request.user.role != 'ADMIN':
                    messages.error(request, 'Access denied. Admin privileges required.')
                    return redirect('dashboard')
                elif 'miner' in request.path and request.user.role != 'MINER':
                    messages.error(request, 'Access denied. Miner privileges required.')
                    return redirect('dashboard')
                elif 'technical' in request.path and request.user.role != 'TECHNICAL':
                    messages.error(request, 'Access denied. Technical privileges required.')
                    return redirect('dashboard')
                
        return self.get_response(request)