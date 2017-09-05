var Alexa = require('alexa-sdk');
var request = require("request");
var ACTAPIKEY = "704292326F281A3AFF95B2EF0CC1B9FC";

exports.handler = function(event, context, callback) {
    var alexa = Alexa.handler(event, context);

    alexa.dynamoDBTableName = 'ACTransit'; // creates new table for session.attributes

    alexa.registerHandlers(handlers);
    alexa.execute();
};

var handlers = {
    'LaunchRequest': function() { //Executes when a new session is launched

    },

    'SetHomeStop': function() {
        var homeStop = this.event.request.intent.slots.homeStop.value;
        this.attributes['myStop'] = homeStop;
        this.emit(':tell', "Got it! I now know your home stop is " + homeStop);
    },

    'GetHomeStop': function() {
        var homeStop = this.attributes['myStop'];
        this.emit(':tell', "Your home stop is " + homeStop);
    },

    'NextBus': function() {
        var stop = this.event.request.intent.slots.stop.value;

        function sendSuccess() {
            this.emit(':tell', "SUCCESS THROUGH FUNCTION!");
        }

        request("https://api.actransit.org/transit/stops/57774/predictions/?token=704292326F281A3AFF95B2EF0CC1B9FC", function (error, response, body) {
            sendSuccess();
            /*
            console.log('error:', error); // Print the error if one occurred 
            console.log('statusCode:', response && response.statusCode); // Print the response status code if a response was received 
            console.log('body:', body); // Print the HTML for the Google homepage.
            */ 
            //this.emit(':tell', "SUCCESS INSIDE!" + body.substring(0, 100));
        });
    }
};

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