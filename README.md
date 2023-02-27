# authentication-service

## Environment Details
- Python 3.9.10
- to install required libraries, run the cmd: `pip install -r requirements.txt`

## Running the server
run the cmd: `python -m flask run`

## Generate Certs
- `openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365`
