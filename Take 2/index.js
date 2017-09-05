'use strict';
var ACTAPIKEY = "704292326F281A3AFF95B2EF0CC1B9FC";

// Route the incoming request based on type (LaunchRequest, IntentRequest,
// etc.) The JSON body of the request is provided in the event parameter.
exports.handler = function (event, context) {
    try {
        console.log("event.session.application.applicationId=" + event.session.application.applicationId);

        /**
         * Uncomment this if statement and populate with your skill's application ID to
         * prevent someone else from configuring a skill that sends requests to this function.
         */
         
        if (event.session.application.applicationId !== "amzn1.ask.skill.fb54ec70-6ed2-4214-b960-71cfbbc01e15") {
           context.fail("Invalid Application ID");
        }

        if (event.session.new) {
            onSessionStarted({requestId: event.request.requestId}, event.session);
        }

        if (event.request.type === "LaunchRequest") {
            onLaunch(event.request,
                event.session,
                function callback(sessionAttributes, speechletResponse) {
                    context.succeed(buildResponse(sessionAttributes, speechletResponse));
                });
        } else if (event.request.type === "IntentRequest") {
            onIntent(event.request,
                event.session,
                function callback(sessionAttributes, speechletResponse) {
                    context.succeed(buildResponse(sessionAttributes, speechletResponse));
                });
        } else if (event.request.type === "SessionEndedRequest") {
            onSessionEnded(event.request, event.session);
            context.succeed();
        }
    } catch (e) {
        context.fail("Exception: " + e);
    }
};

/**
 * Called when the session starts.
 */
function onSessionStarted(sessionStartedRequest, session) {
    console.log("onSessionStarted requestId=" + sessionStartedRequest.requestId
        + ", sessionId=" + session.sessionId);
}

/**
 * Called when the user invokes the skill without specifying what they want.
 */
function onLaunch(launchRequest, session, callback) {
    console.log("onLaunch requestId=" + launchRequest.requestId
        + ", sessionId=" + session.sessionId);

    var cardTitle = "AC Transit"
    var speechOutput = "Welcome to AC Transit! You can ask me questions about AC Transit buses."
    callback(session.attributes,
        buildSpeechletResponse(cardTitle, speechOutput, "", true));
}

/**
 * Called when the user specifies an intent for this skill.
 */
function onIntent(intentRequest, session, callback) {
    console.log("onIntent requestId=" + intentRequest.requestId
        + ", sessionId=" + session.sessionId);

    var intent = intentRequest.intent,
        intentName = intentRequest.intent.name;

    // dispatch custom intents to handlers here
    if (intentName == 'NextBus') {
        handleNextBusRequest(intent, session, callback);
    } else if (intentName == 'NextBuses') {
        handleNextBusesRequest(intent, session, callback);
    } else if (intentName == "SetHomeStop") {
        setHomeStop(intent, session, callback);
    } else {
        throw "Invalid intent";
    }
}

/**
 * Called when the user ends the session.
 * Is not called when the skill returns shouldEndSession=true.
 */
function onSessionEnded(sessionEndedRequest, session) {
    console.log("onSessionEnded requestId=" + sessionEndedRequest.requestId
        + ", sessionId=" + session.sessionId);

    // Add any cleanup logic here
}

function setHomeStop(intent, session, callback) {
    callback(session.attributes, buildSpeechletResponseWithoutCard("Your home stop has been saved.", "", "true"));
    
    var d = require('dynasty')({});
    
    /*
    var table = function(){
        return dynasty.table("ACTransit");
    };
    table().insert({
        userID: "12345",
        Data: "STOP ID"
    });
    */
}

function handleNextBusRequest(intent, session, callback) {
    var stop = intent.slots.Stop.value.toString();
    
    var https = require("https");
    var url = "https://api.actransit.org/transit/stops/" + stop + "/predictions/?token=" + ACTAPIKEY;
    // get is a simple wrapper for request()
    // which sets the http method to GET
    var request = https.get(url, function (response) {
        // data is streamed in chunks from the server
        // so we have to handle the "data" event    
        
        var buffer = "", 
            data,
            route;
    
        response.on("data", function (chunk) {
            buffer += chunk;
        }); 
    
        response.on("end", function (err) {
            // finished transferring data
            // dump the raw data
            data = JSON.parse(buffer);
            // FIGURE OUT ERRORS
            if (buffer === "" || err) {
                callback(session.attributes, buildSpeechletResponseWithoutCard("Sorry - I couldn't find any upcoming buses for that stop.", "", "true"));
            }
            var busInfo = data[0];
            callback(session.attributes, buildSpeechletResponseWithoutCard(getBusInfoString(busInfo), "", "true"));
        }); 
    });
}

function handleNextBusesRequest(intent, session, callback) {
    var stop = intent.slots.Stop.value.toString();
    
    var https = require("https");
    var url = "https://api.actransit.org/transit/stops/" + stop + "/predictions/?token=" + ACTAPIKEY;
    // get is a simple wrapper for request()
    // which sets the http method to GET
    var request = https.get(url, function (response) {
        // data is streamed in chunks from the server
        // so we have to handle the "data" event    
        
        var buffer = "", 
            data,
            route;
    
        response.on("data", function (chunk) {
            buffer += chunk;
        }); 
    
        response.on("end", function (err) {
            // finished transferring data
            // dump the raw data
            data = JSON.parse(buffer);
            // FIGURE OUT ERRORS
            if (buffer === "" || err) {
                callback(session.attributes, buildSpeechletResponseWithoutCard("Sorry - I couldn't find any upcoming buses for that stop.", "", "true"));
            }
            var tripIds = [];
            var nextBusesStr = "";
            
            for (var i = 0; i < data.length; i++) {
                var busInfo = data[i];
                var tripId = busInfo.TripId;
                if (tripIds.indexOf(tripId) == -1) {
                    tripIds.push(tripId);
                    nextBusesStr += getBusInfoString(busInfo);
                }
            }
            
            callback(session.attributes, buildSpeechletResponseWithoutCard(nextBusesStr, "", "true"));
        }); 
    });
}

function getBusInfoString(busInfo) {
    var timeString = getTimeString(busInfo.PredictedDeparture);
    
    var nextBusStr = "A ";
    nextBusStr += busInfo.RouteName + " bus ";
    nextBusStr += " will be leaving from that stop at ";
    nextBusStr += timeString;
    return nextBusStr + " ";
}

function getTimeString(dateString) {
    var time = new Date(Date.parse(dateString));
    var hour = time.getHours();
    var minutes = time.getMinutes();
    var AMPM = "A.M.";
    if (hour > 12) {
        hour -= 12;
        AMPM = "P.M.";
    }
    return hour + ":" + minutes + " " + AMPM;
}

// ------- Helper functions to build responses -------

function buildSpeechletResponse(title, output, repromptText, shouldEndSession) {
    return {
        outputSpeech: {
            type: "PlainText",
            text: output
        },
        card: {
            type: "Simple",
            title: title,
            content: output
        },
        reprompt: {
            outputSpeech: {
                type: "PlainText",
                text: repromptText
            }
        },
        shouldEndSession: shouldEndSession
    };
}

function buildSpeechletResponseWithoutCard(output, repromptText, shouldEndSession) {
    return {
        outputSpeech: {
            type: "PlainText",
            text: output
        },
        reprompt: {
            outputSpeech: {
                type: "PlainText",
                text: repromptText
            }
        },
        shouldEndSession: shouldEndSession
    };
}

function buildResponse(sessionAttributes, speechletResponse) {
    return {
        version: "1.0",
        sessionAttributes: sessionAttributes,
        response: speechletResponse
    };
}
