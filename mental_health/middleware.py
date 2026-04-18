import json
import logging

logger = logging.getLogger(__name__)

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            print("=== API REQUEST ===")
            print(f"Path: {request.path}")
            print(f"Method: {request.method}")
            print(f"Headers: {dict(request.headers)}")
            
            if request.body:
                try:
                    body_str = request.body.decode('utf-8')
                    print(f"Body: {body_str}")
                    if body_str:
                        try:
                            body_data = json.loads(body_str)
                            print(f"Parsed JSON: {body_data}")
                        except json.JSONDecodeError:
                            print("Body is not JSON")
                except Exception as e:
                    print(f"Error reading body: {e}")
        
        response = self.get_response(request)
        
        if request.path.startswith('/api/'):
            print(f"Response Status: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Response Data: {response.data}")
            print("=== END REQUEST ===\n")
        
        return response