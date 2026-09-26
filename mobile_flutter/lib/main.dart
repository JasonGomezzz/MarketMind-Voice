import 'package:flutter/material.dart';

import 'src/api_client.dart';
import 'src/home_screen.dart';
import 'src/login_screen.dart';

void main() => runApp(const MarketMindApp());

class MarketMindApp extends StatefulWidget {
  const MarketMindApp({super.key});

  @override
  State<MarketMindApp> createState() => _MarketMindAppState();
}

class _MarketMindAppState extends State<MarketMindApp> {
  final api = ApiClient();
  bool? authenticated;

  @override
  void initState() {
    super.initState();
    api.hasSession().then((value) => setState(() => authenticated = value));
  }

  @override
  Widget build(BuildContext context) {
    const seed = Color(0xFF625BFF);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'NexoMark IA',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF0D0E19),
        cardTheme: const CardThemeData(color: Color(0xFF171927), elevation: 0),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF171927),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: BorderSide.none,
          ),
        ),
      ),
      home: authenticated == null
          ? const Scaffold(body: Center(child: CircularProgressIndicator()))
          : authenticated!
          ? HomeScreen(
              api: api,
              onLogout: () => setState(() => authenticated = false),
            )
          : LoginScreen(
              api: api,
              onLogin: () => setState(() => authenticated = true),
            ),
    );
  }
}
