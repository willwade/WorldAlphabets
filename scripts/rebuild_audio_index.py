#!/usr/bin/env python3
"""
Rebuild the audio index by scanning audio files under the per-language directories.
This fixes corrupted audio index files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.lib.data_layout import RepoDataLayout  # noqa: E402

DATA_LAYOUT = RepoDataLayout()


def parse_audio_filename(path: Path) -> Optional[dict[str, str]]:
    """
    Parse audio filename to extract metadata.
    Expected format: {lang-script}_{engine}_{voice_id}.wav
    Example: cy-Latn_microsoft_cy_gb_aledneural.wav
    """
    filename = path.name
    # Remove .wav extension
    name = filename.replace('.wav', '')
    
    # Split by underscores
    parts = name.split('_')
    if len(parts) < 3:
        return None
    
    lang_script = parts[0]
    engine = parts[1]
    voice_id = '_'.join(parts[2:])  # Join remaining parts as voice_id
    
    # Extract base language code (e.g., "cy-Latn" -> "cy")
    base_lang = lang_script.split('-')[0]
    
    rel_path = path if not path.is_absolute() else path.relative_to(Path.cwd())

    return {
        'engine': engine,
        'voice_id': voice_id,
        'path': rel_path.as_posix(),
        'lang_script': lang_script,
        'base_lang': base_lang
    }

def main() -> None:
    wav_files: List[Path] = []
    if DATA_LAYOUT.root.exists():
        for lang_dir in DATA_LAYOUT.root.iterdir():
            audio_dir = lang_dir / "audio"
            if audio_dir.is_dir():
                wav_files.extend(audio_dir.glob("*.wav"))

    # Fallback to legacy flat structure
    legacy_audio_dir = DATA_LAYOUT.legacy_audio_dir()
    if legacy_audio_dir.exists():
        wav_files.extend(legacy_audio_dir.glob("*.wav"))

    if not wav_files:
        print("❌ No audio files found under data/*/audio or data/audio")
        return
    
    print(f"Found {len(wav_files)} audio files")
    
    # Build new index
    new_index: Dict[str, List[Dict[str, str]]] = {}
    
    for wav_file in wav_files:
        metadata = parse_audio_filename(wav_file)
        if not metadata:
            print(f"⚠️ Could not parse filename: {wav_file.name}")
            continue
        
        base_lang = metadata['base_lang']
        
        # Add to index under base language code
        if base_lang not in new_index:
            new_index[base_lang] = []
        
        # Create audio entry
        audio_entry = {
            'engine': metadata['engine'],
            'voice_id': metadata['voice_id'],
            'path': metadata['path']
        }
        
        new_index[base_lang].append(audio_entry)
        print(f"Added: {base_lang} - {metadata['engine']} - {metadata['voice_id']}")
    
    # Remove duplicates within each language
    for lang_code in new_index:
        seen_paths = set()
        unique_files = []
        for audio_file in new_index[lang_code]:
            path = audio_file.get('path', '')
            if path not in seen_paths:
                seen_paths.add(path)
                unique_files.append(audio_file)
        new_index[lang_code] = unique_files
        print(f"✅ {lang_code}: {len(unique_files)} unique audio files")
    
    # Save the rebuilt index
    DATA_LAYOUT.legacy_audio_dir().mkdir(parents=True, exist_ok=True)
    index_path = DATA_LAYOUT.audio_index_path()
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(new_index, f, ensure_ascii=False, indent=2)

    # Write per-language indexes
    for lang_code, entries in new_index.items():
        lang_index = DATA_LAYOUT.audio_dir(lang_code) / "index.json"
        lang_index.parent.mkdir(parents=True, exist_ok=True)
        with lang_index.open('w', encoding='utf-8') as fh:
            json.dump(entries, fh, ensure_ascii=False, indent=2)
    
    print(f"\n🎵 Rebuilt audio index saved to {index_path}")
    print(f"Languages with audio: {sorted(new_index.keys())}")
    
    # Check for Welsh specifically
    if 'cy' in new_index:
        print(f"\n🏴󠁧󠁢󠁷󠁬󠁳󠁿 Welsh (cy) found with {len(new_index['cy'])} audio files:")
        for audio in new_index['cy']:
            print(f"  - {audio['engine']}: {audio['voice_id']}")

if __name__ == "__main__":
    main()
