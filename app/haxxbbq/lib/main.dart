import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'mqtt_wrapper.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        // This is the theme of your application.
        //
        // Try running your application with "flutter run". You'll see the
        // application has a blue toolbar. Then, without quitting the app, try
        // changing the primarySwatch below to Colors.green and then invoke
        // "hot reload" (press "r" in the console where you ran "flutter run",
        // or simply save your changes to "hot reload" in a Flutter IDE).
        // Notice that the counter didn't reset back to zero; the application
        // is not restarted.
        primarySwatch: Colors.blue,
        // This makes the visual density adapt to the platform that you run
        // the app on. For desktop platforms, the controls will be smaller and
        // closer together (more dense) than on mobile platforms.
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: MyHomePage(title: 'Haxx iBBQ'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  MyHomePage({Key key, this.title}) : super(key: key);

  // This widget is the home page of your application. It is stateful, meaning
  // that it has a State object (defined below) that contains fields that affect
  // how it looks.

  // This class is the configuration for the state. It holds the values (in this
  // case the title) provided by the parent (in this case the App widget) and
  // used by the build method of the State. Fields in a Widget subclass are
  // always marked "final".

  final String title;

  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  String ibbqState = 'unknown';
  String ibbqTemp = '0.0';
  String targetTemp = '60';
  MQTTClientWrapper mqttClientWrapper;

  void setup() {
    mqttClientWrapper = MQTTClientWrapper(() => onConnect(),
        (newState) => gotNewState(newState), (newTemp) => gotNewTemp(newTemp));
    mqttClientWrapper.prepareMqttClient();
  }

  void onConnect() {
    print('connected!');
  }

  void gotNewState(String state) {
    setState(() {
      this.ibbqState = state;
    });
  }

  void gotNewTemp(String temp) {
    setState(() {
      this.ibbqTemp = temp;
    });
  }

  void setTargetTemp(String temp) {
    setState(() {
      this.targetTemp = temp;
    });
  }

  @override
  void initState() {
    super.initState();

    setup();
  }

  @override
  Widget build(BuildContext context) {
    // This method is rerun every time setState is called, for instance as done
    // by the _incrementCounter method above.
    //
    // The Flutter framework has been optimized to make rerunning build methods
    // fast, so that you can just rebuild anything that needs updating rather
    // than having to individually change instances of widgets.
    return Scaffold(
      appBar: AppBar(
          // Here we take the value from the MyHomePage object that was created by
          // the App.build method, and use it to set our appbar title.
          title: Text(widget.title),
          actions: <Widget>[
            FlatButton(
                onPressed: () {
                  if (ibbqState == "idle") {
                    mqttClientWrapper.sendControlMessage("connect");
                  }
                },
                child: Text(
                  ibbqState,
                  style: Theme.of(context)
                      .primaryTextTheme
                      .button
                      .copyWith(color: Colors.white),
                ))
          ]),
      body: Center(
        // Center is a layout widget. It takes a single child and positions it
        // in the middle of the parent.
        child: Column(
          // Column is also a layout widget. It takes a list of children and
          // arranges them vertically. By default, it sizes itself to fit its
          // children horizontally, and tries to be as tall as its parent.
          //
          // Invoke "debug painting" (press "p" in the console, choose the
          // "Toggle Debug Paint" action from the Flutter Inspector in Android
          // Studio, or the "Toggle Debug Paint" command in Visual Studio Code)
          // to see the wireframe for each widget.
          //
          // Column has various properties to control how it sizes itself and
          // how it positions its children. Here we use mainAxisAlignment to
          // center the children vertically; the main axis here is the vertical
          // axis because Columns are vertical (the cross axis would be
          // horizontal).
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text(
              "Temperature",
              style: Theme.of(context).textTheme.headline5,
            ),
            Text(
              ibbqTemp,
              style: Theme.of(context).textTheme.headline2,
            ),
            Text(
              "Target temperature",
              style: Theme.of(context).textTheme.headline5,
            ),
            GestureDetector(
                onTap: () async {
                  String _name;
                  _name = await Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) {
                        return TextEntry(
                          type: TextInputType.number,
                          title: "Target temperature",
                          defaultText: targetTemp,
                        );
                      },
                    ),
                  );
                  if (_name != null) {
                    setTargetTemp(_name);
                  }
                },
                child: Text(
                  targetTemp,
                  style: Theme.of(context).textTheme.headline3,
                )),
          ],
        ),
      ),
    );
  }
}

class TextEntry extends StatefulWidget {
  final String title;
  final String defaultText;
  final TextInputType type;

  const TextEntry(
      {Key key,
      @required this.type,
      @required this.title,
      @required this.defaultText})
      : super(key: key);

  _TextEntryState createState() => _TextEntryState();
}

class _TextEntryState extends State<TextEntry> {
  List<TextInputFormatter> formatters;
  TextEditingController inputController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    if (widget.type == TextInputType.number) {
      formatters = [WhitelistingTextInputFormatter.digitsOnly];
    } else {
      formatters = [];
    }
    inputController.text = widget.defaultText;
    inputController.selection = TextSelection(
        baseOffset: widget.defaultText.length,
        extentOffset: widget.defaultText.length);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: Column(children: <Widget>[
        TextField(
            autofocus: true,
            keyboardType: widget.type,
            inputFormatters: formatters,
            controller: inputController,
            decoration: InputDecoration(
              labelText: widget.title,
            )),
        RaisedButton(
            child: Text("OK"),
            onPressed: () {
              Navigator.of(context).pop(inputController.value.text);
            }),
      ]),
    );
  }

  void dispose() {
    inputController.dispose();
    super.dispose();
  }
}
