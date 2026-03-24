import urllib.request
import json
import base64

url = 'http://localhost:8080/api/employees/register'
data = {
    'empno': 'EMP123', 'name': 'Test', 'dept': 'HR', 'designation': 'MGR',
    'bankName': 'Chase', 'accountNo': '123', 'basicSalary': 1000,
    'hra': 100, 'conveyance': 10, 'medical': 0, 'special': 0,
    'grossSalary': 1110, 'epf': 0, 'healthInsurance': 0, 'professionalTax': 0,
    'tds': 0, 'totalDeductions': 0, 'netPay': 1110, 'totalDays': 30,
    'presentDays': 30, 'absentDays': 0, 'month': 10, 'year': 2023
}
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + base64.b64encode(b"admin:admin").decode('ascii')
}

try:
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.read().decode('utf-8'))
except Exception as e:
    print("Other Error:", e)
