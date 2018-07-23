'use strict';

exports.handler = (event, context, callback) => {

    //setting the below attribute ensures our Lambda function returns control as soon as callback() is invoked
    //it does not wait for empty loop scenarios
    context.callbackWaitsForEmptyEventLoop = false;
    
    //we will be using the following 3 plugins. 
    var admin = require("firebase-admin");
    // Postgres connector
    var pg = require("pg");
    const { Pool, Client} = require('pg');
    // Datetime handling
    var moment = require("moment");
    
    //since we will be invoking our Lambda function with AWS API Gateway using a POST request
    //it will send the body payload within 'body-json' attribute
    var jsonBody = event['body-json'];

    //fcm is the unique token generated for each device by Firebase
    var fcm = jsonBody.fcm;
    //mobile_id is a unique device identifier generated for each device
    var mobile_id = jsonBody.mobile_id;
    
    //replace the contents below with the JSON object downloaded from the FCM console.
    var serviceAccount = {
      "type": "service_account",
      "project_id": "pushengine-15948",
      "private_key_id": "528bc23ee87b96fa1c31cd3bf88aed01445535a4",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDINacpB0wP0hkm\nRfQF4ZaqTeButzcblcXYjEwNyvg4mfnjqKSCGBhkyDIllWqVhS+laffmxisKKA+Y\nVbRgLR/w6FqJ01tTplgfc9LQhYjcsu8DcLypiPK1iwbKh3KuU5lMJ9/mAqX0i8SP\n0FZKGUVwzlTtTlWQisXR+VcWCdsuSgk3szjo2wqQhYpp3lKoyphgXf6FZi8obyfH\nIF8l7C94bS85m08EmaEXD3BJq8wONnMe92xgiC24CUMHWLb29auezQ8Nl6LyYI9c\nQ7BYtaBaDO4BgfOLrZHdq7iFCT5Eozfcp5hYamN4xg0MX7dPE0C9z2D8b1Jeux06\nHYTOPDx7AgMBAAECggEAS55AKbXw25TeHN+VAFepIV/Sod6feNLD7DtpSlhcEnzN\nrlf28pAJPp+CmUFrBVhNm6t/j3FPtkFVSpMsUpsYklQgRihHOTv90rtbZ5jYDYuj\nzOfayinIihsdkIdCIGfA4cu5vFVJuyjDMBJfVRNgb+/ukcbheHuBpgIIC3HjkAKJ\nf7MmKA3WB3crKWiXcy8SP/5bib8l4nFWWmRbzP6OovEjMMoryl/7VHjuIbprlw2W\n6MxKu2e3wWIqBTq594cDIj5irJ73Gd37SlfipIkyWcN4p3OElHg/lPAvjLpe/KJo\nR15uN7TzghpHBR4tPyxPr1iaAiGLWcNVros13bNEIQKBgQDrAxzmd/F69vV5NeGH\nDN0TQwIdAeyOKT/E3fxyd8gnadNOoGTW0eKOlkaezKcwqRfpUbI8QVmO23rMdfvF\nlrb4T3AlvWMDUtKaomAM6jtNpGYIv5B5OzZ1OqYj/+WCg46TzEsWT9GNE1xXKgEH\nngWGeN1nVbQcknsStYADd9m6iwKBgQDaFuC0WS/9hhYdtg2k69ttURBDg9cgQvco\ndaGpq2rD9X4bcj1cnB//KziMimJ9cxGsSfwK50cpL+pRd2LYooSQu8Opa1OUnvQt\nK57Ps7sQ+Z9h/tTB2e9xTmoxtjbMCGLJi9mZ1FtfJnZY7LXDgOz5s5KTRDdflmGI\n6TxGLlvz0QKBgQCnOh3UeUDhyN0/lPGYEbU2QZY9YeMb/Yoc4gECyu0n7ouoBUX7\n/nmCELjLwsCtRYV4RuPXMIEzwEWPO90d6nLkGlKo6CyObt7hne1PA1WTmAnq67U4\nLsQ/gq46K5r61fYcgWBkzgNEqaQpegAllXJFD7gsEbYKJslgtLoUvbG2pQKBgDFB\nzYquQiqOqFwZjEddhffQwU2eb2438b7Poq3Bq6GKxurICJfsI0Xsqx8C+m+/F5TE\nOQr1ZZsl2VSBFHA9dJeD8RNIzF3a8Odq3LmorG2PE7J8be1CndQHk/CaaRH4Kue+\nkG0wC1sYQs6e2AbKDbvwFQDx/Ve3jVvw4c4wFlChAoGBAIavhZR/Qh6XUJu/XyWA\naAhOUApceX1terr6HGeM6jmhBTxGwn9ECVLcXWTLWzcdfMqXlxZm5NFp7l0prUAn\nDil6PPbaiVnTyC80JPeeGB/Ic0S9cSADLnJZ2dhi5bLFFW8xrAROC8MnHhGjh+tJ\n87pzjYNja5Ptwdm4XGyM1E90\n-----END PRIVATE KEY-----\n",
      "client_email": "firebase-adminsdk-w1y76@pushengine-15948.iam.gserviceaccount.com",
      "client_id": "113067317108662883381",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://accounts.google.com/o/oauth2/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-w1y76%40pushengine-15948.iam.gserviceaccount.com"
    }
    
    //databaseURL below is provided in the FCM console.
    admin.initializeApp({
        credential: admin.credential.cert(serviceAccount),
        databaseURL: "https://pushengine-15948.firebaseio.com"
    });
    
    //our database configuration. I am using an RDS PostgreSQL instance on AWS
    var config = {
        host: 'blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com',
        user: 'root',
        password: 'agdevil1',
        // debug : true,
        database: 'pushengine',
        port: 5432
    }
    const db_pool = new Pool(config);
    const db = new Client(config)
    db.connect();
    db.query(
        "SELECT * FROM fcm_users WHERE mobile_id = ?",
        [mobile_id],
        function (err, users) {
            if (users.length > 0) {
                //if the mobile_id already exists in our database, simply update the FCM token for all matching mobile_ids
                db.query(
                    "UPDATE fcm_users SET fcm = ?, updated_on = ? WHERE mobile_id = ?",
                    [fcm, moment().format("YYYY-MM-DD HH:mm:ss"), mobile_id],
                    function (err, status) {
                        
                        db.end();
                        
                        if(err){
                            var response = {
                                statusCode: 200,
                                headers: {},
                                body: "error updating data to DB"
                            };
                            callback(null, response);
                        }else{
                            //subcribe to the 'general' topic in FCM. 
                            admin.messaging().subscribeToTopic(fcm, "general")
                            .then(function (fcmResp) {
                                //delete the firebase object. This is especially important in lambda
                                admin.app('[DEFAULT]').delete();

                                var response = {
                                    statusCode: 200,
                                    headers: {},
                                    body: "fcm subscribed sucessfully"
                                };
                                callback(null, response);
                            })
                            .catch(function (fcmError) {
                                //delete the firebase object. This is especially important in lambda
                                admin.app('[DEFAULT]').delete();

                                var response = {
                                    statusCode: 200,
                                    headers: {},
                                    body: "some error during fcm subscription"
                                };
                                callback(null, response);
                            });
                        }
                    });
                } else {
                    //the passed mobile_id does not exist in our DB. So, we create a fresh entry
                    var data = {
                        "fcm": fcm,
                        "mobile_id": mobile_id,
                        "added_on": moment().format("YYYY-MM-DD HH:mm:ss"),
                        "updated_on": moment().format("YYYY-MM-DD HH:mm:ss")
                    };
                    
                    db.query(
                        "INSERT INTO fcm_users set ? ",
                        data,
                        function (err, status) {
                            db.end();

                            if (err) {
                                var response = {
                                    statusCode: 200,
                                    headers: {},
                                    body: "error inserting data to DB"
                                };
                                callback(null, response);
                            } else {
                                //subcribe to the 'general' topic in FCM. 
                                admin.messaging().subscribeToTopic(fcm, "general")
                                .then(function (fcmResp) {
                                    //delete the firebase object. This is especially important in lambda
                                    admin.app('[DEFAULT]').delete();
                                    var response = {
                                        statusCode: 200,
                                        headers: {},
                                        body: "fcm subscribed sucessfully"
                                    };
                                    callback(null, response);
                                })
                                .catch(function (fcmError) {
                                    //delete the firebase object. This is especially important in lambda
                                    admin.app('[DEFAULT]').delete();
                                    var response = {
                                        statusCode: 200,
                                        headers: {},
                                        body: "some error during fcm subscription"
                                    };
                                    callback(null, response);
                                });
                            }
                        }
                    );
                }
            }
        );
        
    }
