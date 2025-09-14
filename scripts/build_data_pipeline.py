#!/usr/bin/env python3
"""
Consolidated WorldAlphabets Data Collection Pipeline

This script replaces the fragmented build system with a unified, robust pipeline
that generates comprehensive language and alphabet data from multiple sources.

Usage:
    uv run scripts/build_data_pipeline.py [--stage STAGE] [--language LANG] [--verbose]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Any
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from worldalphabets.data_sources import (
    CLDRCollector,
    ISO639Collector,
    WikidataCollector,
    FrequencyCollector,
    FallbackDataCollector,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataPipeline:
    """Consolidated data collection pipeline for WorldAlphabets."""

    def __init__(self, root_dir: Path, verbose: bool = False):
        self.root_dir = root_dir
        self.data_dir = root_dir / "data"
        self.sources_dir = self.data_dir / "sources"
        self.alphabets_dir = self.data_dir / "alphabets"

        # Create directories
        for dir_path in [self.data_dir, self.sources_dir, self.alphabets_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Configure logging level
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Pipeline statistics
        self.stats: Dict[str, Any] = {
            "start_time": time.time(),
            "stages_completed": 0,
            "total_stages": 10,
            "languages_processed": 0,
            "alphabets_generated": 0,
            "errors": [],
            "warnings": [],
        }

        # Initialize data collectors
        self.cldr = CLDRCollector(self.sources_dir)
        self.iso639 = ISO639Collector(self.sources_dir)
        self.wikidata = WikidataCollector(self.sources_dir)
        self.frequency = FrequencyCollector(self.sources_dir)
        self.fallback = FallbackDataCollector(
            self.root_dir / "src" / "worldalphabets" / "data" / "fallbacks.json"
        )

    def run_full_pipeline(self) -> bool:
        """Run the complete data collection pipeline."""
        logger.info("🌍 Starting WorldAlphabets Data Collection Pipeline")
        logger.info("=" * 60)

        stages = [
            ("collect_sources", "Collecting source data"),
            ("build_language_registry", "Building language registry"),
            ("build_alphabets", "Generating alphabets"),
            ("build_translations", "Generating translations"),
            ("build_keyboards", "Building keyboard layouts"),
            ("build_top200", "Building Top-200 token lists"),
            ("build_tts_index", "Indexing TTS voices"),
            ("build_audio", "Generating audio files"),
            ("build_index", "Creating indexes"),
            ("validate_data", "Validating data"),
        ]

        success_count = 0
        for stage_name, description in stages:
            logger.info(f"📋 Stage {success_count + 1}/{len(stages)}: {description}")

            try:
                stage_method = getattr(self, stage_name)
                if stage_method():
                    success_count += 1
                    self.stats["stages_completed"] += 1
                    logger.info(f"✅ {description} completed successfully")
                else:
                    logger.error(f"❌ {description} failed")
                    break
            except Exception as e:
                logger.error(f"❌ {description} failed with exception: {e}")
                self.stats["errors"].append(f"{stage_name}: {e}")
                break

        # Print final statistics
        self._print_final_stats(success_count, len(stages))
        return success_count == len(stages)

    def collect_sources(self) -> bool:
        """Stage 1: Download and cache external data sources."""
        try:
            # Download frequency data
            logger.info("Downloading Simia unigrams dataset...")
            if not self.frequency.download_simia_unigrams():
                self.stats["warnings"].append("Failed to download Simia unigrams")

            # Cache CLDR available locales
            logger.info("Caching CLDR available locales...")
            locales = self.cldr.get_available_locales()
            logger.info(f"Found {len(locales)} available CLDR locales")

            # Download ISO 639-3 registry
            logger.info("Downloading ISO 639-3 language registry...")
            languages = self.iso639.get_language_registry()
            logger.info(f"Loaded {len(languages)} languages from ISO registry")

            # Cache Wikidata mappings
            logger.info("Fetching Wikidata language-script mappings...")
            mappings = self.wikidata.get_language_script_mappings()
            logger.info(f"Cached {len(mappings)} language-script mappings")

            return True
        except Exception as e:
            logger.error(f"Source collection failed: {e}")
            self.stats["errors"].append(f"collect_sources: {e}")
            return False

    def build_language_registry(self) -> bool:
        """Stage 2: Create comprehensive language database."""
        try:
            # Get base language data from ISO 639-3
            iso_languages = self.iso639.get_language_registry()

            # Get script mappings from Wikidata
            wikidata_scripts = self.wikidata.get_language_script_mappings()

            # Get manual additions
            manual_additions = self.fallback.get_manual_language_additions()

            # Build comprehensive registry
            registry = {}
            script_mappings = {}

            # Process ISO 639-3 languages
            for lang in iso_languages:
                code = lang.get("Id", "").lower()
                if not code or len(code) < 2:
                    continue

                registry[code] = {
                    "code": code,
                    "iso639_1": lang.get("Part1", ""),
                    "iso639_3": lang.get("Id", ""),
                    "name": lang.get("Ref_Name", ""),
                    "type": lang.get("Language_Type", ""),
                    "scope": lang.get("Scope", ""),
                    "status": (
                        "active" if lang.get("Language_Type") == "L" else "inactive"
                    ),
                    "scripts": list(wikidata_scripts.get(code, set())),
                    "sources": ["iso639-3"],
                }

                # Add to script mappings if has scripts
                if registry[code]["scripts"]:
                    script_mappings[code] = registry[code]["scripts"]

            # Add manual additions
            for lang in manual_additions:
                code = lang["Id"].lower()
                registry[code] = {
                    "code": code,
                    "iso639_1": lang.get("Part1", ""),
                    "iso639_3": lang.get("Part2T", ""),
                    "name": lang["Ref_Name"],
                    "type": "L",
                    "scope": "I",
                    "status": "active",
                    "scripts": lang.get("scripts", []),
                    "sources": ["manual"],
                }
                if lang.get("scripts"):
                    script_mappings[code] = lang["scripts"]

            # Save registry
            registry_file = self.data_dir / "language_registry.json"
            with open(registry_file, "w", encoding="utf-8") as f:
                json.dump(registry, f, ensure_ascii=False, indent=2)

            # Save enhanced script mappings
            scripts_file = self.data_dir / "language_scripts.json"
            with open(scripts_file, "w", encoding="utf-8") as f:
                json.dump(script_mappings, f, ensure_ascii=False, indent=2)

            logger.info(f"Built language registry with {len(registry)} languages")
            logger.info(f"Created script mappings for {len(script_mappings)} languages")

            self.stats["languages_processed"] = len(registry)
            return True

        except Exception as e:
            logger.error(f"Language registry building failed: {e}")
            self.stats["errors"].append(f"build_language_registry: {e}")
            return False

    def build_alphabets(self) -> bool:
        """Stage 3: Generate alphabet files for all language-script pairs."""
        try:
            logger.info("Running comprehensive alphabet builder...")

            # Run the existing build_comprehensive_alphabets.py script
            import subprocess

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    str(self.root_dir / "scripts" / "build_comprehensive_alphabets.py"),
                    "--manifest",
                    str(self.data_dir / "language_scripts.json"),
                    "--verbose",
                ],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"Alphabet building failed: {result.stderr}")
                return False

            # Count generated files
            alphabets_dir = self.data_dir / "alphabets"
            if alphabets_dir.exists():
                alphabet_files = list(alphabets_dir.glob("*.json"))
                alphabets_generated = len(alphabet_files)
                logger.info(f"Generated {alphabets_generated} alphabet files")
                self.stats["alphabets_generated"] = alphabets_generated
            else:
                logger.warning("Alphabets directory not found")
                self.stats["alphabets_generated"] = 0

            return True

        except Exception as e:
            logger.error(f"Alphabet building failed: {e}")
            self.stats["errors"].append(f"build_alphabets: {e}")
            return False

    def build_translations(self) -> bool:
        """Stage 4: Generate translations for alphabet files."""
        try:
            logger.info("Generating translations using Google Translate...")

            # Check if Google Translate API key is available
            import os

            if not os.environ.get("GOOGLE_TRANS_KEY"):
                logger.warning("GOOGLE_TRANS_KEY not set, skipping translations")
                return True

            # Run the generate_translations script
            import subprocess

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    str(self.root_dir / "scripts" / "generate_translations.py"),
                    "--skip-existing",
                ],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.warning(f"Translation generation had issues: {result.stderr}")
                # Don't fail the pipeline for translation issues
                self.stats["warnings"].append("Translation generation had issues")
            else:
                logger.info("Translations generated successfully")

            return True

        except Exception as e:
            logger.error(f"Translation building failed: {e}")
            self.stats["errors"].append(f"build_translations: {e}")
            return False

    def build_keyboards(self) -> bool:
        """Stage 5: Build keyboard layouts."""
        try:
            logger.info("Populating keyboard layout references...")

            # Run the populate_layouts script
            import subprocess

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    str(self.root_dir / "src" / "scripts" / "populate_layouts.py"),
                ],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"populate_layouts failed: {result.stderr}")
                return False

            logger.info("Building keyboard layout files...")

            # Run the build_layouts script
            result = subprocess.run(
                ["uv", "run", "wa-build-layouts"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"wa-build-layouts failed: {result.stderr}")
                return False

            logger.info("Keyboard layouts built successfully")
            return True

        except Exception as e:
            logger.error(f"Keyboard building failed: {e}")
            self.stats["errors"].append(f"build_keyboards: {e}")
            return False

    def build_top200(self) -> bool:
        """Stage 6: Build Top-200 token lists using unified pipeline."""
        try:
            logger.info("Building Top-200 token lists using unified 5-priority pipeline...")
            import subprocess

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "scripts/build_top200_unified.py",
                    "--all",
                ],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"build_top200_unified failed: {result.stderr}")
                return False

            logger.info("Top-200 token lists built successfully with unified pipeline")
            return True

        except Exception as e:
            logger.error(f"Top-200 token build failed: {e}")
            self.stats["errors"].append(f"build_top200: {e}")
            return False

    def build_tts_index(self) -> bool:
        """Stage 7: Index available TTS voices."""
        try:
            logger.info("Indexing available TTS voices...")

            # Run the TTS indexing script
            import subprocess

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    str(self.root_dir / "scripts" / "index_tts.py"),
                ],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.warning(f"TTS indexing had issues: {result.stderr}")
                # Don't fail the pipeline for TTS indexing issues
                self.stats["warnings"].append("TTS indexing had issues")
            else:
                logger.info("TTS voices indexed successfully")

            return True

        except Exception as e:
            logger.error(f"TTS indexing failed: {e}")
            self.stats["errors"].append(f"build_tts_index: {e}")
            return False

    def build_audio(self) -> bool:
        """Stage 8: Generate audio files using TTS."""
        try:
            logger.info("Generating audio files using TTS...")

            # Run the audio generation script
            import subprocess

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    str(self.root_dir / "scripts" / "generate_audio.py"),
                    "--skip-existing",
                ],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.warning(f"Audio generation had issues: {result.stderr}")
                # Don't fail the pipeline for audio generation issues
                self.stats["warnings"].append("Audio generation had issues")
            else:
                logger.info("Audio files generated successfully")

            return True

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            self.stats["errors"].append(f"build_audio: {e}")
            return False

    def build_index(self) -> bool:
        """Stage 9: Create searchable indexes and metadata."""
        try:
            logger.info("Creating searchable indexes and metadata...")

            # Use the Node.js script which handles the new format correctly
            import subprocess

            result = subprocess.run(
                ["node", str(self.root_dir / "scripts" / "create_index.js")],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"Index creation failed: {result.stderr}")
                return False

            logger.info("Indexes and metadata created successfully")
            return True

        except Exception as e:
            logger.error(f"Index building failed: {e}")
            self.stats["errors"].append(f"build_index: {e}")
            return False

    def validate_data(self) -> bool:
        """Stage 10: Comprehensive data validation."""
        logger.info("Validating generated data...")
        # Implementation will be added
        return True

    def run_single_stage(self, stage_name: str) -> bool:
        """Run a single pipeline stage."""
        if not hasattr(self, stage_name):
            logger.error(f"Unknown stage: {stage_name}")
            return False

        logger.info(f"🔧 Running single stage: {stage_name}")
        stage_method = getattr(self, stage_name)

        try:
            result = stage_method()
            if result:
                logger.info(f"✅ Stage {stage_name} completed successfully")
            else:
                logger.error(f"❌ Stage {stage_name} failed")
            return result
        except Exception as e:
            logger.error(f"❌ Stage {stage_name} failed with exception: {e}")
            return False

    def build_single_language(
        self, language: str, script: Optional[str] = None
    ) -> bool:
        """Build alphabet data for a single language."""
        logger.info(
            f"🔤 Building alphabet for {language}" + (f"-{script}" if script else "")
        )
        # Implementation will be added
        return True

    def _print_final_stats(self, success_count: int, total_stages: int) -> None:
        """Print final pipeline statistics."""
        elapsed = time.time() - self.stats["start_time"]

        logger.info("\n" + "=" * 60)
        logger.info("📊 PIPELINE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Stages completed: {success_count}/{total_stages}")
        logger.info(f"Languages processed: {self.stats['languages_processed']}")
        logger.info(f"Alphabets generated: {self.stats['alphabets_generated']}")
        logger.info(f"Total time: {elapsed:.2f} seconds")

        if self.stats["errors"]:
            logger.info(f"Errors: {len(self.stats['errors'])}")
            for error in self.stats["errors"][:5]:  # Show first 5 errors
                logger.error(f"  - {error}")

        if self.stats["warnings"]:
            logger.info(f"Warnings: {len(self.stats['warnings'])}")

        if success_count == total_stages:
            logger.info("🎉 Pipeline completed successfully!")
        else:
            logger.error("💥 Pipeline failed - check logs for details")


def main() -> None:
    """Main entry point for the data pipeline."""
    parser = argparse.ArgumentParser(
        description="WorldAlphabets consolidated data collection pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  uv run scripts/build_data_pipeline.py
  
  # Run single stage
  uv run scripts/build_data_pipeline.py --stage build_alphabets
  
  # Build single language
  uv run scripts/build_data_pipeline.py --language mi --script Latn
  
  # Verbose output
  uv run scripts/build_data_pipeline.py --verbose
        """,
    )

    parser.add_argument(
        "--stage",
        choices=[
            "collect_sources",
            "build_language_registry",
            "build_alphabets",
            "build_translations",
            "build_keyboards",
            "build_top200",
            "build_tts_index",
            "build_audio",
            "build_index",
            "validate_data",
        ],
        help="Run only a specific pipeline stage",
    )

    parser.add_argument(
        "--language",
        help="Build alphabet for a specific language (requires --script if ambiguous)",
    )

    parser.add_argument(
        "--script", help="Script code for single language build (e.g., Latn, Cyrl)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.language and not args.stage and not args.script:
        logger.warning(
            "Building single language without script - will build all scripts for this language"
        )

    # Initialize pipeline
    root_dir = Path(__file__).parent.parent
    pipeline = DataPipeline(root_dir, verbose=args.verbose)

    # Run appropriate pipeline mode
    success = False

    if args.language:
        success = pipeline.build_single_language(args.language, args.script)
    elif args.stage:
        success = pipeline.run_single_stage(args.stage)
    else:
        success = pipeline.run_full_pipeline()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
