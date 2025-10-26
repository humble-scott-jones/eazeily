#!/usr/bin/env python3
"""
Format user feedback into structured GitHub issue using LLM.

This script takes raw user feedback and uses an LLM to generate a clear,
structured issue title and body suitable for GitHub issue tracking.
"""

import os
import sys
import json
import argparse
from pathlib import Path


def load_prompt_template():
    """Load the LLM prompt template from the repository."""
    template_path = Path(__file__).parent.parent / "config" / "feedback-prompt.txt"
    
    if template_path.exists():
        with open(template_path, 'r') as f:
            return f.read()
    
    # Default prompt template if file doesn't exist
    return """You are a helpful assistant that converts user feedback into well-structured GitHub issues.

Given the following user feedback, create a clear GitHub issue with:
1. A concise, descriptive title (max 80 characters)
2. A structured body with:
   - Problem/Context section
   - Expected behavior or desired outcome
   - Any additional details from the feedback

User Feedback:
{feedback}

User Email: {user_email}

Respond with JSON in this exact format:
{{
  "title": "Brief descriptive title here",
  "body": "## Problem\\n\\nClear description...\\n\\n## Expected Outcome\\n\\nWhat the user wants...\\n\\n## Additional Context\\n\\nAny other relevant details...\\n\\n---\\n*Submitted by: {user_email}*"
}}

Keep the language professional and clear. Focus on actionable information."""


def format_feedback_with_llm(feedback: str, user_email: str, api_key: str) -> dict:
    """
    Use OpenAI API to format feedback into structured issue.
    
    Args:
        feedback: Raw user feedback text
        user_email: Email of user who submitted feedback
        api_key: OpenAI API key
    
    Returns:
        Dictionary with 'title' and 'body' keys
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai package not installed", file=sys.stderr)
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Load and format the prompt template
    prompt_template = load_prompt_template()
    prompt = prompt_template.format(
        feedback=feedback,
        user_email=user_email or "Anonymous"
    )
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that formats user feedback into GitHub issues. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract and parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if content.startswith("```"):
            # Remove markdown code block markers
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
        
        result = json.loads(content)
        
        # Validate required fields
        if 'title' not in result or 'body' not in result:
            raise ValueError("Response missing required fields: title and/or body")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response as JSON: {e}", file=sys.stderr)
        print(f"Response content: {content}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}", file=sys.stderr)
        sys.exit(1)


def fallback_format(feedback: str, user_email: str) -> dict:
    """
    Fallback formatting when LLM is not available or fails.
    
    Args:
        feedback: Raw user feedback text
        user_email: Email of user who submitted feedback
    
    Returns:
        Dictionary with 'title' and 'body' keys
    """
    # Create a simple title from first line or truncated feedback
    lines = feedback.strip().split('\n')
    first_line = lines[0] if lines else feedback
    title = first_line[:80].strip()
    if len(first_line) > 80:
        title += "..."
    
    # Ensure title starts with capital
    if title and not title[0].isupper():
        title = title[0].upper() + title[1:]
    
    # Remove trailing period unless it's part of ellipsis
    if title.endswith('.') and not title.endswith('...'):
        title = title[:-1]
    
    # If title is too short or generic, prefix it
    if len(title) < 10:
        title = f"User Feedback: {title}"
    
    # Format body
    body = f"""## User Feedback

{feedback}

## Additional Context

*Submitted by: {user_email or "Anonymous"}*

---

*Note: This issue was automatically created from user feedback. Manual review recommended.*
"""
    
    return {"title": title, "body": body}


def main():
    parser = argparse.ArgumentParser(description="Format user feedback into GitHub issue")
    parser.add_argument("--feedback", required=True, help="Raw feedback text")
    parser.add_argument("--user-email", help="Email of user who submitted feedback")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Format the feedback
    if api_key:
        print("Using LLM to format feedback...", file=sys.stderr)
        try:
            result = format_feedback_with_llm(args.feedback, args.user_email, api_key)
        except Exception as e:
            print(f"LLM formatting failed, using fallback: {e}", file=sys.stderr)
            result = fallback_format(args.feedback, args.user_email)
    else:
        print("No OpenAI API key found, using fallback formatting", file=sys.stderr)
        result = fallback_format(args.feedback, args.user_email)
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Formatted feedback written to {output_path}", file=sys.stderr)
    print(f"Title: {result['title']}", file=sys.stderr)


if __name__ == "__main__":
    main()
