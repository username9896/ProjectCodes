const express = require('express');
const bodyParser = require('body-parser');
const admin = require('firebase-admin');
const mqtt = require('mqtt');

const serviceAccount = require('./serviceAccountKey.json');

admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: "https://shms-3646a-default-rtdb.firebaseio.com"
});

const db = admin.database();

const app = express();
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
    extended: true
}));

const port = 5003;

app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

const URL = 'mqtt://localhost:1884';
const temperature = 'temperature_topic'
const IR = 'heart_rate_topic'
const Avg_BPM = 'bpm_topic'
const date = 'date'

const connect = mqtt.connect(URL);

let a = 0;
let b = 0;
let c = 0;
let d = 0;

connect.on('connect', function () {
    console.log('Connected to MQTT broker');

    connect.subscribe(temperature, function (err) {
        if (err) {
            console.error('Failed: ', err);
        } else {
            console.log('Subscribed: ', temperature);
        }
    });

    connect.subscribe(IR, function (err) {
        if (err) {
            console.error('Failed: ', err);
        } else {
            console.log('Subscribed: ', IR);
        }
    });

    connect.subscribe(Avg_BPM, function (err) {
        if (err) {
            console.error('Failed: ', err);
        } else {
            console.log('Subscribed: ', Avg_BPM);
        }
    });

    connect.subscribe(date, function (err) { // Corrected the topic name
        if (err) {
            console.error('Failed: ', err);
        } else {
            console.log('Subscribed: ', date);
        }
    });
});

connect.on('message', async function (topic, message) {
    console.log(topic, ' ', message.toString());

    if (topic === 'temperature_topic') {
        a = message;
    } else if (topic === 'heart_rate_topic') {
        b = message;
    } else if (topic === 'bpm_topic') {
        c = message;
    } else if (topic === 'date') {
        d = message;
    }
});

// Define a function to push data to the database
const pushDataToDatabase = async () => {
    if (a && b && c && d) {
        const sensorDataRef = db.ref('sensorData');
        const newSensorData = {
            temperature: parseFloat(a),
            HeartRate: parseFloat(b),
            BPM: parseFloat(c),
            Date: Date(d)
        };

        try {
            await sensorDataRef.push(newSensorData);
            console.log('Sensor data pushed to Realtime Database');
        } catch (error) {
            console.error('Error pushing sensor data to Realtime Database:', error);
        }
    }
};

// Set an interval to push data every 1 second
setInterval(pushDataToDatabase, 1000);

app.listen(port, () => {
    console.log(`Server is listening on port ${port}.`);
});
