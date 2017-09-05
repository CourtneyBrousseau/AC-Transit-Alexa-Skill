var request = require("request");
var i = 0; 

information = request("https://api.actransit.org/transit/stops/56044/predictions/?token=704292326F281A3AFF95B2EF0CC1B9FC", function (error, response, body) {
    
    /*
    console.log('error:', error); // Print the error if one occurred 
    console.log('statusCode:', response && response.statusCode); // Print the response status code if a response was received 
    console.log('body:', body); // Print the HTML for the Google homepage.
    */ 
    logIt(body);
    console.log("0: " + i);
});

function logIt(body) {
	i += 1;
}

console.log("1: " + i);

// console.log(i.toString());

/*
request("https://api.actransit.org/transit/stops/57774/predictions/?token=704292326F281A3AFF95B2EF0CC1B9FC", function (error, response, body) {
    console.log('error:', error); // Print the error if one occurred 
    console.log('statusCode:', response && response.statusCode); // Print the response status code if a response was received 
    console.log('body:', body); // Print the HTML for the Google homepage.
});
*/