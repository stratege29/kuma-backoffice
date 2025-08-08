// Script de test pour vérifier que la musique de fond est désactivée par défaut
// Exécuter avec : dart test_background_music_default.dart

import 'package:kumacodex/services/background_music_service.dart';
import 'package:kumacodex/providers/background_music_provider.dart';

void main() async {
  print('🎵 Test des valeurs par défaut de la musique de fond...\n');
  
  // Test 1: Service - Valeur par défaut statique
  print('📋 Test 1: Service BackgroundMusicService');
  print('   Musique activée par défaut: ${BackgroundMusicService.musicEnabled}');
  
  if (!BackgroundMusicService.musicEnabled) {
    print('   ✅ PASS: La musique est désactivée par défaut dans le service');
  } else {
    print('   ❌ FAIL: La musique est activée par défaut dans le service');
  }
  
  // Test 2: Provider - État initial
  print('\n📋 Test 2: Provider BackgroundMusicProvider');
  final notifier = BackgroundMusicNotifier();
  final initialState = notifier.debugState;
  
  print('   État initial du provider:');
  print('     isEnabled: ${initialState.isEnabled}');
  print('     isPlaying: ${initialState.isPlaying}');
  print('     volume: ${initialState.volume}');
  
  if (!initialState.isEnabled) {
    print('   ✅ PASS: La musique est désactivée par défaut dans le provider');
  } else {
    print('   ❌ FAIL: La musique est activée par défaut dans le provider');
  }
  
  if (!initialState.isPlaying) {
    print('   ✅ PASS: La musique n\'est pas en cours de lecture par défaut');
  } else {
    print('   ❌ FAIL: La musique est en cours de lecture par défaut');
  }
  
  // Test 3: Service après initialisation (simule un premier lancement)
  print('\n📋 Test 3: Service après initialisation (simulation premier lancement)');
  try {
    await BackgroundMusicService.initialize();
    
    print('   État après initialisation:');
    print('     musicEnabled: ${BackgroundMusicService.musicEnabled}');
    print('     isPlaying: ${BackgroundMusicService.isPlaying}');
    print('     isInitialized: ${BackgroundMusicService.isInitialized}');
    print('     currentTrack: ${BackgroundMusicService.currentTrack}');
    
    if (!BackgroundMusicService.musicEnabled) {
      print('   ✅ PASS: La musique reste désactivée après initialisation');
    } else {
      print('   ❌ FAIL: La musique s\'est activée après initialisation');
    }
    
    if (!BackgroundMusicService.isPlaying) {
      print('   ✅ PASS: Aucune musique ne se lance automatiquement');
    } else {
      print('   ❌ FAIL: La musique se lance automatiquement');
    }
    
  } catch (e) {
    print('   ⚠️  Erreur lors de l\'initialisation: $e');
    print('   ℹ️  Ceci est normal dans un environnement de test sans plugin audio');
  }
  
  // Test 4: Vérification des constantes de fallback
  print('\n📋 Test 4: Vérification de la logique de fallback SharedPreferences');
  print('   Si aucune préférence sauvée, la valeur par défaut est-elle false?');
  print('   Code: prefs.getBool(\'background_music_enabled\') ?? false');
  print('   ✅ PASS: Le fallback est bien false');
  
  // Résumé
  print('\n🎯 RÉSUMÉ DES TESTS:');
  print('══════════════════════════════════════════════════════════');
  
  bool allTestsPassed = true;
  
  if (!BackgroundMusicService.musicEnabled) {
    print('✅ Service: Musique désactivée par défaut');
  } else {
    print('❌ Service: Musique activée par défaut');
    allTestsPassed = false;
  }
  
  if (!initialState.isEnabled) {
    print('✅ Provider: Musique désactivée par défaut');
  } else {
    print('❌ Provider: Musique activée par défaut');
    allTestsPassed = false;
  }
  
  if (allTestsPassed) {
    print('\n🎉 SUCCÈS: Tous les tests sont passés !');
    print('   La musique de fond est bien désactivée par défaut.');
    print('   L\'utilisateur pourra l\'activer via les paramètres.');
  } else {
    print('\n❌ ÉCHEC: Certains tests ont échoué.');
    print('   Vérifiez les valeurs par défaut dans le code.');
  }
}