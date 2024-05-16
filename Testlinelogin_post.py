import requests

url = "http://127.0.0.1:8000/alpha/v1/Login/Oauth/Yahoo"
data = {
    "code": "200",
    "just_create": False,
    "alpha_advisor_id": None,
    "outer_advisor_id": None,
    "registration_source": None,
    "recommendation": None,
}

response = requests.post(url, json=data)
print(response.status_code)
print(response.json())


            # data={
            #     "client_id": self._client_id,
            #     "client_secret": self._client_secret,
            #     "code": code,
            #     "redirect_uri": self._redirect_uri,
            #     "grant_type": self._grant_type,
            # },