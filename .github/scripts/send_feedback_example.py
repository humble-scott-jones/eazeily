#!/usr/bin/env python3
"""
Example script to send feedback to GitHub for automated processing.

This demonstrates how to trigger the feedback automation from your application.
"""

import os
import sys
import requests
from datetime import datetime


def send_feedback_to_github(feedback_text, user_email=None, github_token=None):
    """
    Send user feedback to GitHub for automated processing.
    
    Args:
        feedback_text: The raw feedback text from the user
        user_email: Optional email of the user submitting feedback
        github_token: GitHub personal access token with repo scope
    
    Returns:
        True if successful, False otherwise
    """
    if not github_token:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
            return False
    
    url = "https://api.github.com/repos/humble-scott-jones/togetherly/dispatches"
    
    payload = {
        "event_type": "user_feedback",
        "client_payload": {
            "feedback": feedback_text,
            "user_email": user_email or "anonymous",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 204:
            print("Feedback sent successfully!", file=sys.stderr)
            return True
        else:
            print(f"Error: GitHub API returned {response.status_code}", file=sys.stderr)
            print(f"Response: {response.text}", file=sys.stderr)
            return False
    
    except Exception as e:
        print(f"Error sending feedback: {e}", file=sys.stderr)
        return False


def main():
    """CLI interface for testing feedback submission."""
    if len(sys.argv) < 2:
        print("Usage: python send_feedback_example.py <feedback_text> [user_email]")
        print("\nExample:")
        print('  python send_feedback_example.py "Add dark mode support" user@example.com')
        print("\nRequires GITHUB_TOKEN environment variable to be set.")
        sys.exit(1)
    
    feedback = sys.argv[1]
    email = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Sending feedback: {feedback}")
    if email:
        print(f"From: {email}")
    
    success = send_feedback_to_github(feedback, email)
    
    if success:
        print("\n✓ Feedback submitted successfully!")
        print("Check GitHub Actions for processing status:")
        print("  https://github.com/humble-scott-jones/togetherly/actions")
    else:
        print("\n✗ Failed to submit feedback")
        sys.exit(1)


if __name__ == "__main__":
    main()
