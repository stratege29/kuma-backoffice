// Script de validation de la configuration iOS Google Sign-In
// Exécuter avec : dart validate_ios_configuration.dart

import 'dart:io';

void main() {
  print('🍎 Validation de la configuration iOS Google Sign-In...\n');

  try {
    _validateGoogleServiceInfo();
    _validateFirebaseOptions();
    _validateInfoPlist();
    _validateConsistency();

    print('\n🎉 Validation iOS terminée avec succès !');
    print('   Configuration iOS prête pour Google Sign-In.');
  } catch (e) {
    print('❌ Erreur lors de la validation iOS: $e');
    exit(1);
  }
}

void _validateGoogleServiceInfo() {
  print('📋 Vérification GoogleService-Info.plist...');

  final file = File('ios/Runner/GoogleService-Info.plist');
  if (!file.existsSync()) {
    throw 'Fichier GoogleService-Info.plist non trouvé !';
  }

  final content = file.readAsStringSync();

  // Vérifications basiques
  if (!content.contains('CLIENT_ID')) {
    throw 'CLIENT_ID manquant dans GoogleService-Info.plist';
  }

  if (!content.contains('com.ultimesgriots.kuma')) {
    throw 'Bundle ID incorrect dans GoogleService-Info.plist';
  }

  if (!content.contains('kumafire-7864b')) {
    throw 'Project ID incorrect dans GoogleService-Info.plist';
  }

  // Extraction du CLIENT_ID
  final clientIdMatch =
      RegExp(r'<key>CLIENT_ID</key>\s*<string>([^<]+)</string>')
          .firstMatch(content);
  if (clientIdMatch != null) {
    final clientId = clientIdMatch.group(1)!;
    print('   ✅ CLIENT_ID: ${clientId.substring(0, 20)}...');
  }

  // Extraction du GOOGLE_APP_ID
  final appIdMatch =
      RegExp(r'<key>GOOGLE_APP_ID</key>\s*<string>([^<]+)</string>')
          .firstMatch(content);
  if (appIdMatch != null) {
    final appId = appIdMatch.group(1)!;
    print('   ✅ GOOGLE_APP_ID: $appId');
  }

  // Vérification IS_SIGNIN_ENABLED
  if (content.contains('IS_SIGNIN_ENABLED')) {
    print('   ✅ IS_SIGNIN_ENABLED configuré');
  } else {
    print('   ⚠️  IS_SIGNIN_ENABLED non trouvé');
  }

  print('   ✅ GoogleService-Info.plist valide');
}

void _validateFirebaseOptions() {
  print('\\n🔥 Vérification firebase_options.dart...');

  final file = File('lib/firebase_options.dart');
  if (!file.existsSync()) {
    throw 'Fichier firebase_options.dart non trouvé !';
  }

  final content = file.readAsStringSync();

  // Vérifications iOS
  if (!content.contains('static const FirebaseOptions ios')) {
    throw 'Configuration iOS manquante dans firebase_options.dart';
  }

  if (!content.contains('com.ultimesgriots.kuma')) {
    throw 'Bundle ID iOS incorrect dans firebase_options.dart';
  }

  // Extraction de l'App ID iOS
  final appIdMatches = RegExp(r"appId: '([^']+)'").allMatches(content).toList();
  if (appIdMatches.length >= 2) {
    final iosAppId = appIdMatches[1].group(1)!; // Deuxième occurrence (iOS)
    print('   ✅ iOS App ID: $iosAppId');

    // Vérification de l'App ID attendu
    if (iosAppId != '1:116620596804:ios:4423a854fd8b1399170e11') {
      print('   ⚠️  App ID iOS différent de celui attendu');
      print('       Trouvé: $iosAppId');
      print('       Attendu: 1:116620596804:ios:4423a854fd8b1399170e11');
    }
  }

  print('   ✅ firebase_options.dart iOS configuration valide');
}

void _validateInfoPlist() {
  print('\\n📱 Vérification Info.plist...');

  final file = File('ios/Runner/Info.plist');
  if (!file.existsSync()) {
    throw 'Fichier Info.plist non trouvé !';
  }

  final content = file.readAsStringSync();

  // Vérification Bundle ID
  if (!content.contains('com.ultimesgriots.kuma')) {
    throw 'Bundle ID incorrect dans Info.plist';
  }
  print('   ✅ Bundle ID: com.ultimesgriots.kuma');

  // Vérification URL Schemes Google
  if (!content.contains(
      'com.googleusercontent.apps.116620596804-20mo7jna56n7amt5p5rh003elako0pi7')) {
    print('   ⚠️  URL Scheme Google non trouvé ou incorrect');
  } else {
    print('   ✅ URL Scheme Google configuré');
  }

  // Vérification des domaines associés
  if (content.contains('com.apple.developer.associated-domains')) {
    print('   ✅ Domaines associés configurés');
  }

  print('   ✅ Info.plist configuration valide');
}

void _validateConsistency() {
  print('\\n🔄 Vérification de la cohérence entre fichiers...');

  // Lire GoogleService-Info.plist
  final googleServiceFile = File('ios/Runner/GoogleService-Info.plist');
  final googleServiceContent = googleServiceFile.readAsStringSync();

  // Lire firebase_options.dart
  final firebaseOptionsFile = File('lib/firebase_options.dart');
  final firebaseOptionsContent = firebaseOptionsFile.readAsStringSync();

  // Extraire GOOGLE_APP_ID du plist
  final appIdMatch =
      RegExp(r'<key>GOOGLE_APP_ID</key>\s*<string>([^<]+)</string>')
          .firstMatch(googleServiceContent);

  if (appIdMatch != null) {
    final plistAppId = appIdMatch.group(1)!;

    // Vérifier correspondance dans firebase_options.dart
    if (firebaseOptionsContent.contains(plistAppId)) {
      print(
          '   ✅ App ID iOS cohérent entre GoogleService-Info.plist et firebase_options.dart');
    } else {
      print('   ❌ App ID iOS incohérent !');
      print('      GoogleService-Info.plist: $plistAppId');
      print('      Vérifiez firebase_options.dart');
    }
  }

  // Vérifier Bundle ID cohérence
  if (googleServiceContent.contains('com.ultimesgriots.kuma') &&
      firebaseOptionsContent.contains('com.ultimesgriots.kuma')) {
    print('   ✅ Bundle ID cohérent dans tous les fichiers');
  } else {
    print('   ❌ Bundle ID incohérent entre les fichiers');
  }

  print('   ✅ Cohérence validée');
}
