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
    elif intent_name == "removeStop":
        return removeStop(intent, userID)
    elif intent_name == "myStops":
        return myStops(userID)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    print "Ending session."
    # Cleanup goes here...

def handle_session_end_request():
    card_title = "AC Transit - Thanks"
    speech_output = "Thank you for using the AC Transit skill.  See you next time!"
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome_response():
    session_attributes = {}
    card_title = "AC Transit"
    speech_output = "Welcome to the Alexa AC Transit skill. " \
                    "You can ask me for bus times from any AC Transit stop, and " \
                    "save your nearby stops for the future."
    reprompt_text = "Ask me for the next buses leaving from an AC Transit stop, " \
                    "for example: what are the next buses at stop 5 5 5 5 9."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_help():
    session_attributes = {}
    card_title = "AC Transit - HELP"
    speech_output = "You can ask me for bus times from any AC Transit stop, and " \
                    "save your nearby stops for the future." \
                    "To find the 5 digit stop IDs of the stops near you, google: AC transit stop IDs"
    reprompt_text = "Ask me for the next buses leaving from an AC Transit stop, " \
                    "for example: what are the next buses at stop 5 5 5 5 9." \
                    "To find the 5 digit stop IDs of the stops near you, google: AC transit stop IDs"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    

def nextBusesFromStop(intent):
    if "value" not in intent["slots"]["StopID"].keys():
        speech_output = "I didn't hear the Stop ID. Try again. To find the 5 digit stop IDs of the stops near you, google: AC transit stop IDs"
        card_title = "Invalid Stop ID"
        should_end_session = False
        return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))
    
    stopID = str(intent["slots"]["StopID"]["value"])

    if stopInvalid(stopID):
        return sendInvalidMessage(stopID)
        
    session_attributes = {}
    card_title = "Next buses from stop " + stopID
    should_end_session = True
    
    reprompt_text = ""

    response = urllib2.urlopen(NEXT_BUS_API_BASE + "command=predictions&a=actransit&stopId=" + stopID)
    bus_departures = xml.etree.ElementTree.parse(response).getroot()
    speech_output = "Here are the next buses from "
    for route in bus_departures.findall('predictions'):
        if route == bus_departures.findall('predictions')[0]:
            stopName = route.get("stopTitle")
            stopName = stopName.replace("&", "and")
            speech_output += stopName + ": "
        routeName = route.get("routeTag")
        if not route.get("dirTitleBecauseNoPredictions"):
            for direction in route.findall("direction"):
                toward = direction.get("title")
                minutes = direction[0].get("minutes")
                speech_output += routeName + " bus toward " + toward + " in " + minutes + " minutes. "
    
    if speech_output == "Here are the next buses from ":
        speech_output = "I couldn't find any buses leaving from that stop."
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
       
def nextBusFromMyStops(intent, userID):
    if "value" not in intent["slots"]["busNumber"].keys():
        speech_output = "I didn't hear a bus route. Try again."
        card_title = "No Bus Route"
        should_end_session = False
        return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('acTransit')
    
    busNumber = str(intent["slots"]["busNumber"]["value"])

    if busNumber == "40 6L" or busNumber == "46 l":
        busNumber = "46L"
    if busNumber == "50 1A" or busNumber == "51 a":
        busNumber = "51A"
    if busNumber == "50 1B" or busNumber == "51 b" or busNumber == "51 be":
        busNumber = "51B"
    if busNumber == "70 2M" or busNumber == "72 m" or busNumber == "72 em":
        busNumber = "72M"
    if busNumber == "70 2R" or busNumber == "72 r" or busNumber == "72 are":
        busNumber = "72R"
    
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
    
    if 'Item' not in response.keys():
        speech_output = "You don't have any saved stops. To save a stop, say something like: add 5 5 5 5 9 to my stops. To find the 5 digit stop IDs of the stops near you, google: AC transit stop IDs"
        card_title = "No saved stops found "
        return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

    savedStops  = response['Item']['myStops']

    speech_output = "Here are the next " + busNumber + " buses from your saved stops: "
    
    for stopID in savedStops:
        response = urllib2.urlopen(NEXT_BUS_API_BASE + "command=predictions&a=actransit&stopId=" + stopID)
        bus_departures = xml.etree.ElementTree.parse(response).getroot()
        for route in bus_departures.findall('predictions'):
            routeName = route.get("routeTag")
            stopName = route.get("stopTitle")
            stopName = stopName.replace("&", "and")
            if routeName == busNumber and not route.get("dirTitleBecauseNoPredictions"):
                for direction in route.findall("direction"):
                    toward = direction.get("title")
                    minutes = direction[0].get("minutes")
                    speech_output += routeName + " bus leaving " + stopName + " toward " + toward + " in " + minutes + " minutes. "

    if speech_output == "Here are the next " + busNumber + " buses from your saved stops: ":
        speech_output = "I couldn't find any " + busNumber + " buses leaving from your saved stops"
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def myStops(userID):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('acTransit')
    
    session_attributes = {}
    card_title = "Your saved stops"
    should_end_session = True
    speech_output = ""
    reprompt_text = ""
    
    response = table.get_item(
    Key={
        'userID': userID,
    }
    )
    
    if 'Item' not in response.keys():
        speech_output = "You don't have any saved stops. To save a stop, say something like: add 5 5 5 5 9 to my stops. To find the 5 digit stop IDs of the stops near you, google: AC transit stop IDs"
        card_title = "No saved stops found "
        return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

    savedStops  = response['Item']['myStops']

    speech_output = "Here are your saved stops: "
    
    for stopID in savedStops:
        speech_output += stopID + ", "

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def addStop(intent, userID):
    if "value" not in intent["slots"]["StopID"].keys():
        speech_output = "I didn't hear a Stop ID. Try again. To find the 5 digit stop IDs of the stops near you, google: AC transit stop IDs"
        card_title = "Invalid Stop ID"
        should_end_session = False
        return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('acTransit')

    stopID = intent["slots"]["StopID"]["value"]
    
    if stopInvalid(stopID):
        return sendInvalidMessage(stopID)
        
    response = table.update_item(
    Key={
    'userID': userID,
    },
    UpdateExpression="ADD myStops :i",
    ExpressionAttributeValues={
        ':i': set([str(stopID)]),
    },
    ReturnValues="UPDATED_NEW"
    )
    
    speech_output = 'Great, I added ' + str(stopID) + ' to your saved stops'
    card_title = "Stop added successfully"
    
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def removeStop(intent, userID):
    if "value" not in intent["slots"]["StopID"].keys():
        speech_output = "I didn't hear a Stop ID. Try again. To find the 5 digit stop IDs of the stops near you, google: AC transit stop IDs"
        card_title = "Invalid Stop ID"
        should_end_session = False
        return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('acTransit')

    stopID = intent["slots"]["StopID"]["value"]
    
    if stopInvalid(stopID):
        return sendInvalidMessage(stopID)
        
    response = table.update_item(
    Key={
    'userID': userID,
    },
    UpdateExpression="DELETE myStops :i",
    ExpressionAttributeValues={
        ':i': set([str(stopID)]),
    },
    ReturnValues="UPDATED_NEW"
    )
    
    speech_output = 'Great, I removed ' + str(stopID) + ' from your saved stops'
    card_title = "Stop added removed"
    
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def addSpaces(stopID):
    return " ".join(stopID)
    
def stopInvalid(stopID):
    return len(str(stopID)) != 5 or str(stopID)[0] != "5"
    
def sendInvalidMessage(stopID):
    speech_output = "I heard you say stop " + addSpaces(stopID) + ". That's not a valid Stop ID. Try again. To find the 5 digit stop IDs of the stops near you, google: AC transit stop IDs"
    card_title = "Invalid Stop ID"
    should_end_session = False
    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))


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