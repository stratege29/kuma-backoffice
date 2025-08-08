#!/usr/bin/env node

/**
 * Kuma Stories Uploader - Version Ultra-Simple
 * Upload direct en TypeScript - Juste 3 fichiers nécessaires
 */

import * as admin from 'firebase-admin';
import * as fs from 'fs';

// Interface minimale pour les histoires
interface KumaStory {
    id: string;
    title: string;
    [key: string]: any; // Permet tous les autres champs
}

interface StoriesData {
    stories: KumaStory[];
}

/**
 * Upload simple et direct vers Firestore
 */
async function uploadKumaStories(): Promise<void> {
    try {
        console.log('🚀 Kuma Uploader - Version Simple');
        console.log('='.repeat(40));

        // 1. Initialiser Firebase
        console.log('📡 Connexion à Firebase...');
        const credentials = JSON.parse(fs.readFileSync('./firebase-credentials.json', 'utf8'));

        admin.initializeApp({
            credential: admin.credential.cert(credentials),
            projectId: credentials.project_id
        });

        const db = admin.firestore();
        console.log(`✅ Connecté au projet: ${credentials.project_id}`);

        // 2. Charger les histoires
        console.log('📚 Chargement des histoires...');
        const storiesData: StoriesData = JSON.parse(
            fs.readFileSync('./kuma_stories_complete.json', 'utf8')
        );

        const stories = storiesData.stories;
        console.log(`✅ ${stories.length} histoires trouvées`);

        // 3. Upload vers Firestore
        console.log('🚀 Upload vers Firestore...');

        let successCount = 0;
        let errorCount = 0;

        for (const story of stories) {
            try {
                await db.collection('stories').doc(story.id).set(story);
                console.log(`✅ ${story.title} (${story.id})`);
                successCount++;
            } catch (error) {
                console.error(`❌ Erreur ${story.title}: ${error}`);
                errorCount++;
            }
        }

        // 4. Résumé
        console.log('\n' + '='.repeat(40));
        console.log('📊 Résumé:');
        console.log(`✅ Réussies: ${successCount}`);
        console.log(`❌ Erreurs: ${errorCount}`);

        if (errorCount === 0) {
            console.log('🎉 Upload terminé avec succès!');
            console.log('🔗 Vérifiez dans Firebase Console');
        } else {
            console.log('⚠️  Upload terminé avec des erreurs');
        }

    } catch (error) {
        console.error('💥 Erreur fatale:', error);
        console.log('\n🔧 Vérifiez:');
        console.log('- firebase-credentials.json existe et est valide');
        console.log('- kuma_stories_complete.json existe et est valide');
        console.log('- Connexion internet');
        process.exit(1);
    }
}

// Mode interactif simple
async function main(): Promise<void> {
    const args = process.argv.slice(2);

    if (args.includes('--help') || args.includes('-h')) {
        console.log(`
🚀 Kuma Uploader Simple - Aide

Usage:
  npx ts-node simple-uploader.ts          # Upload direct
  npx ts-node simple-uploader.ts --dry    # Mode test (bientôt)
  npx ts-node simple-uploader.ts --help   # Cette aide

Fichiers requis:
  - firebase-credentials.json    # Vos credentials Firebase
  - kuma_stories_complete.json   # JSON des histoires Kuma

Installation:
  npm install firebase-admin @types/node typescript ts-node
    `);
        return;
    }

    if (args.includes('--dry')) {
        console.log('🔍 Mode test pas encore implémenté');
        console.log('💡 Utilisez le script complet pour le mode test');
        return;
    }

    // Vérifier que les fichiers existent
    const requiredFiles = ['./firebase-credentials.json', './kuma_stories_complete.json'];
    const missingFiles = requiredFiles.filter(file => !fs.existsSync(file));

    if (missingFiles.length > 0) {
        console.error('❌ Fichiers manquants:');
        missingFiles.forEach(file => console.error(`   - ${file}`));
        console.log('\n💡 Guide rapide:');
        console.log('1. Téléchargez firebase-credentials.json depuis Firebase Console');
        console.log('2. Créez kuma_stories_complete.json avec vos histoires');
        console.log('3. Relancez le script');
        return;
    }

    // Confirmation avant upload
    console.log('⚠️  Vous allez uploader vers Firestore');
    console.log('📁 Fichiers détectés:');
    requiredFiles.forEach(file => console.log(`   ✅ ${file}`));

    console.log('\n🚀 Upload en cours...');
    await uploadKumaStories();
}

// Point d'entrée
if (require.main === module) {
    main().catch(console.error);
}

export { uploadKumaStories };

/* 
UTILISATION ULTRA-RAPIDE:

1. Créer dossier:
   mkdir kuma-quick && cd kuma-quick

2. Installer:
   npm init -y
   npm install firebase-admin @types/node typescript ts-node

3. Créer fichiers:
   - firebase-credentials.json (vos credentials)
   - kuma_stories_complete.json (JSON des histoires)
   - simple-uploader.ts (ce fichier)

4. Lancer:
   npx ts-node simple-uploader.ts

C'est tout! 🎉
*/