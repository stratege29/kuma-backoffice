#!/usr/bin/env python3
"""
🧪 Tests complets du système d'upload d'images et audio du backoffice Kuma.

Couvre tous les scénarios :
- Optimisation d'images (formats, tailles, modes couleur, EXIF)
- Upload audio brut (pas d'optimisation)
- Nommage structuré par pays
- Extraction du countryCode multipart
- Gestion d'erreurs (fichiers vides, corrompus, mauvais Content-Type)
- Réponses JSON cohérentes
- Intégration avec Firebase Storage mock
"""

import sys
import os
import io
import json
import uuid
import unittest
import urllib.parse
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageOps, ExifTags


# ─────────────────────────────────────────────────────────
# Helpers : création de données multipart et images test
# ─────────────────────────────────────────────────────────

def make_test_image(width=1600, height=900, mode='RGB', format='JPEG', exif_rotate=False):
    """Crée une image test en mémoire et retourne les bytes."""
    if mode == 'RGBA':
        img = Image.new('RGBA', (width, height), (255, 0, 0, 128))
    elif mode == 'P':
        img = Image.new('P', (width, height))
    elif mode == 'LA':
        img = Image.new('LA', (width, height), (128, 200))
    elif mode == 'L':
        img = Image.new('L', (width, height), 128)
    elif mode == 'CMYK':
        img = Image.new('CMYK', (width, height), (0, 128, 255, 0))
    else:
        img = Image.new('RGB', (width, height), (100, 150, 200))

    buf = io.BytesIO()

    if exif_rotate and format == 'JPEG' and mode == 'RGB':
        # Créer une image avec orientation EXIF (rotation 90°)
        import struct
        img.save(buf, format=format, quality=95)
        buf.seek(0)
        # On ne peut pas facilement injecter de l'EXIF pur avec Pillow
        # mais on teste au moins que exif_transpose ne crash pas
        return buf.getvalue()

    if mode == 'P' and format == 'JPEG':
        img = img.convert('RGB')
    if mode == 'RGBA' and format == 'JPEG':
        img = img.convert('RGB')
    if mode == 'LA' and format == 'JPEG':
        img = img.convert('RGB')
    if mode == 'CMYK' and format == 'PNG':
        img = img.convert('RGB')

    img.save(buf, format=format)
    return buf.getvalue()


def make_test_audio(size_bytes=1024, filename_hint='test.mp3'):
    """Crée des données audio factices (pas un vrai fichier audio)."""
    # Header MP3 minimal factice
    return b'\xff\xfb\x90\x00' + os.urandom(size_bytes - 4)


def build_multipart(fields, boundary='----TestBoundary123'):
    """
    Construit un body multipart/form-data.

    fields: liste de dicts :
      - {'name': 'countryCode', 'value': 'KE'}  -> champ texte
      - {'name': 'imageFile', 'filename': 'photo.jpg', 'data': bytes, 'content_type': 'image/jpeg'}
    """
    parts = []
    for field in fields:
        part = b'--' + boundary.encode() + b'\r\n'
        if 'filename' in field:
            part += (
                f'Content-Disposition: form-data; name="{field["name"]}"; '
                f'filename="{field["filename"]}"\r\n'
            ).encode()
            ct = field.get('content_type', 'application/octet-stream')
            part += f'Content-Type: {ct}\r\n'.encode()
            part += b'\r\n'
            part += field['data']
        else:
            part += f'Content-Disposition: form-data; name="{field["name"]}"\r\n'.encode()
            part += b'\r\n'
            part += field['value'].encode()
        part += b'\r\n'
        parts.append(part)

    body = b''.join(parts) + b'--' + boundary.encode() + b'--\r\n'
    content_type = f'multipart/form-data; boundary={boundary}'
    return body, content_type


class MockHandler:
    """
    Simule KumaFirebaseHTTPHandler pour tester handle_file_upload()
    sans démarrer un vrai serveur HTTP.
    """

    def __init__(self, content_type='', firebase_initialized=True):
        self.headers = {'content-type': content_type, 'Content-Type': content_type}
        self.response_code = None
        self.response_body = None

        # Mock firebase_manager
        self.firebase_manager = MagicMock()
        self.firebase_manager.initialized = firebase_initialized
        self.firebase_manager.upload_file_to_storage = MagicMock(
            side_effect=self._mock_upload
        )

        # Track les appels upload
        self.uploaded_calls = []

    def _mock_upload(self, file_data, filename, folder):
        """Simule un upload Firebase réussi."""
        self.uploaded_calls.append({
            'data': file_data,
            'filename': filename,
            'folder': folder,
            'size': len(file_data),
        })
        return f'https://storage.googleapis.com/test-bucket/{folder}/{filename}'

    def send_json_response(self, data, status=200):
        self.response_code = status
        self.response_body = data

    def send_error_response(self, code, message):
        self.response_code = code
        self.response_body = {'success': False, 'error': message}

    def send_response(self, code):
        self.response_code = code

    def send_header(self, key, value):
        pass

    def end_headers(self):
        pass


def run_upload(handler, raw_data):
    """
    Appelle handle_file_upload sur le handler mock avec les bons imports injectés.
    On ré-implémente la logique ici en important directement du fichier source.
    """
    # Import dynamique de la classe
    from firebase_web_backoffice import KumaFirebaseHTTPHandler

    # Bind la méthode au mock handler
    import types
    handler.handle_file_upload = types.MethodType(
        KumaFirebaseHTTPHandler.handle_file_upload, handler
    )
    handler.handle_file_upload(raw_data)


# ─────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────

class TestImageUploadOptimization(unittest.TestCase):
    """Tests d'optimisation des images lors de l'upload."""

    def test_jpeg_to_webp_conversion(self):
        """Upload JPG → doit être converti en WebP."""
        img_data = make_test_image(1600, 900, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'KE'},
            {'name': 'imageFile', 'filename': 'photo.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        self.assertTrue(handler.response_body['success'])
        self.assertEqual(len(handler.uploaded_calls), 1)

        call = handler.uploaded_calls[0]
        self.assertTrue(call['filename'].endswith('.webp'), f"Filename should end with .webp: {call['filename']}")
        self.assertIn('_cover.webp', call['filename'])

        # Vérifier que c'est bien du WebP
        result_img = Image.open(io.BytesIO(call['data']))
        self.assertEqual(result_img.format, 'WEBP')

    def test_png_to_webp_conversion(self):
        """Upload PNG → converti en WebP."""
        img_data = make_test_image(1200, 800, 'RGB', 'PNG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'cover.png', 'data': img_data, 'content_type': 'image/png'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        self.assertIn('_cover.webp', call['filename'])

    def test_image_resize_respects_max_dimensions(self):
        """Image > 800x450 doit être réduite proportionnellement (thumbnail)."""
        img_data = make_test_image(3000, 2000, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'big.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        w, h = result_img.size
        # thumbnail garde le ratio, chaque dimension <= max
        self.assertLessEqual(w, 800)
        self.assertLessEqual(h, 450)

    def test_small_image_not_upscaled(self):
        """Image plus petite que 800x450 ne doit PAS être agrandie."""
        img_data = make_test_image(400, 200, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'small.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        w, h = result_img.size
        # thumbnail ne scale pas vers le haut
        self.assertLessEqual(w, 400)
        self.assertLessEqual(h, 200)

    def test_landscape_image_ratio_preserved(self):
        """Image paysage : ratio préservé après thumbnail."""
        img_data = make_test_image(1600, 400, 'RGB', 'JPEG')  # très large
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'wide.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        w, h = result_img.size
        self.assertLessEqual(w, 800)
        # Le ratio original est 4:1, la hauteur doit être bien inférieure à 450
        self.assertLessEqual(h, 250)

    def test_portrait_image_ratio_preserved(self):
        """Image portrait : ratio préservé, hauteur contrainte à 450."""
        img_data = make_test_image(400, 1200, 'RGB', 'JPEG')  # portrait
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'tall.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        w, h = result_img.size
        self.assertLessEqual(h, 450)
        self.assertLessEqual(w, 800)

    def test_image_size_reduction(self):
        """L'image optimisée doit être significativement plus petite."""
        img_data = make_test_image(2000, 1500, 'RGB', 'JPEG')
        original_size = len(img_data)
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'heavy.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        optimized_size = call['size']
        self.assertLess(optimized_size, original_size,
                        f"Optimized ({optimized_size}B) should be smaller than original ({original_size}B)")

    def test_webp_input_still_optimized(self):
        """Un WebP en entrée est quand même re-traité (resize + re-encode)."""
        img_data = make_test_image(2000, 1500, 'RGB', 'WEBP')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'already.webp', 'data': img_data, 'content_type': 'image/webp'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        self.assertIn('_cover.webp', call['filename'])
        result_img = Image.open(io.BytesIO(call['data']))
        self.assertLessEqual(result_img.size[0], 800)


class TestImageColorModes(unittest.TestCase):
    """Tests de conversion des différents modes couleur."""

    def test_rgba_to_rgb_white_background(self):
        """RGBA → RGB avec fond blanc (pas de transparence dans WebP final)."""
        img_data = make_test_image(800, 450, 'RGBA', 'PNG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'transparent.png', 'data': img_data, 'content_type': 'image/png'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        # WebP peut être RGB ou RGBA, mais notre code force RGB
        self.assertIn(result_img.mode, ('RGB', 'YCbCr'))

    def test_palette_mode_p(self):
        """Mode palette (P) → converti correctement en RGB."""
        img = Image.new('P', (600, 400))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()

        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'palette.png', 'data': img_data, 'content_type': 'image/png'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)

    def test_grayscale_l_mode(self):
        """Mode niveaux de gris (L) → converti en RGB."""
        img = Image.new('L', (600, 400), 128)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()

        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'grayscale.png', 'data': img_data, 'content_type': 'image/png'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        self.assertEqual(result_img.format, 'WEBP')

    def test_la_mode_with_alpha(self):
        """Mode LA (grayscale + alpha) → RGB avec fond blanc."""
        img_data = make_test_image(600, 400, 'LA', 'PNG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'gray_alpha.png', 'data': img_data, 'content_type': 'image/png'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)

    def test_gif_to_webp(self):
        """GIF (mode P) → converti en WebP."""
        img = Image.new('P', (300, 200))
        buf = io.BytesIO()
        img.save(buf, format='GIF')
        img_data = buf.getvalue()

        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'animation.gif', 'data': img_data, 'content_type': 'image/gif'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        self.assertIn('_cover.webp', call['filename'])


class TestImageExifHandling(unittest.TestCase):
    """Tests de gestion de l'orientation EXIF."""

    def test_exif_transpose_no_crash(self):
        """Image avec données EXIF ne doit pas crasher."""
        img_data = make_test_image(800, 600, 'RGB', 'JPEG', exif_rotate=True)
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'rotated.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        self.assertTrue(handler.response_body['success'])

    def test_image_without_exif(self):
        """Image PNG (pas d'EXIF) traitée sans erreur."""
        img_data = make_test_image(800, 600, 'RGB', 'PNG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'no_exif.png', 'data': img_data, 'content_type': 'image/png'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)


class TestAudioUpload(unittest.TestCase):
    """Tests de l'upload audio (pas d'optimisation)."""

    def test_mp3_uploaded_raw(self):
        """MP3 uploadé sans modification."""
        audio_data = make_test_audio(2048, 'song.mp3')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'SN'},
            {'name': 'audioFile', 'filename': 'histoire.mp3', 'data': audio_data, 'content_type': 'audio/mpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        # Audio : pas de conversion, le nom original est dans le filename
        self.assertIn('histoire.mp3', call['filename'])
        self.assertNotIn('cover.webp', call['filename'])
        # Données brutes non modifiées
        self.assertEqual(call['data'], audio_data)

    def test_wav_uploaded_raw(self):
        """WAV uploadé sans modification."""
        audio_data = make_test_audio(4096)
        body, ct = build_multipart([
            {'name': 'audioFile', 'filename': 'narration.wav', 'data': audio_data, 'content_type': 'audio/wav'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        self.assertIn('narration.wav', call['filename'])
        self.assertEqual(call['data'], audio_data)

    def test_m4a_uploaded_raw(self):
        """M4A uploadé sans modification."""
        audio_data = make_test_audio(3000)
        body, ct = build_multipart([
            {'name': 'audioFile', 'filename': 'voice.m4a', 'data': audio_data, 'content_type': 'audio/mp4'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        self.assertIn('voice.m4a', call['filename'])

    def test_ogg_uploaded_raw(self):
        """OGG uploadé sans modification."""
        audio_data = make_test_audio(2000)
        body, ct = build_multipart([
            {'name': 'audioFile', 'filename': 'conte.ogg', 'data': audio_data, 'content_type': 'audio/ogg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        self.assertIn('conte.ogg', call['filename'])


class TestCountryCodeNaming(unittest.TestCase):
    """Tests du nommage structuré par pays."""

    def test_image_path_with_country_code(self):
        """Image stockée dans stories/{CC}/..._cover.webp."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'KE'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'stories/KE')
        self.assertIn('_cover.webp', call['filename'])

    def test_audio_path_with_country_code(self):
        """Audio stocké dans stories/{CC}/..."""
        audio_data = make_test_audio(1024)
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'SN'},
            {'name': 'audioFile', 'filename': 'conte.mp3', 'data': audio_data, 'content_type': 'audio/mpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'stories/SN')

    def test_default_country_code_xx(self):
        """Sans countryCode → défaut 'XX'."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'stories/XX')

    def test_country_code_lowercased_input(self):
        """countryCode en minuscules → converti en majuscules."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'bf'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'stories/BF')

    def test_invalid_country_code_too_long(self):
        """countryCode > 2 chars → ignoré, défaut XX."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'KENYA'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'stories/XX')

    def test_invalid_country_code_numeric(self):
        """countryCode numérique → ignoré, défaut XX."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': '12'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'stories/XX')

    def test_empty_country_code(self):
        """countryCode vide → défaut XX."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': ''},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'stories/XX')

    def test_single_char_country_code(self):
        """countryCode 1 char → ignoré, défaut XX."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'K'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'stories/XX')


class TestFilenameStructure(unittest.TestCase):
    """Tests du format de nommage des fichiers uploadés."""

    def test_image_filename_format(self):
        """Image : {timestamp}_{uuid8}_cover.webp"""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'CI'},
            {'name': 'imageFile', 'filename': 'photo_vacances.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        filename = call['filename']
        # Format attendu : YYYYMMDD_HHMMSS_{8hex}_cover.webp
        parts = filename.split('_')
        self.assertEqual(len(parts[0]), 8, "Date should be 8 chars (YYYYMMDD)")
        self.assertEqual(len(parts[1]), 6, "Time should be 6 chars (HHMMSS)")
        self.assertEqual(len(parts[2]), 8, "UUID should be 8 hex chars")
        self.assertTrue(filename.endswith('_cover.webp'))

    def test_audio_filename_preserves_original_name(self):
        """Audio : {timestamp}_{uuid8}_{original_filename}"""
        audio_data = make_test_audio(1024)
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'GH'},
            {'name': 'audioFile', 'filename': 'anansi_story.mp3', 'data': audio_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        filename = call['filename']
        self.assertTrue(filename.endswith('_anansi_story.mp3'))

    def test_unknown_extension_goes_to_media_folder(self):
        """Extension inconnue → dossier 'media'."""
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'KE'},
            {'name': 'file', 'filename': 'document.pdf', 'data': b'%PDF-fake', 'content_type': 'application/pdf'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'media')


class TestErrorHandling(unittest.TestCase):
    """Tests de gestion d'erreurs."""

    def test_wrong_content_type(self):
        """Content-Type non multipart → erreur 400."""
        handler = MockHandler(content_type='application/json')
        run_upload(handler, b'{"file": "data"}')

        self.assertEqual(handler.response_code, 400)
        self.assertFalse(handler.response_body['success'])
        self.assertIn('multipart', handler.response_body['error'].lower())

    def test_no_files_in_multipart(self):
        """Multipart sans fichier → erreur 400."""
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'KE'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 400)
        self.assertIn('Aucun fichier', handler.response_body['error'])

    def test_empty_file_data(self):
        """Fichier avec 0 bytes → ignoré, aucun upload."""
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'empty.jpg', 'data': b'', 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 400)
        self.assertEqual(len(handler.uploaded_calls), 0)

    def test_corrupted_image_fallback_to_raw(self):
        """Image corrompue → fallback upload brut (log warning)."""
        corrupt_data = b'NOT_AN_IMAGE_AT_ALL_JUST_RANDOM_BYTES' * 100
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'corrupt.jpg', 'data': corrupt_data, 'content_type': 'image/jpeg'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        # L'upload doit quand même réussir (fallback brut)
        self.assertEqual(handler.response_code, 200)
        self.assertTrue(handler.response_body['success'])
        call = handler.uploaded_calls[0]
        # Le filename est quand même _cover.webp (nommage décidé avant l'optimisation)
        self.assertIn('_cover.webp', call['filename'])
        # Mais les données sont les données brutes (non optimisées)
        self.assertEqual(call['data'], corrupt_data)

    def test_empty_filename_ignored(self):
        """Filename vide → part ignorée."""
        boundary = '----TestBound'
        # Construire manuellement un part avec filename=""
        part = (
            f'------{boundary}\r\n'
            f'Content-Disposition: form-data; name="imageFile"; filename=""\r\n'
            f'Content-Type: image/jpeg\r\n'
            f'\r\n'
            f'some data\r\n'
            f'------{boundary}--\r\n'
        ).encode()

        handler = MockHandler(content_type=f'multipart/form-data; boundary=----{boundary}')
        run_upload(handler, part)

        self.assertEqual(handler.response_code, 400)

    def test_firebase_upload_failure(self):
        """Firebase retourne None → fichier pas dans la réponse."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        handler.firebase_manager.upload_file_to_storage = MagicMock(return_value=None)
        run_upload(handler, body)

        # Pas de fichier uploadé avec succès → erreur
        self.assertEqual(handler.response_code, 400)
        self.assertIn('Aucun fichier', handler.response_body['error'])


class TestResponseFormat(unittest.TestCase):
    """Tests du format des réponses JSON."""

    def test_success_response_structure(self):
        """Réponse succès contient success, message, files[]."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'KE'},
            {'name': 'imageFile', 'filename': 'test.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        resp = handler.response_body
        self.assertIn('success', resp)
        self.assertTrue(resp['success'])
        self.assertIn('message', resp)
        self.assertIn('files', resp)
        self.assertIsInstance(resp['files'], list)
        self.assertGreater(len(resp['files']), 0)

    def test_file_entry_structure(self):
        """Chaque fichier dans la réponse a field, filename, url, type."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'photo.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        file_entry = handler.response_body['files'][0]
        self.assertIn('field', file_entry)
        self.assertIn('filename', file_entry)
        self.assertIn('url', file_entry)
        self.assertIn('type', file_entry)

    def test_image_type_is_webp_after_optimization(self):
        """Le type retourné pour une image optimisée est file/webp."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'photo.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        file_entry = handler.response_body['files'][0]
        self.assertEqual(file_entry['type'], 'file/webp')

    def test_audio_type_preserved(self):
        """Le type audio est préservé (file/mp3, file/wav, etc.)."""
        audio_data = make_test_audio(1024)
        body, ct = build_multipart([
            {'name': 'audioFile', 'filename': 'narration.mp3', 'data': audio_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        file_entry = handler.response_body['files'][0]
        self.assertEqual(file_entry['type'], 'file/mp3')

    def test_url_contains_country_and_filename(self):
        """L'URL retournée contient le dossier pays et le filename."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'BW'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        url = handler.response_body['files'][0]['url']
        self.assertIn('stories/BW/', url)
        self.assertIn('_cover.webp', url)

    def test_error_response_structure(self):
        """Réponse erreur contient success=false et error."""
        handler = MockHandler(content_type='application/json')
        run_upload(handler, b'{}')

        resp = handler.response_body
        self.assertFalse(resp['success'])
        self.assertIn('error', resp)

    def test_message_count_multiple_files(self):
        """Message indique le nombre de fichiers uploadés."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        audio_data = make_test_audio(1024)
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'KE'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data},
            {'name': 'audioFile', 'filename': 'story.mp3', 'data': audio_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        self.assertIn('2 fichier(s)', handler.response_body['message'])
        self.assertEqual(len(handler.response_body['files']), 2)


class TestMultipartParsing(unittest.TestCase):
    """Tests du parsing multipart."""

    def test_country_code_before_file(self):
        """countryCode envoyé AVANT le fichier → correctement extrait."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'NG'},
            {'name': 'imageFile', 'filename': 'img.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.uploaded_calls[0]['folder'], 'stories/NG')

    def test_country_code_after_file(self):
        """countryCode envoyé APRÈS le fichier → correctement extrait (2 passes)."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'img.jpg', 'data': img_data},
            {'name': 'countryCode', 'value': 'GH'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.uploaded_calls[0]['folder'], 'stories/GH')

    def test_multiple_files_same_country(self):
        """Plusieurs fichiers → même countryCode pour tous."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        audio_data = make_test_audio(512)
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'CI'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data},
            {'name': 'audioFile', 'filename': 'narr.mp3', 'data': audio_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(len(handler.uploaded_calls), 2)
        self.assertEqual(handler.uploaded_calls[0]['folder'], 'stories/CI')
        self.assertEqual(handler.uploaded_calls[1]['folder'], 'stories/CI')

    def test_unicode_filename(self):
        """Filename avec caractères unicode → traité sans crash."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'café_été.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)

    def test_filename_with_spaces(self):
        """Filename avec espaces → traité correctement."""
        audio_data = make_test_audio(1024)
        body, ct = build_multipart([
            {'name': 'audioFile', 'filename': 'mon histoire préférée.mp3', 'data': audio_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        self.assertIn('mon histoire préférée.mp3', call['filename'])


class TestEdgeCases(unittest.TestCase):
    """Tests de cas limites."""

    def test_1x1_pixel_image(self):
        """Image 1x1 pixel → optimisée sans erreur."""
        img_data = make_test_image(1, 1, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'tiny.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        self.assertEqual(result_img.size, (1, 1))  # thumbnail ne scale pas vers le haut

    def test_very_large_image_dimensions(self):
        """Image 8000x6000 → réduite à max 800x450."""
        # Utiliser une image plus petite mais vérifier le ratio
        img_data = make_test_image(4000, 3000, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'huge.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        w, h = result_img.size
        self.assertLessEqual(w, 800)
        self.assertLessEqual(h, 450)

    def test_square_image(self):
        """Image carrée → redimensionnée proportionnellement."""
        img_data = make_test_image(2000, 2000, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'square.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        w, h = result_img.size
        self.assertLessEqual(w, 800)
        self.assertLessEqual(h, 450)
        # Carré → contraint par la hauteur (450), largeur = 450 aussi
        self.assertEqual(w, h)

    def test_exact_max_size_image(self):
        """Image exactement 800x450 → pas de redimensionnement."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'perfect.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        call = handler.uploaded_calls[0]
        result_img = Image.open(io.BytesIO(call['data']))
        self.assertEqual(result_img.size, (800, 450))

    def test_file_without_extension(self):
        """Fichier sans extension → dossier 'media'."""
        body, ct = build_multipart([
            {'name': 'file', 'filename': 'noextension', 'data': b'some binary data here'},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        self.assertEqual(handler.response_code, 200)
        call = handler.uploaded_calls[0]
        self.assertEqual(call['folder'], 'media')


class TestConsoleOutput(unittest.TestCase):
    """Tests des messages de log/console."""

    def test_optimization_log_printed(self):
        """Le log d'optimisation est imprimé avec les tailles."""
        img_data = make_test_image(2000, 1500, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'photo.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)

        with patch('builtins.print') as mock_print:
            run_upload(handler, body)

        # Chercher le log d'optimisation
        optimization_logs = [
            call for call in mock_print.call_args_list
            if 'Image optimisée' in str(call)
        ]
        self.assertEqual(len(optimization_logs), 1, "Devrait y avoir exactement 1 log d'optimisation")
        log_msg = str(optimization_logs[0])
        self.assertIn('KB', log_msg)
        self.assertIn('→', log_msg)

    def test_corrupted_image_warning_logged(self):
        """Image corrompue → log d'avertissement."""
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'bad.jpg', 'data': b'NOT_AN_IMAGE' * 50},
        ])
        handler = MockHandler(content_type=ct)

        with patch('builtins.print') as mock_print:
            run_upload(handler, body)

        warning_logs = [
            call for call in mock_print.call_args_list
            if 'Optimisation image' in str(call) and 'échouée' in str(call)
        ]
        self.assertEqual(len(warning_logs), 1, "Devrait y avoir 1 log d'avertissement pour image corrompue")


class TestFirebaseStorageIntegration(unittest.TestCase):
    """Tests d'intégration avec Firebase Storage (mockée)."""

    def test_upload_called_with_correct_mime_path(self):
        """upload_file_to_storage appelé avec le bon dossier."""
        img_data = make_test_image(800, 450, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'BF'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        handler.firebase_manager.upload_file_to_storage.assert_called_once()
        args = handler.firebase_manager.upload_file_to_storage.call_args
        self.assertEqual(args[0][2], 'stories/BF')  # 3ème arg = folder

    def test_url_from_firebase_returned_to_client(self):
        """L'URL retournée par Firebase est bien dans la réponse JSON."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'test.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        url = handler.response_body['files'][0]['url']
        self.assertTrue(url.startswith('https://storage.googleapis.com/'))
        self.assertIn('stories/XX/', url)


# ─────────────────────────────────────────────────────────
# Tests de doublons stories et nomenclature souvenirs
# ─────────────────────────────────────────────────────────

class MockStoryHandler:
    """Simule le handler HTTP pour tester handle_create_story et handle_update_story."""

    def __init__(self, existing_stories=None, save_returns=(True, 'new_id_123')):
        self.headers = {}
        self.response_code = None
        self.response_body = None

        self.firebase_manager = MagicMock()
        self.firebase_manager.get_stories = MagicMock(return_value=existing_stories or [])
        self.firebase_manager.save_story = MagicMock(return_value=save_returns)
        self.firebase_manager.update_story = MagicMock(return_value=(True, 'story_ke_001'))
        self.firebase_manager.get_story_by_id = MagicMock(return_value=None)

        # Mock security_manager
        self.security_manager = MagicMock()
        self.security_manager.update_activity = MagicMock()

    def send_json_response(self, data, status=200):
        self.response_code = status
        self.response_body = data

    def send_error_response(self, code, message):
        self.response_code = code
        self.response_body = {'success': False, 'error': message}


def run_create_story(handler, post_data):
    """Appelle handle_create_story sur le handler mock."""
    from firebase_web_backoffice import KumaFirebaseHTTPHandler
    import types
    handler._check_story_duplicate = types.MethodType(
        KumaFirebaseHTTPHandler._check_story_duplicate, handler
    )
    handler.handle_create_story = types.MethodType(
        KumaFirebaseHTTPHandler.handle_create_story, handler
    )
    handler.handle_create_story(post_data)


def run_update_story(handler, story_id, post_data):
    """Appelle handle_update_story sur le handler mock."""
    from firebase_web_backoffice import KumaFirebaseHTTPHandler
    import types
    handler._check_story_duplicate = types.MethodType(
        KumaFirebaseHTTPHandler._check_story_duplicate, handler
    )
    handler.handle_update_story = types.MethodType(
        KumaFirebaseHTTPHandler.handle_update_story, handler
    )
    handler.handle_update_story(story_id, post_data)


def make_story_form_data(**overrides):
    """Construit un post_data de formulaire d'histoire."""
    defaults = {
        'title': 'Anansi et le serpent',
        'country': 'Ghana',
        'countryCode': 'GH',
        'estimatedReadingTime': '10',
        'estimatedAudioDuration': '600',
        'content_fr': 'Il était une fois...',
        'content_en': 'Once upon a time...',
        'imageUrl': 'https://example.com/img.webp',
        'audioUrl': 'https://example.com/audio.mp3',
        'values': 'courage,sagesse',
        'tags': 'animaux,leçon',
        'isPublished': 'false',
        'order': '1',
        'quizQuestionsJson': '[]',
        'author': 'Tradition orale',
        'origin': 'Ghana',
        'moralLesson': 'La ruse ne paie pas',
        'keywords': 'anansi,serpent',
        'ageGroup': '6-9',
        'difficulty': 'Easy',
        'region': 'Afrique de l\'Ouest',
    }
    defaults.update(overrides)
    return urllib.parse.urlencode(defaults)


class TestStoryDuplicateDetection(unittest.TestCase):
    """Tests de détection de doublons lors de la création d'histoires."""

    def test_no_duplicate_creates_story(self):
        """Titre unique → histoire créée normalement."""
        handler = MockStoryHandler(existing_stories=[])
        run_create_story(handler, make_story_form_data())

        self.assertEqual(handler.response_code, 200)
        self.assertTrue(handler.response_body['success'])
        handler.firebase_manager.save_story.assert_called_once()

    def test_duplicate_title_same_country_blocked(self):
        """Même titre + même pays → erreur 409."""
        existing = [{'title': 'Anansi et le serpent', 'countryCode': 'GH'}]
        handler = MockStoryHandler(existing_stories=existing)
        run_create_story(handler, make_story_form_data(
            title='Anansi et le serpent', countryCode='GH'
        ))

        self.assertEqual(handler.response_code, 409)
        self.assertFalse(handler.response_body['success'])
        self.assertIn('existe déjà', handler.response_body['error'])
        handler.firebase_manager.save_story.assert_not_called()

    def test_duplicate_title_case_insensitive(self):
        """Doublon détecté même avec casse différente."""
        existing = [{'title': 'anansi et le serpent', 'countryCode': 'GH'}]
        handler = MockStoryHandler(existing_stories=existing)
        run_create_story(handler, make_story_form_data(
            title='ANANSI ET LE SERPENT', countryCode='GH'
        ))

        self.assertEqual(handler.response_code, 409)

    def test_same_title_different_country_allowed(self):
        """Même titre mais pays différent → autorisé."""
        existing = [{'title': 'Anansi et le serpent', 'countryCode': 'GH'}]
        handler = MockStoryHandler(existing_stories=existing)
        run_create_story(handler, make_story_form_data(
            title='Anansi et le serpent', countryCode='NG'  # Nigeria, pas Ghana
        ))

        self.assertEqual(handler.response_code, 200)
        handler.firebase_manager.save_story.assert_called_once()

    def test_different_title_same_country_allowed(self):
        """Titre différent même pays → autorisé."""
        existing = [{'title': 'Anansi et le serpent', 'countryCode': 'GH'}]
        handler = MockStoryHandler(existing_stories=existing)
        run_create_story(handler, make_story_form_data(
            title='Le lion et la souris', countryCode='GH'
        ))

        self.assertEqual(handler.response_code, 200)
        handler.firebase_manager.save_story.assert_called_once()

    def test_duplicate_with_whitespace_variations(self):
        """Doublon détecté même avec espaces en plus."""
        existing = [{'title': '  Anansi et le serpent  ', 'countryCode': 'GH'}]
        handler = MockStoryHandler(existing_stories=existing)
        run_create_story(handler, make_story_form_data(
            title='Anansi et le serpent', countryCode='GH'
        ))

        self.assertEqual(handler.response_code, 409)

    def test_multiple_existing_stories_checks_all(self):
        """Vérification contre toutes les histoires existantes."""
        existing = [
            {'title': 'Histoire A', 'countryCode': 'KE'},
            {'title': 'Histoire B', 'countryCode': 'SN'},
            {'title': 'Le lièvre malin', 'countryCode': 'BF'},
        ]
        handler = MockStoryHandler(existing_stories=existing)
        run_create_story(handler, make_story_form_data(
            title='Le lièvre malin', countryCode='BF'
        ))

        self.assertEqual(handler.response_code, 409)

    def test_empty_title_rejected_before_duplicate_check(self):
        """Titre vide → rejeté par la validation serveur (400) avant toute vérification de doublon."""
        existing = [{'title': '', 'countryCode': 'KE'}]
        handler = MockStoryHandler(existing_stories=existing)
        run_create_story(handler, make_story_form_data(title='', countryCode='KE'))

        self.assertEqual(handler.response_code, 400)
        handler.firebase_manager.save_story.assert_not_called()

    def test_duplicate_error_message_includes_title_and_country(self):
        """Le message d'erreur contient le titre et le code pays."""
        existing = [{'title': 'Le baobab magique', 'countryCode': 'SN'}]
        handler = MockStoryHandler(existing_stories=existing)
        run_create_story(handler, make_story_form_data(
            title='Le baobab magique', countryCode='SN'
        ))

        error_msg = handler.response_body['error']
        self.assertIn('Le baobab magique', error_msg)
        self.assertIn('SN', error_msg)


class TestStoryServerValidation(unittest.TestCase):
    """Tests de validation côté serveur des champs requis."""

    def test_empty_title_rejected(self):
        """Titre vide → erreur 400."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(title=''))

        self.assertEqual(handler.response_code, 400)
        self.assertIn('titre', handler.response_body['error'].lower())
        handler.firebase_manager.save_story.assert_not_called()

    def test_whitespace_only_title_rejected(self):
        """Titre avec uniquement des espaces → erreur 400."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(title='   '))

        self.assertEqual(handler.response_code, 400)
        handler.firebase_manager.save_story.assert_not_called()

    def test_invalid_country_code_rejected(self):
        """countryCode invalide → erreur 400."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(countryCode='123'))

        self.assertEqual(handler.response_code, 400)
        self.assertIn('code pays', handler.response_body['error'].lower())

    def test_single_char_country_code_rejected(self):
        """countryCode 1 char → erreur 400."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(countryCode='K'))

        self.assertEqual(handler.response_code, 400)

    def test_three_char_country_code_rejected(self):
        """countryCode 3 chars → erreur 400."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(countryCode='KEN'))

        self.assertEqual(handler.response_code, 400)

    def test_empty_content_fr_rejected(self):
        """Contenu français vide → erreur 400."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(content_fr=''))

        self.assertEqual(handler.response_code, 400)
        self.assertIn('français', handler.response_body['error'].lower())

    def test_invalid_reading_time_uses_default(self):
        """estimatedReadingTime non-numérique → fallback à 10."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(estimatedReadingTime='abc'))

        self.assertEqual(handler.response_code, 200)
        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(saved['estimatedReadingTime'], 10)

    def test_invalid_order_uses_default(self):
        """order non-numérique → fallback à 0."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(order='xyz'))

        self.assertEqual(handler.response_code, 200)
        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(saved['order'], 0)

    def test_invalid_quiz_json_uses_empty(self):
        """quizQuestionsJson malformé → fallback à []."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson='{broken json'))

        self.assertEqual(handler.response_code, 200)
        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(saved['quizQuestions'], [])

    def test_valid_story_all_fields(self):
        """Histoire valide avec tous les champs → succès + tous les champs corrects."""
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(
            title='Le lion et la souris',
            country='Kenya',
            countryCode='KE',
            content_fr='Il était une fois un lion...',
            content_en='Once upon a time a lion...',
            estimatedReadingTime='15',
            estimatedAudioDuration='900',
            values='courage,sagesse',
            tags='animaux',
            isPublished='true',
            order='3',
        ))

        self.assertEqual(handler.response_code, 200)
        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(saved['title'], 'Le lion et la souris')
        self.assertEqual(saved['countryCode'], 'KE')
        self.assertEqual(saved['content']['fr'], 'Il était une fois un lion...')
        self.assertEqual(saved['estimatedReadingTime'], 15)
        self.assertEqual(saved['order'], 3)
        self.assertTrue(saved['isPublished'])
        self.assertEqual(saved['values'], ['courage', 'sagesse'])


class TestStoryUpdateDuplicate(unittest.TestCase):
    """Tests de vérification de doublon lors de la mise à jour."""

    def test_update_same_title_same_story_allowed(self):
        """Renommer une histoire avec le même titre → autorisé (c'est elle-même)."""
        existing = [
            {'id': 'story_ke_001', 'title': 'Le lion', 'countryCode': 'KE',
             'content': {'fr': 'texte', 'en': ''}, 'estimatedReadingTime': 10,
             'estimatedAudioDuration': 600, 'order': 1, 'metadata': {}},
        ]
        handler = MockStoryHandler(existing_stories=existing)
        handler.firebase_manager.get_story_by_id = MagicMock(return_value=existing[0])
        run_update_story(handler, 'story_ke_001', make_story_form_data(
            title='Le lion', countryCode='KE'
        ))

        self.assertEqual(handler.response_code, 200)

    def test_update_rename_to_duplicate_blocked(self):
        """Renommer une histoire vers un titre qui existe pour le même pays → 409."""
        existing = [
            {'id': 'story_ke_001', 'title': 'Le lion', 'countryCode': 'KE',
             'content': {'fr': 'texte', 'en': ''}, 'estimatedReadingTime': 10,
             'estimatedAudioDuration': 600, 'order': 1, 'metadata': {}},
            {'id': 'story_ke_002', 'title': 'La girafe', 'countryCode': 'KE',
             'content': {'fr': 'texte2', 'en': ''}, 'estimatedReadingTime': 10,
             'estimatedAudioDuration': 600, 'order': 2, 'metadata': {}},
        ]
        handler = MockStoryHandler(existing_stories=existing)
        handler.firebase_manager.get_story_by_id = MagicMock(return_value=existing[0])
        # Essayer de renommer story_ke_001 "Le lion" → "La girafe" (déjà pris par story_ke_002)
        run_update_story(handler, 'story_ke_001', make_story_form_data(
            title='La girafe', countryCode='KE'
        ))

        self.assertEqual(handler.response_code, 409)
        handler.firebase_manager.update_story.assert_not_called()

    def test_update_rename_to_same_title_different_country_allowed(self):
        """Renommer vers un titre existant mais pour un autre pays → autorisé."""
        existing = [
            {'id': 'story_ke_001', 'title': 'Le lion', 'countryCode': 'KE',
             'content': {'fr': 'texte', 'en': ''}, 'estimatedReadingTime': 10,
             'estimatedAudioDuration': 600, 'order': 1, 'metadata': {}},
            {'id': 'story_sn_001', 'title': 'La girafe', 'countryCode': 'SN',
             'content': {'fr': 'texte2', 'en': ''}, 'estimatedReadingTime': 10,
             'estimatedAudioDuration': 600, 'order': 1, 'metadata': {}},
        ]
        handler = MockStoryHandler(existing_stories=existing)
        handler.firebase_manager.get_story_by_id = MagicMock(return_value=existing[0])
        # Renommer story_ke_001 → "La girafe" pour KE (l'existant est pour SN)
        run_update_story(handler, 'story_ke_001', make_story_form_data(
            title='La girafe', countryCode='KE'
        ))

        self.assertEqual(handler.response_code, 200)

    def test_update_nonexistent_story_404(self):
        """Mise à jour d'une histoire inexistante → 404."""
        handler = MockStoryHandler()
        handler.firebase_manager.get_story_by_id = MagicMock(return_value=None)
        run_update_story(handler, 'story_ke_999', make_story_form_data())

        self.assertEqual(handler.response_code, 404)

    def test_update_invalid_numeric_fields_use_existing(self):
        """Champs numériques invalides dans update → garder les valeurs existantes."""
        existing_story = {
            'id': 'story_ke_001', 'title': 'Le lion', 'countryCode': 'KE',
            'content': {'fr': 'texte', 'en': ''}, 'estimatedReadingTime': 15,
            'estimatedAudioDuration': 800, 'order': 5, 'metadata': {},
            'quizQuestions': [],
        }
        handler = MockStoryHandler(existing_stories=[existing_story])
        handler.firebase_manager.get_story_by_id = MagicMock(return_value=existing_story)
        run_update_story(handler, 'story_ke_001', make_story_form_data(
            estimatedReadingTime='not_a_number',
            estimatedAudioDuration='bad',
            order='xyz',
        ))

        self.assertEqual(handler.response_code, 200)
        saved = handler.firebase_manager.update_story.call_args[0][1]
        self.assertEqual(saved['estimatedReadingTime'], 15)
        self.assertEqual(saved['estimatedAudioDuration'], 800)
        self.assertEqual(saved['order'], 5)


class TestQuizValidation(unittest.TestCase):
    """Tests de validation et assainissement des quiz questions."""

    def test_valid_quiz_stored_correctly(self):
        """Quiz valide → stocké tel quel."""
        quiz = json.dumps([{
            'id': 'q_abc123',
            'question': 'Quel animal?',
            'options': ['Lion', 'Zèbre', 'Girafe', 'Éléphant'],
            'correctAnswer': 2,
            'explanation': 'La girafe est le héros'
        }])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        self.assertEqual(handler.response_code, 200)
        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(len(saved['quizQuestions']), 1)
        q = saved['quizQuestions'][0]
        self.assertEqual(q['question'], 'Quel animal?')
        self.assertEqual(q['correctAnswer'], 2)
        self.assertEqual(q['options'], ['Lion', 'Zèbre', 'Girafe', 'Éléphant'])

    def test_correct_answer_out_of_range_clamped(self):
        """correctAnswer > 3 → ramené à 0."""
        quiz = json.dumps([{
            'id': 'q_1', 'question': 'Test?',
            'options': ['A', 'B', 'C', 'D'],
            'correctAnswer': 7,  # invalide
            'explanation': ''
        }])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(saved['quizQuestions'][0]['correctAnswer'], 0)

    def test_negative_correct_answer_clamped(self):
        """correctAnswer < 0 → ramené à 0."""
        quiz = json.dumps([{
            'id': 'q_1', 'question': 'Test?',
            'options': ['A', 'B', 'C', 'D'],
            'correctAnswer': -1,
            'explanation': ''
        }])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(saved['quizQuestions'][0]['correctAnswer'], 0)

    def test_correct_answer_string_clamped(self):
        """correctAnswer string au lieu de int → ramené à 0."""
        quiz = json.dumps([{
            'id': 'q_1', 'question': 'Test?',
            'options': ['A', 'B', 'C', 'D'],
            'correctAnswer': 'two',
            'explanation': ''
        }])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(saved['quizQuestions'][0]['correctAnswer'], 0)

    def test_empty_question_text_filtered(self):
        """Question avec texte vide → filtrée."""
        quiz = json.dumps([
            {'id': 'q_1', 'question': '', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 0, 'explanation': ''},
            {'id': 'q_2', 'question': 'Valide?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 1, 'explanation': ''},
        ])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(len(saved['quizQuestions']), 1)
        self.assertEqual(saved['quizQuestions'][0]['question'], 'Valide?')

    def test_wrong_number_of_options_filtered(self):
        """Question avec != 4 options → filtrée."""
        quiz = json.dumps([
            {'id': 'q_1', 'question': 'Trop peu?', 'options': ['A', 'B'], 'correctAnswer': 0, 'explanation': ''},
            {'id': 'q_2', 'question': 'OK?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 0, 'explanation': ''},
        ])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(len(saved['quizQuestions']), 1)
        self.assertEqual(saved['quizQuestions'][0]['question'], 'OK?')

    def test_non_dict_quiz_entry_filtered(self):
        """Entrée non-dict dans le tableau → filtrée."""
        quiz = json.dumps([
            "not a dict",
            42,
            {'id': 'q_1', 'question': 'Valide?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 0, 'explanation': ''},
        ])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(len(saved['quizQuestions']), 1)

    def test_missing_id_gets_generated(self):
        """Question sans id → id auto-généré."""
        quiz = json.dumps([{
            'question': 'Sans ID?',
            'options': ['A', 'B', 'C', 'D'],
            'correctAnswer': 1,
            'explanation': 'test'
        }])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertTrue(saved['quizQuestions'][0]['id'].startswith('q_'))

    def test_options_converted_to_strings(self):
        """Options non-string → converties en string."""
        quiz = json.dumps([{
            'id': 'q_1', 'question': 'Chiffres?',
            'options': [1, 2, 3, 4],
            'correctAnswer': 0,
            'explanation': ''
        }])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(saved['quizQuestions'][0]['options'], ['1', '2', '3', '4'])

    def test_multiple_valid_questions_preserved(self):
        """3 questions valides → toutes les 3 stockées."""
        quiz = json.dumps([
            {'id': 'q_1', 'question': 'Q1?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 0, 'explanation': 'E1'},
            {'id': 'q_2', 'question': 'Q2?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 1, 'explanation': 'E2'},
            {'id': 'q_3', 'question': 'Q3?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 3, 'explanation': 'E3'},
        ])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(len(saved['quizQuestions']), 3)
        self.assertEqual(saved['quizQuestions'][2]['correctAnswer'], 3)

    def test_quiz_with_special_characters(self):
        """Questions avec accents, apostrophes, guillemets → OK."""
        quiz = json.dumps([{
            'id': 'q_1',
            'question': "Qu'est-ce que l'éléphant a dit?",
            'options': ["C'est vrai", 'L"autre', 'Réponse à "trouver"', 'Ça marche!'],
            'correctAnswer': 0,
            'explanation': "L'éléphant a dit la vérité"
        }])
        handler = MockStoryHandler()
        run_create_story(handler, make_story_form_data(quizQuestionsJson=quiz))

        saved = handler.firebase_manager.save_story.call_args[0][0]
        self.assertEqual(len(saved['quizQuestions']), 1)
        self.assertIn("l'éléphant", saved['quizQuestions'][0]['question'])

    def test_update_quiz_validation_applies(self):
        """La validation quiz s'applique aussi en mode update."""
        existing_story = {
            'id': 'story_ke_001', 'title': 'Le lion', 'countryCode': 'KE',
            'content': {'fr': 'texte', 'en': ''}, 'estimatedReadingTime': 10,
            'estimatedAudioDuration': 600, 'order': 1, 'metadata': {},
            'quizQuestions': [{'id': 'q_old', 'question': 'Old?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 0, 'explanation': ''}],
        }
        quiz = json.dumps([
            {'id': 'q_1', 'question': 'Valide?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 5, 'explanation': ''},
            {'id': 'q_2', 'question': '', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 0, 'explanation': ''},
        ])
        handler = MockStoryHandler(existing_stories=[existing_story])
        handler.firebase_manager.get_story_by_id = MagicMock(return_value=existing_story)
        run_update_story(handler, 'story_ke_001', make_story_form_data(
            quizQuestionsJson=quiz
        ))

        self.assertEqual(handler.response_code, 200)
        saved = handler.firebase_manager.update_story.call_args[0][1]
        # Seule la question valide reste, correctAnswer ramené à 0
        self.assertEqual(len(saved['quizQuestions']), 1)
        self.assertEqual(saved['quizQuestions'][0]['correctAnswer'], 0)

    def test_empty_quiz_json_keeps_existing_on_update(self):
        """Quiz JSON vide lors d'un update → garder les quiz existants."""
        existing_story = {
            'id': 'story_ke_001', 'title': 'Le lion', 'countryCode': 'KE',
            'content': {'fr': 'texte', 'en': ''}, 'estimatedReadingTime': 10,
            'estimatedAudioDuration': 600, 'order': 1, 'metadata': {},
            'quizQuestions': [{'id': 'q_old', 'question': 'Existante?', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': 2, 'explanation': ''}],
        }
        handler = MockStoryHandler(existing_stories=[existing_story])
        handler.firebase_manager.get_story_by_id = MagicMock(return_value=existing_story)
        run_update_story(handler, 'story_ke_001', make_story_form_data(
            quizQuestionsJson=''
        ))

        self.assertEqual(handler.response_code, 200)
        saved = handler.firebase_manager.update_story.call_args[0][1]
        # Quiz existant préservé
        self.assertEqual(len(saved['quizQuestions']), 1)
        self.assertEqual(saved['quizQuestions'][0]['question'], 'Existante?')


class TestSouvenirNomenclature(unittest.TestCase):
    """Tests de la numérotation séquentielle des souvenirs."""

    def _make_mock_firebase(self, existing_souvenirs):
        """Crée un FirebaseManager mockée avec des souvenirs existants."""
        fm = MagicMock()
        fm.initialized = True
        fm.get_souvenirs_by_country = MagicMock(return_value=existing_souvenirs)
        fm.db = MagicMock()
        mock_doc_ref = MagicMock()
        fm.db.collection.return_value.document.return_value = mock_doc_ref
        mock_doc_ref.set = MagicMock()
        return fm

    def _run_save_souvenir(self, fm, souvenir_data):
        """Appelle save_souvenir depuis le vrai code."""
        from firebase_web_backoffice import FirebaseManager
        import types
        fm.save_souvenir = types.MethodType(FirebaseManager.save_souvenir, fm)
        return fm.save_souvenir(souvenir_data)

    def test_first_souvenir_gets_001(self):
        """Premier souvenir d'un pays → {CC}_001."""
        fm = self._make_mock_firebase([])
        success, msg = self._run_save_souvenir(fm, {
            'countryCode': 'KE',
            'title': 'Premier souvenir',
        })
        self.assertTrue(success)
        # Vérifier l'ID dans l'appel .set()
        call_args = fm.db.collection.return_value.document.call_args
        self.assertEqual(call_args[0][0], 'KE_001')

    def test_sequential_numbering(self):
        """Souvenirs numérotés séquentiellement."""
        existing = [
            {'souvenirId': 'SN_001', 'countryCode': 'SN'},
            {'souvenirId': 'SN_002', 'countryCode': 'SN'},
        ]
        fm = self._make_mock_firebase(existing)
        self._run_save_souvenir(fm, {'countryCode': 'SN', 'title': 'Nouveau'})

        call_args = fm.db.collection.return_value.document.call_args
        self.assertEqual(call_args[0][0], 'SN_003')

    def test_gap_after_deletion_no_collision(self):
        """Après suppression d'un souvenir, pas de collision.
        Si on a [001, 003] (002 supprimé), le prochain doit être 004, pas 003."""
        existing = [
            {'souvenirId': 'GH_001', 'countryCode': 'GH'},
            {'souvenirId': 'GH_003', 'countryCode': 'GH'},
        ]
        fm = self._make_mock_firebase(existing)
        self._run_save_souvenir(fm, {'countryCode': 'GH', 'title': 'Nouveau'})

        call_args = fm.db.collection.return_value.document.call_args
        self.assertEqual(call_args[0][0], 'GH_004')

    def test_single_remaining_high_number(self):
        """Seul souvenir restant a un numéro élevé → le suivant est +1."""
        existing = [
            {'souvenirId': 'BF_010', 'countryCode': 'BF'},
        ]
        fm = self._make_mock_firebase(existing)
        self._run_save_souvenir(fm, {'countryCode': 'BF', 'title': 'Nouveau'})

        call_args = fm.db.collection.return_value.document.call_args
        self.assertEqual(call_args[0][0], 'BF_011')

    def test_provided_souvenir_id_preserved(self):
        """Si souvenirId fourni → pas de renumérotation."""
        fm = self._make_mock_firebase([])
        self._run_save_souvenir(fm, {
            'souvenirId': 'CUSTOM_ID',
            'countryCode': 'KE',
            'title': 'Custom',
        })

        call_args = fm.db.collection.return_value.document.call_args
        self.assertEqual(call_args[0][0], 'CUSTOM_ID')

    def test_country_code_uppercased(self):
        """countryCode en minuscules → ID en majuscules."""
        fm = self._make_mock_firebase([])
        self._run_save_souvenir(fm, {'countryCode': 'ci', 'title': 'Test'})

        call_args = fm.db.collection.return_value.document.call_args
        self.assertEqual(call_args[0][0], 'CI_001')

    def test_default_country_code_xx(self):
        """Pas de countryCode → défaut XX."""
        fm = self._make_mock_firebase([])
        self._run_save_souvenir(fm, {'title': 'Sans pays'})

        call_args = fm.db.collection.return_value.document.call_args
        self.assertEqual(call_args[0][0], 'XX_001')

    def test_malformed_existing_ids_ignored(self):
        """IDs existants malformés → ignorés dans le calcul du max."""
        existing = [
            {'souvenirId': 'KE_002', 'countryCode': 'KE'},
            {'souvenirId': 'KE_bad', 'countryCode': 'KE'},   # non-numérique
            {'souvenirId': 'INVALID', 'countryCode': 'KE'},   # pas de _
        ]
        fm = self._make_mock_firebase(existing)
        self._run_save_souvenir(fm, {'countryCode': 'KE', 'title': 'Nouveau'})

        call_args = fm.db.collection.return_value.document.call_args
        self.assertEqual(call_args[0][0], 'KE_003')

    def test_timestamps_set_on_new_souvenir(self):
        """Nouveau souvenir → createdAt et updatedAt ajoutés."""
        fm = self._make_mock_firebase([])
        self._run_save_souvenir(fm, {'countryCode': 'NG', 'title': 'Test'})

        saved_data = fm.db.collection.return_value.document.return_value.set.call_args[0][0]
        self.assertIn('createdAt', saved_data)
        self.assertIn('updatedAt', saved_data)

    def test_updated_at_set_on_existing_souvenir(self):
        """Mise à jour d'un souvenir existant → updatedAt mis à jour."""
        fm = self._make_mock_firebase([])
        self._run_save_souvenir(fm, {
            'souvenirId': 'KE_001',
            'countryCode': 'KE',
            'title': 'Mis à jour',
        })

        saved_data = fm.db.collection.return_value.document.return_value.set.call_args[0][0]
        self.assertIn('updatedAt', saved_data)


class TestStoryNomenclature(unittest.TestCase):
    """Tests de la nomenclature séquentielle des IDs d'histoires : story_{cc}_{nnn}."""

    def _make_mock_firebase(self, existing_stories):
        """Crée un FirebaseManager mocké avec des histoires existantes."""
        fm = MagicMock()
        fm.initialized = True
        fm.get_stories = MagicMock(return_value=existing_stories)
        fm.db = MagicMock()
        mock_doc_ref = MagicMock()
        fm.db.collection.return_value.document.return_value = mock_doc_ref
        mock_doc_ref.set = MagicMock()
        return fm

    def _run_save_story(self, fm, story_data):
        """Appelle save_story depuis le vrai code."""
        from firebase_web_backoffice import FirebaseManager
        import types
        fm.save_story = types.MethodType(FirebaseManager.save_story, fm)
        return fm.save_story(story_data)

    def test_first_story_for_country_gets_001(self):
        """Première histoire Kenya → story_ke_001."""
        fm = self._make_mock_firebase([])
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'KE', 'title': 'Le lion'
        })
        self.assertTrue(success)
        self.assertEqual(story_id, 'story_ke_001')

    def test_second_story_gets_002(self):
        """Deuxième histoire Kenya → story_ke_002."""
        existing = [{'id': 'story_ke_001', 'countryCode': 'KE', 'title': 'Le lion'}]
        fm = self._make_mock_firebase(existing)
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'KE', 'title': 'Le léopard'
        })
        self.assertEqual(story_id, 'story_ke_002')

    def test_third_story_gets_003(self):
        """Troisième histoire → story_ke_003."""
        existing = [
            {'id': 'story_ke_001', 'countryCode': 'KE'},
            {'id': 'story_ke_002', 'countryCode': 'KE'},
        ]
        fm = self._make_mock_firebase(existing)
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'KE', 'title': 'La girafe'
        })
        self.assertEqual(story_id, 'story_ke_003')

    def test_different_countries_independent_numbering(self):
        """Pays différents → numérotation indépendante."""
        existing = [
            {'id': 'story_ke_001', 'countryCode': 'KE'},
            {'id': 'story_ke_002', 'countryCode': 'KE'},
            {'id': 'story_sn_001', 'countryCode': 'SN'},
        ]
        fm = self._make_mock_firebase(existing)
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'SN', 'title': 'Leuk le lièvre'
        })
        self.assertEqual(story_id, 'story_sn_002')

    def test_gap_after_deletion_no_collision(self):
        """Après suppression : [001, 003] → prochain = 004, pas 003."""
        existing = [
            {'id': 'story_gh_001', 'countryCode': 'GH'},
            {'id': 'story_gh_003', 'countryCode': 'GH'},
        ]
        fm = self._make_mock_firebase(existing)
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'GH', 'title': 'Anansi'
        })
        self.assertEqual(story_id, 'story_gh_004')

    def test_country_code_lowercased_in_id(self):
        """Le countryCode dans l'ID est en minuscules."""
        fm = self._make_mock_firebase([])
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'BF', 'title': 'Le lièvre malin'
        })
        self.assertEqual(story_id, 'story_bf_001')
        self.assertTrue(story_id.islower() or story_id[-3:].isdigit())

    def test_invalid_country_code_uses_xx(self):
        """countryCode invalide → XX."""
        fm = self._make_mock_firebase([])
        success, story_id = self._run_save_story(fm, {
            'countryCode': '123', 'title': 'Test'
        })
        self.assertEqual(story_id, 'story_xx_001')

    def test_empty_country_code_uses_xx(self):
        """countryCode vide → XX."""
        fm = self._make_mock_firebase([])
        success, story_id = self._run_save_story(fm, {
            'countryCode': '', 'title': 'Test'
        })
        self.assertEqual(story_id, 'story_xx_001')

    def test_missing_country_code_uses_xx(self):
        """Pas de countryCode → XX."""
        fm = self._make_mock_firebase([])
        success, story_id = self._run_save_story(fm, {
            'title': 'Test sans pays'
        })
        self.assertEqual(story_id, 'story_xx_001')

    def test_story_id_stored_in_data(self):
        """L'ID généré est aussi stocké dans story_data['id']."""
        fm = self._make_mock_firebase([])
        self._run_save_story(fm, {'countryCode': 'CI', 'title': 'Test'})

        saved_data = fm.db.collection.return_value.document.return_value.set.call_args[0][0]
        self.assertEqual(saved_data['id'], 'story_ci_001')

    def test_firestore_document_uses_structured_id(self):
        """Le document Firestore utilise l'ID structuré."""
        fm = self._make_mock_firebase([])
        self._run_save_story(fm, {'countryCode': 'NG', 'title': 'Test'})

        doc_call = fm.db.collection.return_value.document.call_args
        self.assertEqual(doc_call[0][0], 'story_ng_001')

    def test_high_number_continues(self):
        """Numéro élevé existant → +1."""
        existing = [{'id': 'story_ke_042', 'countryCode': 'KE'}]
        fm = self._make_mock_firebase(existing)
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'KE', 'title': 'Nouveau'
        })
        self.assertEqual(story_id, 'story_ke_043')

    def test_ignores_malformed_ids(self):
        """IDs existants malformés (ancien format Firestore) → ignorés."""
        existing = [
            {'id': 'Xk4mP9qR2abc', 'countryCode': 'KE'},  # ancien format
            {'id': 'story_ke_002', 'countryCode': 'KE'},     # format valide
            {'id': 'story_ke_bad', 'countryCode': 'KE'},     # numéro invalide
        ]
        fm = self._make_mock_firebase(existing)
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'KE', 'title': 'Nouveau'
        })
        self.assertEqual(story_id, 'story_ke_003')

    def test_mixed_countries_only_counts_matching(self):
        """Seules les histoires du même pays comptent."""
        existing = [
            {'id': 'story_ke_001', 'countryCode': 'KE'},
            {'id': 'story_ke_002', 'countryCode': 'KE'},
            {'id': 'story_sn_001', 'countryCode': 'SN'},
            {'id': 'story_gh_001', 'countryCode': 'GH'},
            {'id': 'story_gh_002', 'countryCode': 'GH'},
            {'id': 'story_gh_003', 'countryCode': 'GH'},
        ]
        fm = self._make_mock_firebase(existing)
        success, story_id = self._run_save_story(fm, {
            'countryCode': 'GH', 'title': 'Nouvelle histoire Ghana'
        })
        self.assertEqual(story_id, 'story_gh_004')


class TestStoragePathUniqueness(unittest.TestCase):
    """Tests que les chemins de stockage sont uniques (pas d'écrasement)."""

    def test_two_uploads_different_uuids(self):
        """Deux uploads successifs → UUIDs différents, pas d'écrasement."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'countryCode', 'value': 'KE'},
            {'name': 'imageFile', 'filename': 'cover.jpg', 'data': img_data},
        ])

        handler1 = MockHandler(content_type=ct)
        run_upload(handler1, body)
        handler2 = MockHandler(content_type=ct)
        run_upload(handler2, body)

        fn1 = handler1.uploaded_calls[0]['filename']
        fn2 = handler2.uploaded_calls[0]['filename']
        self.assertNotEqual(fn1, fn2, "Deux uploads devraient avoir des filenames différents")

    def test_uuid_portion_is_hex(self):
        """La portion UUID du filename est bien hexadécimale."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'test.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        filename = handler.uploaded_calls[0]['filename']
        # Format: YYYYMMDD_HHMMSS_{8hex}_cover.webp
        uuid_part = filename.split('_')[2]
        self.assertEqual(len(uuid_part), 8)
        int(uuid_part, 16)  # doit être parseable en hex, sinon ValueError

    def test_timestamp_is_current(self):
        """Le timestamp dans le filename est celui du moment de l'upload."""
        img_data = make_test_image(400, 300, 'RGB', 'JPEG')
        body, ct = build_multipart([
            {'name': 'imageFile', 'filename': 'test.jpg', 'data': img_data},
        ])
        handler = MockHandler(content_type=ct)
        run_upload(handler, body)

        filename = handler.uploaded_calls[0]['filename']
        date_part = filename.split('_')[0]  # YYYYMMDD
        today = datetime.now().strftime('%Y%m%d')
        self.assertEqual(date_part, today)


# ─────────────────────────────────────────────────────────
# Exécution
# ─────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("🧪 TESTS COMPLETS DU SYSTÈME D'UPLOAD BACKOFFICE KUMA")
    print("=" * 70)
    print()

    # Exécuter avec verbosité
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Charger toutes les classes de test dans l'ordre logique
    test_classes = [
        TestImageUploadOptimization,
        TestImageColorModes,
        TestImageExifHandling,
        TestAudioUpload,
        TestCountryCodeNaming,
        TestFilenameStructure,
        TestErrorHandling,
        TestResponseFormat,
        TestMultipartParsing,
        TestEdgeCases,
        TestConsoleOutput,
        TestFirebaseStorageIntegration,
        TestStoryDuplicateDetection,
        TestStoryServerValidation,
        TestStoryUpdateDuplicate,
        TestSouvenirNomenclature,
        TestStoryNomenclature,
        TestStoragePathUniqueness,
        TestQuizValidation,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    if result.wasSuccessful():
        print(f"✅ TOUS LES TESTS PASSENT ({result.testsRun} tests)")
    else:
        print(f"❌ ÉCHECS: {len(result.failures)} | ERREURS: {len(result.errors)} / {result.testsRun} tests")
    print("=" * 70)
