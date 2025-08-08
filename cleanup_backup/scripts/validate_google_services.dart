// Script de validation du google-services.json
// Exécuter avec : dart validate_google_services.dart

import 'dart:io';
import 'dart:convert';

void main() {
  print('🔍 Validation du fichier google-services.json...\n');
  
  final file = File('android/app/google-services.json');
  
  if (!file.existsSync()) {
    print('❌ Fichier google-services.json non trouvé !');
    print('   Chemin attendu: android/app/google-services.json');
    exit(1);
  }
  
  try {
    final content = file.readAsStringSync();
    final json = jsonDecode(content) as Map<String, dynamic>;
    
    print('✅ Fichier JSON valide');
    
    // Vérifications de base
    _validateBasicStructure(json);
    _validateOAuthClients(json);
    _validatePackageName(json);
    _validateAppId(json);
    
    print('\n🎉 Validation terminée avec succès !');
    print('   Google Sign-In devrait maintenant fonctionner correctement.');
    
  } catch (e) {
    print('❌ Erreur lors de la validation: $e');
    exit(1);
  }
}

void _validateBasicStructure(Map<String, dynamic> json) {
  print('\n📋 Vérification de la structure de base...');
  
  // Project info
  final projectInfo = json['project_info'] as Map<String, dynamic>?;
  if (projectInfo == null) {
    throw 'Manque project_info';
  }
  
  final projectId = projectInfo['project_id'] as String?;
  if (projectId != 'kumafire-7864b') {
    throw 'Project ID incorrect: $projectId (attendu: kumafire-7864b)';
  }
  print('   ✅ Project ID: $projectId');
  
  // Client array
  final clients = json['client'] as List?;
  if (clients == null || clients.isEmpty) {
    throw 'Manque configuration client';
  }
  print('   ✅ Configuration client présente');
}

void _validatePackageName(Map<String, dynamic> json) {
  print('\n📦 Vérification du package name...');
  
  final clients = json['client'] as List;
  final client = clients.first as Map<String, dynamic>;
  final clientInfo = client['client_info'] as Map<String, dynamic>;
  final androidInfo = clientInfo['android_client_info'] as Map<String, dynamic>;
  final packageName = androidInfo['package_name'] as String;
  
  if (packageName != 'com.kumacodex.kumacodex') {
    throw 'Package name incorrect: $packageName (attendu: com.kumacodex.kumacodex)';
  }
  print('   ✅ Package name: $packageName');
}

void _validateAppId(Map<String, dynamic> json) {
  print('\n🆔 Vérification de l\'App ID...');
  
  final clients = json['client'] as List;
  final client = clients.first as Map<String, dynamic>;
  final clientInfo = client['client_info'] as Map<String, dynamic>;
  final appId = clientInfo['mobilesdk_app_id'] as String;
  
  if (appId != '1:116620596804:android:c5e03db7c33dcc93170e11') {
    print('   ⚠️  App ID différent: $appId');
    print('       Attendu: 1:116620596804:android:c5e03db7c33dcc93170e11');
    print('       Ceci peut être normal si un nouveau projet a été créé');
  } else {
    print('   ✅ App ID: $appId');
  }
}

void _validateOAuthClients(Map<String, dynamic> json) {
  print('\n🔐 Vérification des clients OAuth...');
  
  final clients = json['client'] as List;
  final client = clients.first as Map<String, dynamic>;
  final oauthClients = client['oauth_client'] as List?;
  
  if (oauthClients == null || oauthClients.isEmpty) {
    throw 'Aucun client OAuth configuré !';
  }
  
  // Collecter les clients par type
  final clientsByType = <int, String>{};
  for (final oauthClient in oauthClients) {
    final clientMap = oauthClient as Map<String, dynamic>;
    final clientId = clientMap['client_id'] as String;
    final clientType = clientMap['client_type'] as int;
    
    clientsByType[clientType] = clientId;
  }
  
  print('   📱 Clients OAuth trouvés:');
  clientsByType.forEach((type, clientId) {
    final typeName = _getClientTypeName(type);
    print('     - Type $type ($typeName): ${clientId.substring(0, 20)}...');
  });
  
  // Vérifications critiques
  if (!clientsByType.containsKey(1)) {
    throw 'CRITIQUE: Manque client OAuth Android (type 1) !';
  }
  
  if (clientsByType.containsKey(1) && clientsByType.containsKey(3)) {
    final androidClientId = clientsByType[1]!;
    final webClientId = clientsByType[3]!;
    
    if (androidClientId == webClientId) {
      throw 'CRITIQUE: Client ID identique pour Android et Web !';
    }
    print('   ✅ Clients Android et Web ont des IDs différents');
  }
  
  print('   ✅ Configuration OAuth correcte');
}

String _getClientTypeName(int type) {
  switch (type) {
    case 1: return 'Android';
    case 2: return 'iOS';
    case 3: return 'Web';
    default: return 'Inconnu';
  }
}