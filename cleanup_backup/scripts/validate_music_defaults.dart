// Script de validation des valeurs par défaut de la musique de fond
// Exécuter avec : dart validate_music_defaults.dart

import 'dart:io';

void main() {
  print('🎵 Validation des valeurs par défaut de la musique de fond...\n');
  
  bool allTestsPassed = true;
  
  // Test 1: Vérifier BackgroundMusicService
  print('📋 Test 1: Vérification de BackgroundMusicService');
  final serviceFile = File('lib/services/background_music_service.dart');
  final serviceContent = serviceFile.readAsStringSync();
  
  // Vérifier la variable statique _musicEnabled
  if (serviceContent.contains('static bool _musicEnabled = false;')) {
    print('   ✅ PASS: _musicEnabled défini à false par défaut');
  } else if (serviceContent.contains('static bool _musicEnabled = true;')) {
    print('   ❌ FAIL: _musicEnabled défini à true par défaut');
    allTestsPassed = false;
  } else {
    print('   ⚠️  WARNING: _musicEnabled non trouvé ou format inattendu');
    allTestsPassed = false;
  }
  
  // Vérifier le fallback dans _loadPreferences
  if (serviceContent.contains("prefs.getBool('background_music_enabled') ?? false")) {
    print('   ✅ PASS: Fallback SharedPreferences défini à false');
  } else if (serviceContent.contains("prefs.getBool('background_music_enabled') ?? true")) {
    print('   ❌ FAIL: Fallback SharedPreferences défini à true');
    allTestsPassed = false;
  } else {
    print('   ⚠️  WARNING: Fallback SharedPreferences non trouvé ou format inattendu');
    allTestsPassed = false;
  }
  
  // Test 2: Vérifier BackgroundMusicProvider
  print('\n📋 Test 2: Vérification de BackgroundMusicProvider');
  final providerFile = File('lib/providers/background_music_provider.dart');
  final providerContent = providerFile.readAsStringSync();
  
  // Vérifier l'état initial dans le constructeur
  if (providerContent.contains('isEnabled: false,')) {
    print('   ✅ PASS: État initial isEnabled défini à false');
  } else if (providerContent.contains('isEnabled: true,')) {
    print('   ❌ FAIL: État initial isEnabled défini à true');
    allTestsPassed = false;
  } else {
    print('   ⚠️  WARNING: État initial isEnabled non trouvé ou format inattendu');
    allTestsPassed = false;
  }
  
  // Test 3: Vérifier qu'il n'y a pas de démarrage automatique
  print('\n📋 Test 3: Vérification absence de démarrage automatique');
  
  // Vérifier ensureMusicPlaying a bien la garde _musicEnabled
  if (serviceContent.contains('if (!_isSupported || !_musicEnabled) return;')) {
    print('   ✅ PASS: ensureMusicPlaying() vérifie _musicEnabled avant de démarrer');
  } else {
    print('   ❌ FAIL: ensureMusicPlaying() ne vérifie pas _musicEnabled');
    allTestsPassed = false;
  }
  
  // Test 4: Vérifier l'interface utilisateur
  print('\n📋 Test 4: Vérification de l\'interface utilisateur');
  final settingsFile = File('lib/screens/settings_screen.dart');
  final settingsContent = settingsFile.readAsStringSync();
  
  if (settingsContent.contains('SwitchListTile') && 
      settingsContent.contains('Musique de fond') &&
      settingsContent.contains('musicState.isEnabled')) {
    print('   ✅ PASS: Interface utilisateur pour contrôler la musique trouvée');
  } else {
    print('   ❌ FAIL: Interface utilisateur pour contrôler la musique non trouvée');
    allTestsPassed = false;
  }
  
  // Résumé final
  print('\n🎯 RÉSUMÉ DE LA VALIDATION:');
  print('══════════════════════════════════════════════════════════');
  
  if (allTestsPassed) {
    print('🎉 SUCCÈS: Toutes les validations sont passées !');
    print('');
    print('✅ La musique de fond est DÉSACTIVÉE par défaut');
    print('✅ Aucun démarrage automatique de musique');
    print('✅ L\'utilisateur peut activer la musique via les paramètres');
    print('✅ Interface utilisateur disponible pour contrôler la musique');
    print('');
    print('📱 Expérience utilisateur optimisée :');
    print('   • Premier lancement : Silence (non intrusif)');
    print('   • Utilisateur peut activer selon ses préférences');
    print('   • Contrôles disponibles dans les paramètres');
  } else {
    print('❌ ÉCHEC: Certaines validations ont échoué.');
    print('   Vérifiez les points mentionnés ci-dessus.');
  }
}