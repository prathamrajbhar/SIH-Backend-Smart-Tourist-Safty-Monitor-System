# API Test Report

**Date:** September 28, 2025  
**Version:** 3.0.0  
**Tester:** Automated Test Script

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {{ total_tests }} |
| Passed | {{ passed_tests }} |
| Failed | {{ failed_tests }} |
| Success Rate | {{ success_rate }}% |

## Endpoint Details

| Endpoint | Method | Status | Status Code | Response Time |
|----------|--------|--------|-------------|--------------|
{% for endpoint in endpoints %}
| {{ endpoint.path }} | {{ endpoint.method }} | {{ endpoint.status }} | {{ endpoint.status_code }} | {{ endpoint.response_time }}ms |
{% endfor %}

## Test Cases

{% for test in test_cases %}
### {{ test.name }}

- **Endpoint:** {{ test.endpoint }}
- **Method:** {{ test.method }}
- **Status:** {{ test.status }}
- **Response Code:** {{ test.status_code }}
- **Response Time:** {{ test.response_time }}ms

**Request:**
```json
{{ test.request }}
```

**Response:**
```json
{{ test.response }}
```

{% if test.error %}
**Error:**
```
{{ test.error }}
```
{% endif %}

{% endfor %}

## System Information

- **API Version:** {{ api_version }}
- **Database:** {{ database }}
- **Server:** {{ server }}

## Recommendations

{% for recommendation in recommendations %}
- {{ recommendation }}
{% endfor %}

## Conclusion

{{ conclusion }}