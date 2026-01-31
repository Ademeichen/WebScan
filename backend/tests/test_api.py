import requests

response = requests.get('http://127.0.0.1:3000/api/kb/vulnerabilities?page=1&page_size=10')
print(f'Status Code: {response.status_code}')
print(f'Response: {response.text}')