import 'package:flutter/material.dart';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

import 'constants.dart' as Constants;
import 'models.dart';

class MQTTClientWrapper {
  MqttServerClient client;

  MqttCurrentConnectionState connectionState = MqttCurrentConnectionState.IDLE;
  MqttSubscriptionState subscriptionState = MqttSubscriptionState.IDLE;

  final VoidCallback onConnectedCallback;
  final Function(String) onStateReceivedCallback;
  final Function(String) onTempReceivedCallback;

  MQTTClientWrapper(this.onConnectedCallback, this.onStateReceivedCallback,
      this.onTempReceivedCallback);

  void prepareMqttClient() async {
    _setupMqttClient();
    await _connectClient();
    _subscribeToTopics();
  }

  void sendControlMessage(String msg) {
    _publishMessage(msg);
  }

  Future<void> _connectClient() async {
    try {
      print('MQTTClientWrapper::Mosquitto client connecting....');
      connectionState = MqttCurrentConnectionState.CONNECTING;
      await client.connect();
    } on Exception catch (e) {
      print('MQTTClientWrapper::client exception - $e');
      connectionState = MqttCurrentConnectionState.ERROR_WHEN_CONNECTING;
      client.disconnect();
    }

    if (client.connectionStatus.state == MqttConnectionState.connected) {
      connectionState = MqttCurrentConnectionState.CONNECTED;
      print('MQTTClientWrapper::Mosquitto client connected');
    } else {
      print(
          'MQTTClientWrapper::ERROR Mosquitto client connection failed - disconnecting, status is ${client.connectionStatus}');
      connectionState = MqttCurrentConnectionState.ERROR_WHEN_CONNECTING;
      client.disconnect();
    }
  }

  void _setupMqttClient() {
    client =
        MqttServerClient.withPort(Constants.serverUri, '#', Constants.port);
    client.logging(on: false);
    client.keepAlivePeriod = 20;
    client.onDisconnected = _onDisconnected;
    client.onConnected = _onConnected;
    client.onSubscribed = _onSubscribed;
  }

  void _subscribeToTopics() {
    client.subscribe(Constants.stateTopic, MqttQos.atMostOnce);
    client.subscribe(Constants.tempTopic, MqttQos.atMostOnce);

    client.updates.listen((List<MqttReceivedMessage<MqttMessage>> c) {
      final MqttPublishMessage recMess = c[0].payload;
      final String msg =
          MqttPublishPayload.bytesToStringAsString(recMess.payload.message);

      if (c[0].topic == Constants.stateTopic) {
        print("MQTTClientWrapper::new state received: $msg");
        if (msg != null) onStateReceivedCallback(msg);
      }
      if (c[0].topic == Constants.tempTopic) {
        print("MQTTClientWrapper::new temp received: $msg");
        if (msg != null) onTempReceivedCallback(msg);
      }
    });
    _publishMessage("ping");
  }

  void _publishMessage(String message) {
    final MqttClientPayloadBuilder builder = MqttClientPayloadBuilder();
    builder.addString(message);

    print(
        'MQTTClientWrapper::Publishing message $message to topic ${Constants.ctrlTopic}');
    client.publishMessage(
        Constants.ctrlTopic, MqttQos.exactlyOnce, builder.payload);
  }

  void _onSubscribed(String topic) {
    print('MQTTClientWrapper::Subscription confirmed for topic $topic');
    subscriptionState = MqttSubscriptionState.SUBSCRIBED;
  }

  void _onDisconnected() {
    print(
        'MQTTClientWrapper::OnDisconnected client callback - Client disconnection');
    connectionState = MqttCurrentConnectionState.DISCONNECTED;
  }

  void _onConnected() {
    connectionState = MqttCurrentConnectionState.CONNECTED;
    print(
        'MQTTClientWrapper::OnConnected client callback - Client connection was successful');
    onConnectedCallback();
  }
}
