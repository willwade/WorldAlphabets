#!/usr/bin/env python3
"""
Rebuild the audio index by scanning actual audio files in the data/audio directory.
This fixes corrupted audio index files.
"""

import json
from pathlib import Path

def parse_audio_filename(filename: str) -> dict:
    """
    Parse audio filename to extract metadata.
    Expected format: {lang-script}_{engine}_{voice_id}.wav
    Example: cy-Latn_microsoft_cy_gb_aledneural.wav
    """
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
    
    return {
        'engine': engine,
        'voice_id': voice_id,
        'path': f'data/audio/{filename}',
        'lang_script': lang_script,
        'base_lang': base_lang
    }

def main():
    audio_dir = Path("data/audio")
    
    if not audio_dir.exists():
        print("❌ Audio directory not found at data/audio")
        return
    
    # Find all .wav files
    wav_files = list(audio_dir.glob("*.wav"))
    print(f"Found {len(wav_files)} audio files")
    
    # Build new index
    new_index = {}
    
    for wav_file in wav_files:
        metadata = parse_audio_filename(wav_file.name)
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
    index_path = Path("data/audio/index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(new_index, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎵 Rebuilt audio index saved to {index_path}")
    print(f"Languages with audio: {sorted(new_index.keys())}")
    
    # Check for Welsh specifically
    if 'cy' in new_index:
        print(f"\n🏴󠁧󠁢󠁷󠁬󠁳󠁿 Welsh (cy) found with {len(new_index['cy'])} audio files:")
        for audio in new_index['cy']:
            print(f"  - {audio['engine']}: {audio['voice_id']}")

if __name__ == "__main__":
    main()
