from flask import Blueprint, request
from constants import api_constants
try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

district_service = Blueprint("district_page", __name__, template_folder="templates")

@district_service.route('/get-district/postal-code/<postalCode>', methods = ["GET"])
def getDistrictFromPostalCode(postalCode):
    """
    Returns the district that the postal code is in
    """
    if request.method == "GET":
        if len(postalCode) != 6 or " " in postalCode:

            return {"error": "Invalid input. Please enter a postal code in the following format A1B2C3."}, 400
    
    
        url = api_constants.ELECTIONS_CANADA_ELECTORAL_DISTRICTS_API_URL + postalCode
        html_text = requests.get(url).text
        print(html_text)
        soup = BeautifulSoup(html_text, 'html.parser')
  
        info = soup.body.find('div', attrs={'class':'col2'})

        # TODO: need to handle case where the HTML page returned does not contain a riding (ex. the postal code entered was invalid)
        if info != None:
            info = info.findAll('div', attrs={'class':'electiondays'})
        else:
            return {"error": "Invalid postal code. Please enter a valid postal code in the following format A1B2C3."}, 400
  
        #print(info)
  
        constituencyInfo = info[0]
        MPinfo = info[1]
                
        # print(constituencyInfo.text)
        for line in constituencyInfo.text.split("\n"):
            #print(line)
            if "Name" in line:
                print("riding is: " + line.split(":")[1].strip())
                break
        
        # print(MPinfo)
        MPinfo = MPinfo.text.split("\n")
        for i in range(len(MPinfo)):
            if i == 2:
                print("your MP's name is: " + MPinfo[i])
                break