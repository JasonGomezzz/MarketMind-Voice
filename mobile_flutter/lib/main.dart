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
    const seed = Color(0xFF17B8AD);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'NexoMark IA',
      themeMode: ThemeMode.system,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          brightness: Brightness.light,
          primary: const Color(0xFF087B75),
          onPrimary: Colors.white,
          primaryContainer: const Color(0xFFD1F4EE),
          onPrimaryContainer: const Color(0xFF14283F),
          surface: Colors.white,
          onSurface: const Color(0xFF14283F),
        ),
        scaffoldBackgroundColor: const Color(0xFFF5FAFA),
        cardTheme: const CardThemeData(
          color: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(4))),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(4),
            borderSide: const BorderSide(color: Color(0xFFB6CDD1)),
          ),
        ),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          brightness: Brightness.dark,
          primary: seed,
          onPrimary: const Color(0xFF14283F),
          primaryContainer: const Color(0xFF173F47),
          onPrimaryContainer: const Color(0xFFD1F4EE),
          surface: const Color(0xFF14283F),
          onSurface: const Color(0xFFF3FAFB),
        ),
        scaffoldBackgroundColor: const Color(0xFF0B1929),
        cardTheme: const CardThemeData(
          color: Color(0xFF14283F),
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(4))),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF14283F),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(4),
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
