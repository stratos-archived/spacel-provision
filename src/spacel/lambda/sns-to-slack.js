/**
 * @author DeviaVir
 */
var https = require('https');
var util = require('util');

exports.handler = function(event, context) {
  var postData = {
    'username': 'orbit',
    'text': '*' + event.Records[0].Sns.Subject + '*'
  };

  var message = event.Records[0].Sns.Message;
  try {
    message = JSON.parse(event.Records[0].Sns.Message);
  } catch(e) {}
  var stateRed = event.Records[0].Sns.Subject.indexOf('ALARM:');
  var color = 'good';

  if (stateRed != -1) {
    color = 'danger';
  }

  var fields = [];
  if (typeof message === 'object') {
    fields = [
      {
        'title': 'Alarm',
        'value': message.AlarmName,
        'short': true
      },
      {
        'title': 'Status',
        'value': message.NewStateValue,
        'short': true
      },
      {
        'title': 'Reason',
        'value': message.NewStateReason,
        'short': false
      }
    ];
  }

  postData.attachments = [
    {
      'text': event.Records[0].Sns.Subject,
      'fallback': event.Records[0].Sns.Subject,
      'color': color,
      'fields': fields
    }
  ];

  var options = {
    method: 'POST',
    hostname: 'hooks.slack.com',
    port: 443,
    path: '__PATH__'
  };

  var req = https.request(options, function(res) {
    res.setEncoding('utf8');
    res.on('data', function (chunk) {
      context.done(null);
    });
  });

  req.on('error', function(e) {
    console.log('problem with request: ' + e.message);
  });

  req.write(util.format('%j', postData));
  req.end();
};