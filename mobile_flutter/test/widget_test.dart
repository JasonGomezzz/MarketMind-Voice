// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';
import 'package:marketmind_mobile/src/models.dart';

void main() {
  test('interpreta una campaña del backend', () {
    final campaign = Campaign.fromJson({
      'id': 2,
      'titulo': 'Demo',
      'estado': 'generado',
    });
    expect(campaign.id, 2);
    expect(campaign.title, 'Demo');
  });
}
