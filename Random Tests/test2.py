import urllib2
import xml.etree.ElementTree

NEXT_BUS_API_BASE = "http://webservices.nextbus.com/service/publicXMLFeed?"
stopID = "55559"

response = urllib2.urlopen(NEXT_BUS_API_BASE + "command=predictions&a=actransit&stopId=" + stopID)
bus_departures = xml.etree.ElementTree.parse(response).getroot()
speech_output = "Here are the next buses from stop " + stopID + ": "
for route in bus_departures.findall('predictions'):
    routeName = route.get("routeTitle")
    if not route.get("dirTitleBecauseNoPredictions"):
        for direction in route.findall("direction"):
            toward = direction.get("title")
            minutes = direction[0].get("minutes")
            speech_output += routeName + " bus toward " + toward + " in " + minutes + " minutes. "

if speech_output == "Here are the next buses from stop " + stopID + ": ":
    speech_output = "I couldn't find any buses leaving from that stop."
    reprompt_text = "Make sure you said a valid five digit AC Transit Stop ID like 55559"

print speech_output
