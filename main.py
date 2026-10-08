import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.gemini import GeminiModel
import re
import requests
from bs4 import BeautifulSoup


resp = requests.get("https://www.infobae.com", timeout=15)

soup = BeautifulSoup(resp.text, "html.parser")


patron = re.compile(r"/\d{4}/\d{2}/\d{2}/")


notas = []
for a in soup.find_all("a", href=True):
    if patron.search(a["href"]):
        notas.append(a["href"])

print(len(notas))
for url in notas[:10]:
    print(url)



#load_dotenv()

#model = GeminiModel(
 #   client_args={"api_key": os.environ["GEMINI_API_KEY"]},
 #   model_id="gemini-3.6-flash"
#)

#agent = Agent(model=model)


