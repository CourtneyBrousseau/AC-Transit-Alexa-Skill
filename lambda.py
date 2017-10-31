import urllib2
import boto3
import xml.etree.ElementTree

NEXT_BUS_API_BASE = "http://webservices.nextbus.com/service/publicXMLFeed?"

def lambda_handler(event, context):
    if (event["session"]["application"]["applicationId"] !=
            "amzn1.ask.skill.49ae3ec4-1ad6-44d7-b433-6846e87be8a8"):
        raise ValueError("Invalid Application ID")
    
    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])

def on_session_started(session_started_request, session):
    print "Starting new session."

def on_launch(launch_request, session):
    return get_welcome_response()

def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]
    userID = session['user']['userId']

    if intent_name == "nextBusesFromStop":
        return nextBusesFromStop(intent)
    if intent_name == "nextBusFromMyStops":
        return nextBusFromMyStops(intent, userID)
    elif intent_name == "addStop":
        return addStop(intent, userID)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    print "Ending session."
    # Cleanup goes here...

def handle_session_end_request():
    card_title = "BART - Thanks"
    speech_output = "Thank you for using the BART skill.  See you next time!"
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome_response():
    session_attributes = {}
    card_title = "AC Transit"
    speech_output = "Welcome to the Alexa AC Transit skill. " \
                    "You can ask me for bus times from any AC Transit stop, and " \
                    "save your nearby stops for the future."
    reprompt_text = "Ask me for the next buses leaving from an AC Transit stop, " \
                    "for example 55559."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def nextBusesFromStop(intent):
    stopID = str(intent["slots"]["StopID"]["value"])

    session_attributes = {}
    card_title = "Next buses from stop " + stopID
    should_end_session = True
    reprompt_text = "Make sure you said a valid five digit AC Transit Stop ID like 55559"

    response = urllib2.urlopen(NEXT_BUS_API_BASE + "command=predictions&a=actransit&stopId=" + stopID)
    bus_departures = xml.etree.ElementTree.parse(response).getroot()
    speech_output = "Here are the next buses from stop " + stopID + ": "
    for route in bus_departures.findall('predictions'):
        routeName = route.get("routeTag")
        if not route.get("dirTitleBecauseNoPredictions"):
            for direction in route.findall("direction"):
                toward = direction.get("title")
                minutes = direction[0].get("minutes")
                speech_output += routeName + " bus toward " + toward + " in " + minutes + " minutes. "
    
    if speech_output == "Here are the next buses from stop " + stopID + ": ":
        speech_output = "I couldn't find any buses leaving from that stop."
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
       
def nextBusFromMyStops(intent, userID):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('acTransit')
    
    busNumber = str(intent["slots"]["busNumber"]["value"])

    session_attributes = {}
    card_title = "Next " + busNumber + " buses from your saved stops"
    should_end_session = True
    speech_output = ""
    reprompt_text = ""
    
    response = table.get_item(
    Key={
        'userID': userID,
    }
    )

    savedStops  = response['Item']['myStops']

    speech_output = "Here are the next " + busNumber + " buses from your saved stops: "
    
    for stopID in savedStops:
        response = urllib2.urlopen(NEXT_BUS_API_BASE + "command=predictions&a=actransit&stopId=" + stopID)
        bus_departures = xml.etree.ElementTree.parse(response).getroot()
        for route in bus_departures.findall('predictions'):
            routeName = route.get("routeTag")
            stopName = route.get("stopTitle")
            if routeName == busNumber and not route.get("dirTitleBecauseNoPredictions"):
                for direction in route.findall("direction"):
                    toward = direction.get("title")
                    minutes = direction[0].get("minutes")
                    speech_output += routeName + " bus leaving " + stopName + " toward " + toward + " in " + minutes + " minutes. "

    if speech_output == "Here are the next " + busNumber + " buses from your saved stops: ":
        speech_output = "I couldn't find any " + busNumber + " buses leaving from your saved stops"
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def addStop(intent, userID):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('acTransit')

    
    stopID = intent["slots"]["StopID"]["value"]
    stopName = intent["slots"]["StopName"]["value"]
    
    speech_output = 'a'
    
    response = table.update_item(
        TableName='acTransit',
        Key={
            'userID': userID
        },
        UpdateExpression='SET ' + str(stopName) + ' = :val1',
        ExpressionAttributeValues={
        ':val1': stopID
        },
        ConditionExpression='attribute_not_exists(stopID)'
    )
    
    speech_output = 'stop added'
    
    card_title = "BART - Thanks"
    
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def milToPeople(militaryTime):
    hour = int(militaryTime[0:2])
    mins = int(militaryTime[3:5])
    amPm = "AM"
    
    if hour > 12:
        hour = hour - 12
        amPm = "PM"
    elif hour == 12:
        amPm = "PM"
    elif hour == 0:
        hour = 12
    return str(hour) + ":" + str(mins) + " " + amPm

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }