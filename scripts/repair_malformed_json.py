#!/usr/bin/env python3
"""
Database repair script to normalize malformed JSON in VoiceProfile fields.

This script:
1. Finds all VoiceProfile records
2. Normalizes their JSON fields using the normalize_json_fields() method
3. Reports on what was fixed

Usage:
    python scripts/repair_malformed_json.py [--dry-run] [--verbose]

Options:
    --dry-run    Show what would be fixed without making changes
    --verbose    Show detailed information about each profile
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from models import db, VoiceProfile
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def repair_profile(profile, dry_run=False, verbose=False):
    """
    Repair a single profile's JSON fields.
    
    Args:
        profile: VoiceProfile instance
        dry_run: If True, don't save changes
        verbose: If True, show detailed output
        
    Returns:
        dict: Summary of repairs made
    """
    if verbose:
        logger.info(f"Checking profile {profile.id} (user_id={profile.user_id})")
    
    repaired = profile.normalize_json_fields()
    
    if repaired:
        logger.info(f"Profile {profile.id}: Found {len(repaired)} field(s) with malformed JSON")
        
        if verbose:
            for field_name, details in repaired.items():
                logger.info(f"  - {field_name}:")
                logger.info(f"      Original: {details['original']}")
                logger.info(f"      Repaired: {details['repaired']}")
        
        if not dry_run:
            db.session.commit()
            logger.info(f"Profile {profile.id}: Repaired and saved")
        else:
            db.session.rollback()
            logger.info(f"Profile {profile.id}: Would repair (dry-run mode)")
    elif verbose:
        logger.info(f"Profile {profile.id}: All JSON fields valid")
    
    return repaired


def main():
    """Main repair script."""
    parser = argparse.ArgumentParser(
        description='Repair malformed JSON in VoiceProfile database fields'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be fixed without making changes'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information about each profile'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("VoiceProfile JSON Field Repair Script")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("Running in DRY-RUN mode (no changes will be saved)")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Get all profiles
        profiles = VoiceProfile.query.all()
        logger.info(f"Found {len(profiles)} profile(s) to check")
        
        if not profiles:
            logger.info("No profiles found in database")
            return 0
        
        # Track statistics
        total_profiles = len(profiles)
        profiles_with_issues = 0
        total_fields_repaired = 0
        
        # Process each profile
        for profile in profiles:
            repaired = repair_profile(profile, dry_run=args.dry_run, verbose=args.verbose)
            if repaired:
                profiles_with_issues += 1
                total_fields_repaired += len(repaired)
        
        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Summary")
        logger.info("=" * 60)
        logger.info(f"Total profiles checked: {total_profiles}")
        logger.info(f"Profiles with malformed JSON: {profiles_with_issues}")
        logger.info(f"Total fields repaired: {total_fields_repaired}")
        
        if args.dry_run and profiles_with_issues > 0:
            logger.info("")
            logger.info("Note: This was a dry-run. No changes were saved.")
            logger.info("Run without --dry-run to apply fixes.")
        elif profiles_with_issues > 0:
            logger.info("")
            logger.info("✓ All malformed JSON has been repaired!")
        else:
            logger.info("")
            logger.info("✓ All JSON fields are valid - no repairs needed!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
