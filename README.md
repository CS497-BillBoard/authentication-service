# authentication-service
This backend service was made as part of our project for CS 497 (Special Topics in CS - CS capstone). The code for the React Native front-end can be found [here](https://github.com/CS497-BillBoard/frontend).

## Environment Details
- Python 3.9.10
- to install required libraries, run the cmd: `pip install -r requirements.txt`

## Running the server
run the cmd: `python main.py`

as a sanity check, you can visit `http://localhost:5000/bills` (or the url displayed in your terminal) on your web browser to check its running. The page
should say `Hello, World!`

## Generate Certs
- `openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365`

