class Campaign {
  const Campaign({
    required this.id,
    required this.title,
    required this.client,
    required this.industry,
    required this.tone,
    required this.platform,
    required this.prompt,
    required this.copy,
    required this.status,
    this.imageBase64,
  });
  final int id;
  final String title, client, industry, tone, platform, prompt, copy, status;
  final String? imageBase64;

  factory Campaign.fromJson(Map<String, dynamic> json) => Campaign(
    id: (json['id'] as num).toInt(),
    title: (json['titulo'] ?? 'Campaña').toString(),
    client: (json['cliente_nombre'] ?? json['clienteNombre'] ?? '').toString(),
    industry: (json['industria'] ?? '').toString(),
    tone: (json['tono'] ?? '').toString(),
    platform: (json['plataforma'] ?? '').toString(),
    prompt: (json['prompt'] ?? '').toString(),
    copy: (json['texto_generado'] ?? json['textoGenerado'] ?? '').toString(),
    status: (json['estado'] ?? '').toString(),
    imageBase64: (json['imagen_b64'] ?? json['imagenB64'])?.toString(),
  );
}

class CampaignDraft {
  const CampaignDraft({
    required this.title,
    required this.clientName,
    required this.clientEmail,
    required this.industry,
    required this.tone,
    required this.platform,
    required this.prompt,
  });
  final String title, clientName, clientEmail, industry, tone, platform, prompt;
  Map<String, dynamic> toJson() => {
    'titulo': title,
    'cliente_nombre': clientName,
    'cliente_email': clientEmail,
    'industria': industry,
    'tono': tone,
    'plataforma': platform,
    'prompt': prompt,
  };
}
