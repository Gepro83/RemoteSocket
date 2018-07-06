/*
 * This server provides the frontend for the project. It forwards the user inputs to the python script
 * that manages the connection to arduino.
 */
var http = require('http');
var url = require('url');
var fs = require('fs');
// run the python script that communicates with arduino
var spawn = require('child_process').spawn;
var arduinoPy = spawn('python', ['ArduinoInterface.py'], { stdio: 'pipe'});

// just print everything coming from python to console, these are just status messages
arduinoPy.stdout.on('data', function (message) {
  console.log(message.toString('utf-8'));
})

http.createServer(function (req, res) {
  var q = url.parse(req.url, true);
  var filename = "." + q.pathname;
  // check post request values for OnlineInterface page
  if (filename == "./OnlineInterface.html") {
      var data = q.query;
      if ('on' in data) {
        if (data['on'] == '1') {
          // send turn on signal to adruino
          arduinoPy.stdin.write('on\n');
          console.log('on sent');
        }
      }
      if ('off' in data) {
        if (data['off'] == '1') {
          // send turn off signal to adruino
          arduinoPy.stdin.write('off\n');
          console.log('off sent');
        }
      }
      if ('threshold' in data) {
        // check if th contains a number
        if (!isNaN(data['threshold'])) {
          // convert to number
          var th = Number(data['threshold'])
          // limit range to [0,100]
          if (th < 0) {
            th = 0
          }
          if (th > 100) {
            th = 100
          }
          arduinoPy.stdin.write(th.toString() + '\n');
        } else {
          res.writeHead(200, {'Content-Type': 'text/html'});
          return res.end('Threshold must be a number!')
        }
      }  
  }
  fs.readFile(filename, function(err, data) {
    if (err) {
      res.writeHead(404, {'Content-Type': 'text/html'});
      return res.end("404 Not Found");
    }  
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.write(data);
    return res.end();
  });
}).listen(8080);