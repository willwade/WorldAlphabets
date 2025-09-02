#!/usr/bin/env python3
"""Comprehensive data builder for WorldAlphabets.

This script runs the complete data collection pipeline:
1. Build alphabets from CLDR + fallbacks
2. Create index files
3. Generate audio files (if configured)
4. Update web UI data
5. Run validation tests
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

def run_command(cmd: List[str], description: str, cwd: Optional[Path] = None) -> bool:
    """Run a command and return success status."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print("Output:", result.stdout[:500])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with return code {e.returncode}")
        if e.stderr:
            print("Error:", e.stderr[:500])
        if e.stdout:
            print("Output:", e.stdout[:500])
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-audio", action="store_true", help="Skip audio generation")
    parser.add_argument("--skip-web", action="store_true", help="Skip web UI update")
    parser.add_argument("--skip-tests", action="store_true", help="Skip validation tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    root_dir = Path(__file__).parent.parent
    scripts_dir = root_dir / "scripts"
    web_dir = root_dir / "web"
    
    print("🌍 WorldAlphabets Data Builder")
    print("=" * 50)
    
    success_count = 0
    total_steps = 0
    
    # Step 1: Build alphabets
    total_steps += 1
    if run_command([
        "uv", "run", "python", 
        str(scripts_dir / "build_comprehensive_alphabets.py"),
        "--manifest", str(root_dir / "data" / "language_scripts.json"),
        "--verbose" if args.verbose else ""
    ], "Building alphabets from CLDR + fallbacks", cwd=root_dir):
        success_count += 1
    
    # Step 2: Create index
    total_steps += 1
    if run_command([
        "uv", "run", "python",
        str(scripts_dir / "create_index.py")
    ], "Creating data index", cwd=root_dir):
        success_count += 1
    
    # Step 3: Generate audio (optional)
    if not args.skip_audio:
        total_steps += 1
        if run_command([
            "uv", "run", "python",
            str(scripts_dir / "generate_audio.py")
        ], "Generating audio files", cwd=root_dir):
            success_count += 1
    
    # Step 4: Update web UI data
    if not args.skip_web and web_dir.exists():
        total_steps += 1
        if run_command([
            "npm", "run", "predev"
        ], "Updating web UI data", cwd=web_dir):
            success_count += 1
    
    # Step 5: Run validation tests
    if not args.skip_tests:
        # Python tests
        total_steps += 1
        if run_command([
            "uv", "run", "python", "-m", "pytest", "tests/", "-v"
        ], "Running Python tests", cwd=root_dir):
            success_count += 1
        
        # Node.js tests
        total_steps += 1
        if run_command([
            "npm", "test"
        ], "Running Node.js tests", cwd=root_dir):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 BUILD SUMMARY")
    print("=" * 50)
    print(f"Completed: {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        print("🎉 All steps completed successfully!")
        return 0
    else:
        print(f"⚠️  {total_steps - success_count} steps failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
