from django.http import JsonResponse
def request_verification(_): return JsonResponse({'status': 'requested'})
