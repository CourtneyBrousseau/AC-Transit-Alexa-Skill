import urllib2
import xml.etree.ElementTree

NEXT_BUS_API_BASE = "http://webservices.nextbus.com/service/publicXMLFeed?"
busNumber = "7"

savedStops = ["55559", "57776", "51544", "55107"]

speech_output = "Here are the next " + busNumber + " buses from your saved stops: "
for stopID in savedStops:
    response = urllib2.urlopen(NEXT_BUS_API_BASE + "command=predictions&a=actransit&stopId=" + stopID)

    bus_departures = xml.etree.ElementTree.parse(response).getroot()

    for route in bus_departures.findall('predictions'):
        print("STOP NAME: " + str(route.get("stopTitle")))
        routeName = route.get("routeTag")
        stopName = route.get("stopTitle")
        if routeName == busNumber and not route.get("dirTitleBecauseNoPredictions"):
            for direction in route.findall("direction"):
                toward = direction.get("title")
                minutes = direction[0].get("minutes")
                speech_output += routeName + " bus leaving " + stopName + " toward " + toward + " in " + minutes + " minutes. "

if speech_output == "Here are the next " + busNumber + " buses from your saved stops: ":
    speech_output = "I couldn't find any " + busNumber + " buses leaving from your saved stops"

print speech_output