import urllib3
import urllib.parse
from bs4 import BeautifulSoup
import os
from google.cloud import translate

# feature toggle
USE_GOOGLE_TRANSLATION_API_FOR_FREE = True

OUTPUT_FILE = "data.html"
url = "https://spaceflightnow.com/launch-schedule/"

def scrape_site_and_write_output():

    http = urllib3.PoolManager(timeout=1.0)
    r = http.request('GET', url)
    data = r.data

    soup = BeautifulSoup(data, "html.parser")

    when = soup.find("span", {"class": "launchdate"}).contents[0].strip()
    rocket = soup.find("span", {"class": "mission"}).contents[0].split("•")[0].strip()
    payload = soup.find("span", {"class": "mission"}).contents[0].split("•")[1].strip()

    launch_window = soup.find("div", {"class": "missiondata"}).contents[1].strip()
    where = soup.find("div", {"class": "missiondata"}).contents[3].strip()
    information = soup.find("div", {"class": "missdescrip"}).contents[0].strip()
    # remove trailing "[" if present
    if information[-1:] == "[":
        information = information[:-1].strip()
    information_de = translate_en_to_de(information).strip()
    when_de = translate_en_to_de(when).strip()

    # write a plain string, separator is "|"
    with open(OUTPUT_FILE, 'w') as file:
        file.write(when + "|" + rocket + "|" + payload + "|" + launch_window + "|" + where + "|" + information + "|" + information_de + "|" + when_de)

def translate_en_to_de(str):

    if USE_GOOGLE_TRANSLATION_API_FOR_FREE:

        # append string to url
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=de&dt=t&q=" + urllib.parse.quote(str);

        http = urllib3.PoolManager(timeout=1.0)
        r = http.request('GET', url)
        data = r.data.decode('utf-8')

        """
        output to parse
        [
            [
                ["EINGABE", "INPUT", null, null, 3],
                ["EINGABE", "INPUT", null, null, 3]
            ],
        null, "en"]
        """

        # remove prefix
        data = data[data.find("\"")-1:]

        # remove suffix
        data = data[:data.rfind("3")+2]

        sentences_raw = data.split("],")
        sentences = ""
        for ele in sentences_raw:
            pos1 = ele.find("\"")
            pos2 = ele.find("\"", pos1 + 1)
            sentences = sentences + (ele[pos1 + 1:pos2])

        return sentences

    else:
        # client with API key
        translate_client = translate.Client()
        return (translate_client.translate(str, target_language="de"))['translatedText']

if __name__ == "__main__":

    if not USE_GOOGLE_TRANSLATION_API_FOR_FREE:
        # point to credentials JSON (placed outside of www folder, here in bitnami environment)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/bitnami/google.json"

    scrape_site_and_write_output()
