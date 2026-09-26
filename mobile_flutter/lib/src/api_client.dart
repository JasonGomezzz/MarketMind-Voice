import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import 'models.dart';

class ApiException implements Exception {
  const ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();
  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
  static const _storage = FlutterSecureStorage();
  final http.Client _client;

  Future<bool> hasSession() async =>
      (await _storage.read(key: 'access'))?.isNotEmpty == true;

  Future<void> login(String email, String password) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/token/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    final body = _json(response);
    if (response.statusCode != 200) {
      throw ApiException(_message(body, 'Correo o contraseña incorrectos.'));
    }
    await _storage.write(key: 'access', value: body['access']?.toString());
    await _storage.write(key: 'refresh', value: body['refresh']?.toString());
  }

  Future<void> logout() async => _storage.deleteAll();

  Future<List<Campaign>> campaigns() async {
    final response = await _get('/api/campaigns/');
    final body = _json(response);
    if (response.statusCode != 200) {
      throw ApiException(_message(body, 'No se pudieron cargar las campañas.'));
    }
    final dynamic raw =
        body['results'] ??
        (body['data'] is Map ? body['data']['results'] ?? body['data'] : body);
    final list = raw is List ? raw : <dynamic>[];
    return list
        .map(
          (item) => Campaign.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<Campaign> createCampaign(CampaignDraft draft) async {
    final response = await _post('/api/campaigns/', draft.toJson());
    final body = _json(response);
    if (response.statusCode != 201 && response.statusCode != 200) {
      throw ApiException(_message(body, 'No se pudo crear la campaña.'));
    }
    final data = body['data'];
    final raw = data is Map
        ? data['campaign'] ?? data
        : body['campaign'] ?? body;
    return Campaign.fromJson(Map<String, dynamic>.from(raw as Map));
  }

  Future<Uint8List> geminiSpeech(String text) async {
    final response = await _post('/api/campaigns/voice/synthesize/', {
      'text': text,
    });
    if (response.statusCode != 200) {
      throw ApiException(
        _message(_json(response), 'La voz Gemini no está disponible.'),
      );
    }
    return response.bodyBytes;
  }

  Future<String> geminiTranscription(
    Uint8List audio, {
    String mimeType = 'audio/mp4',
    String filename = 'dictado.m4a',
  }) async {
    final token = await _storage.read(key: 'access');
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/campaigns/voice/transcribe/'),
    )
      ..headers['Authorization'] = 'Bearer $token'
      ..files.add(
        http.MultipartFile.fromBytes(
          'audio',
          audio,
          filename: filename,
          contentType: MediaType.parse(mimeType),
        ),
      );
    final response = await http.Response.fromStream(await _client.send(request));
    final body = _json(response);
    if (response.statusCode != 200) {
      throw ApiException(_message(body, 'No se pudo transcribir el audio.'));
    }
    final transcript = body['transcript']?.toString().trim() ?? '';
    if (transcript.isEmpty) {
      throw const ApiException('Gemini no detectó voz en el audio.');
    }
    return transcript;
  }

  Future<http.Response> _get(String path) async {
    final token = await _storage.read(key: 'access');
    return _client.get(
      Uri.parse('$baseUrl$path'),
      headers: {'Authorization': 'Bearer $token'},
    );
  }

  Future<http.Response> _post(String path, Map<String, dynamic> body) async {
    final token = await _storage.read(key: 'access');
    return _client.post(
      Uri.parse('$baseUrl$path'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(body),
    );
  }

  Map<String, dynamic> _json(http.Response response) {
    try {
      return Map<String, dynamic>.from(
        jsonDecode(utf8.decode(response.bodyBytes)) as Map,
      );
    } catch (_) {
      return const {};
    }
  }

  String _message(Map<String, dynamic> body, String fallback) {
    final data = body['data'];
    return (body['detail'] ??
            body['message'] ??
            (data is Map ? data['detail'] : null) ??
            fallback)
        .toString();
  }
}
