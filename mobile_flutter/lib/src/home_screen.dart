import 'dart:convert';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import 'api_client.dart';
import 'models.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api, required this.onLogout});
  final ApiClient api;
  final VoidCallback onLogout;
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int tab = 0;
  bool loading = true;
  String? error;
  List<Campaign> items = const [];

  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      items = await widget.api.campaigns();
    } catch (e) {
      error = e.toString();
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> logout() async {
    await widget.api.logout();
    widget.onLogout();
  }

  void showCampaign(Campaign campaign) => Navigator.of(context).push(
    MaterialPageRoute(
      builder: (_) => CampaignDetailScreen(api: widget.api, campaign: campaign),
    ),
  );

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: Row(
        children: [
          const Icon(Icons.auto_awesome, color: Color(0xFF938EFF)),
          const SizedBox(width: 10),
          Text(tab == 0 ? 'Mis campañas' : 'Laboratorio IA'),
        ],
      ),
      actions: [
        IconButton(
          onPressed: logout,
          tooltip: 'Cerrar sesión',
          icon: const Icon(Icons.logout),
        ),
      ],
    ),
    body: tab == 0
        ? RefreshIndicator(onRefresh: refresh, child: _campaignList())
        : CreateCampaignView(
            api: widget.api,
            onCreated: (campaign) {
              setState(() {
                items = [campaign, ...items];
                tab = 0;
              });
              showCampaign(campaign);
            },
          ),
    bottomNavigationBar: NavigationBar(
      selectedIndex: tab,
      onDestinationSelected: (value) => setState(() => tab = value),
      destinations: const [
        NavigationDestination(
          icon: Icon(Icons.campaign_outlined),
          selectedIcon: Icon(Icons.campaign),
          label: 'Campañas',
        ),
        NavigationDestination(
          icon: Icon(Icons.mic_none),
          selectedIcon: Icon(Icons.mic),
          label: 'Crear con voz',
        ),
      ],
    ),
  );

  Widget _campaignList() {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (error != null) {
      return ListView(
        children: [
          const SizedBox(height: 180),
          const Icon(Icons.cloud_off, size: 54),
          const SizedBox(height: 16),
          Text(error!, textAlign: TextAlign.center),
          const SizedBox(height: 14),
          Center(
            child: FilledButton(
              onPressed: refresh,
              child: const Text('Reintentar'),
            ),
          ),
        ],
      );
    }
    if (items.isEmpty) {
      return ListView(
        children: [
          const SizedBox(height: 180),
          const Icon(Icons.campaign_outlined, size: 64),
          const SizedBox(height: 16),
          const Text('Aún no tienes campañas', textAlign: TextAlign.center),
        ],
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
      itemCount: items.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (_, index) {
        final item = items[index];
        return Card(
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => showCampaign(item),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: Theme.of(
                      context,
                    ).colorScheme.primaryContainer,
                    child: const Icon(Icons.auto_awesome),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.title,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          '${item.platform} · ${item.client}',
                          style: TextStyle(
                            color: Theme.of(
                              context,
                            ).colorScheme.onSurfaceVariant,
                          ),
                        ),
                        const SizedBox(height: 8),
                        _StatusChip(item.status),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class CreateCampaignView extends StatefulWidget {
  const CreateCampaignView({
    super.key,
    required this.api,
    required this.onCreated,
  });
  final ApiClient api;
  final ValueChanged<Campaign> onCreated;
  @override
  State<CreateCampaignView> createState() => _CreateCampaignViewState();
}

class _CreateCampaignViewState extends State<CreateCampaignView> {
  final form = GlobalKey<FormState>();
  final title = TextEditingController();
  final clientName = TextEditingController();
  final clientEmail = TextEditingController();
  final prompt = TextEditingController();
  final recorder = AudioRecorder();
  TextEditingController? dictationTarget;
  String dictationTargetLabel = 'instrucciones';
  String industry = 'tecnologia', tone = 'profesional', platform = 'instagram';
  bool listening = false, saving = false;
  String? message;

  Future<void> toggleDictation(
    TextEditingController target,
    String targetLabel,
  ) async {
    if (listening) {
      await finishDictation();
      return;
    }
    final ready = await recorder.hasPermission();
    if (!ready) {
      setState(() => message = 'Activa el permiso de micrófono para dictar.');
      return;
    }
    final temporaryDirectory = await getTemporaryDirectory();
    final path =
        '${temporaryDirectory.path}/nexomark_${DateTime.now().millisecondsSinceEpoch}.m4a';
    dictationTarget = target;
    dictationTargetLabel = targetLabel;
    await recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.aacLc,
        sampleRate: 16000,
        numChannels: 1,
        echoCancel: true,
        noiseSuppress: true,
      ),
      path: path,
    );
    setState(() {
      listening = true;
      message = 'Escuchando $targetLabel… toca detener cuando termines.';
    });
  }

  Future<void> finishDictation() async {
    final path = await recorder.stop();
    if (mounted) {
      setState(() {
        listening = false;
        message = 'Transcribiendo con Gemini…';
      });
    }
    if (path == null || dictationTarget == null) return;
    try {
      final bytes = await File(path).readAsBytes();
      final transcript = await widget.api.geminiTranscription(bytes);
      final controller = dictationTarget!;
      final selection = controller.selection;
      final start = selection.isValid ? selection.start : controller.text.length;
      final end = selection.isValid ? selection.end : start;
      final separator =
          start > 0 && !RegExp(r'\s$').hasMatch(controller.text.substring(0, start))
          ? ' '
          : '';
      final next = controller.text.replaceRange(
        start,
        end,
        '$separator$transcript',
      );
      final cursor = start + separator.length + transcript.length;
      controller
        ..text = next
        ..selection = TextSelection.collapsed(offset: cursor);
      if (mounted) {
        setState(() => message = 'Dictado insertado en $dictationTargetLabel.');
      }
    } catch (error) {
      if (mounted) setState(() => message = error.toString());
    } finally {
      try {
        await File(path).delete();
      } catch (_) {
        // El sistema puede limpiar el archivo temporal si ya no existe.
      }
    }
  }

  Future<void> create() async {
    if (!form.currentState!.validate()) return;
    if (listening) await recorder.stop();
    setState(() {
      saving = true;
      message = null;
    });
    try {
      final campaign = await widget.api.createCampaign(
        CampaignDraft(
          title: title.text.trim(),
          clientName: clientName.text.trim(),
          clientEmail: clientEmail.text.trim(),
          industry: industry,
          tone: tone,
          platform: platform,
          prompt: prompt.text.trim(),
        ),
      );
      widget.onCreated(campaign);
    } catch (e) {
      setState(() => message = e.toString());
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  String? required(String? value) =>
      value == null || value.trim().isEmpty ? 'Completa este campo' : null;

  @override
  void dispose() {
    recorder.dispose();
    title.dispose();
    clientName.dispose();
    clientEmail.dispose();
    prompt.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Form(
    key: form,
    child: ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
      children: [
        Card(
          color: const Color(0xFF242044),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: [
                Icon(
                  listening ? Icons.graphic_eq : Icons.mic,
                  size: 34,
                  color: const Color(0xFFA7A3FF),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        listening ? 'Te estoy escuchando' : 'Crea hablando',
                        style: const TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 18,
                        ),
                      ),
                      const Text(
                        'Dicta la idea y podrás editarla antes de enviarla.',
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: title,
          validator: required,
          decoration: InputDecoration(
            labelText: 'Título de la campaña',
            suffixIcon: IconButton(
              onPressed: () => toggleDictation(title, 'el título'),
              tooltip: 'Dictar título con Gemini',
              icon: Icon(
                listening && identical(dictationTarget, title)
                    ? Icons.stop
                    : Icons.mic,
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: clientName,
          validator: required,
          decoration: InputDecoration(
            labelText: 'Nombre del cliente',
            suffixIcon: IconButton(
              onPressed: () => toggleDictation(clientName, 'el cliente'),
              tooltip: 'Dictar cliente con Gemini',
              icon: Icon(
                listening && identical(dictationTarget, clientName)
                    ? Icons.stop
                    : Icons.mic,
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: clientEmail,
          validator: (value) {
            final base = required(value);
            if (base != null) return base;
            return value!.contains('@') ? null : 'Correo no válido';
          },
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(labelText: 'Correo del cliente'),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _Dropdown(
                label: 'Industria',
                value: industry,
                values: const [
                  'tecnologia',
                  'salud',
                  'educacion',
                  'retail',
                  'gastronomia',
                  'moda',
                  'finanzas',
                  'entretenimiento',
                  'otro',
                ],
                onChanged: (v) => setState(() => industry = v),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _Dropdown(
                label: 'Tono',
                value: tone,
                values: const [
                  'profesional',
                  'casual',
                  'urgente',
                  'inspiracional',
                  'humoristico',
                  'persuasivo',
                ],
                onChanged: (v) => setState(() => tone = v),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _Dropdown(
          label: 'Plataforma',
          value: platform,
          values: const ['instagram', 'facebook', 'linkedin'],
          onChanged: (v) => setState(() => platform = v),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: prompt,
          validator: required,
          minLines: 5,
          maxLines: 9,
          decoration: InputDecoration(
            labelText: 'Describe la campaña',
            hintText:
                'Ejemplo: promociona un nuevo servicio para emprendedores…',
            alignLabelWithHint: true,
            suffixIcon: Padding(
              padding: const EdgeInsets.only(right: 8, bottom: 72),
              child: IconButton.filled(
                onPressed: () => toggleDictation(prompt, 'las instrucciones'),
                tooltip: listening ? 'Detener dictado' : 'Dictar',
                icon: Icon(listening ? Icons.stop : Icons.mic),
              ),
            ),
          ),
        ),
        if (message != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(
              message!,
              style: TextStyle(
                color: listening
                    ? const Color(0xFFA7A3FF)
                    : Theme.of(context).colorScheme.error,
              ),
            ),
          ),
        const SizedBox(height: 20),
        FilledButton.icon(
          onPressed: saving ? null : create,
          icon: saving
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.auto_awesome),
          label: const Padding(
            padding: EdgeInsets.symmetric(vertical: 14),
            child: Text('Crear campaña con IA'),
          ),
        ),
      ],
    ),
  );
}

class CampaignDetailScreen extends StatefulWidget {
  const CampaignDetailScreen({
    super.key,
    required this.api,
    required this.campaign,
  });
  final ApiClient api;
  final Campaign campaign;
  @override
  State<CampaignDetailScreen> createState() => _CampaignDetailScreenState();
}

class _CampaignDetailScreenState extends State<CampaignDetailScreen> {
  final player = AudioPlayer();
  final localTts = FlutterTts();
  bool speaking = false;
  String? voiceMessage;

  Future<void> speak() async {
    final text = widget.campaign.copy.isNotEmpty
        ? widget.campaign.copy
        : widget.campaign.prompt;
    if (speaking) {
      await player.stop();
      await localTts.stop();
      setState(() {
        speaking = false;
        voiceMessage = null;
      });
      return;
    }
    setState(() {
      speaking = true;
      voiceMessage = 'Generando voz con Gemini…';
    });
    try {
      final bytes = await widget.api.geminiSpeech(text);
      await player.play(BytesSource(bytes));
      setState(() => voiceMessage = 'Reproduciendo voz Gemini');
      player.onPlayerComplete.first.then((_) {
        if (mounted) {
          setState(() {
            speaking = false;
            voiceMessage = null;
          });
        }
      });
    } catch (_) {
      await localTts.setLanguage('es-PE');
      await localTts.setSpeechRate(0.48);
      await localTts.speak(text);
      setState(() {
        voiceMessage =
            'Modo demo: voz del dispositivo. Gemini se activará al colocar la API key.';
      });
      localTts.setCompletionHandler(() {
        if (mounted) setState(() => speaking = false);
      });
    }
  }

  @override
  void dispose() {
    player.dispose();
    localTts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final campaign = widget.campaign;
    return Scaffold(
      appBar: AppBar(title: const Text('Detalle de campaña')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  campaign.title,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              _StatusChip(campaign.status),
            ],
          ),
          const SizedBox(height: 16),
          if (campaign.imageBase64?.isNotEmpty == true)
            ClipRRect(
              borderRadius: BorderRadius.circular(18),
              child: Image.memory(
                base64Decode(
                  campaign.imageBase64!.contains(',')
                      ? campaign.imageBase64!.split(',').last
                      : campaign.imageBase64!,
                ),
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Expanded(
                        child: Text(
                          'Copy generado',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      FilledButton.tonalIcon(
                        onPressed: speak,
                        icon: Icon(speaking ? Icons.stop : Icons.volume_up),
                        label: Text(speaking ? 'Detener' : 'Escuchar'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  SelectableText(
                    campaign.copy.isNotEmpty
                        ? campaign.copy
                        : 'El texto todavía se está generando.',
                    style: const TextStyle(fontSize: 16, height: 1.5),
                  ),
                  if (voiceMessage != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 14),
                      child: Text(
                        voiceMessage!,
                        style: const TextStyle(color: Color(0xFFA7A3FF)),
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Información',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 12),
                  Text('Cliente: ${campaign.client}'),
                  Text('Industria: ${campaign.industry}'),
                  Text('Tono: ${campaign.tone}'),
                  Text('Plataforma: ${campaign.platform}'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Dropdown extends StatelessWidget {
  const _Dropdown({
    required this.label,
    required this.value,
    required this.values,
    required this.onChanged,
  });
  final String label, value;
  final List<String> values;
  final ValueChanged<String> onChanged;
  @override
  Widget build(BuildContext context) => DropdownButtonFormField<String>(
    initialValue: value,
    decoration: InputDecoration(labelText: label),
    items: values
        .map((item) => DropdownMenuItem(value: item, child: Text(item)))
        .toList(),
    onChanged: (item) {
      if (item != null) onChanged(item);
    },
  );
}

class _StatusChip extends StatelessWidget {
  const _StatusChip(this.status);
  final String status;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.primaryContainer,
      borderRadius: BorderRadius.circular(20),
    ),
    child: Text(
      status.replaceAll('_', ' '),
      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
    ),
  );
}
