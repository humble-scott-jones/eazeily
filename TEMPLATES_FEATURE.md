# Content Templates Library

## Overview
The Content Templates Library provides pre-built content templates organized by industry to help users overcome blank-canvas paralysis and quickly generate relevant content.

## Features

### 1. Template Service (`services/template_service.py`)
- **35 pre-built templates** across 5 industries
- Each template includes:
  - Unique ID
  - Display name
  - Description
  - Industry classification
  - Task type (post, email, script)
  - Default parameters
  - Example output for preview

### 2. API Endpoints (`routes/template_routes.py`)
- `GET /api/templates` - List all templates with optional filters
  - Filter by `industry`: restaurant, fitness, retail, software, general
  - Filter by `task_type`: post, email, script
  - Search by `search` query (name/description)
  
- `GET /api/templates/<id>` - Get specific template by ID

- `GET /api/templates/recommended` - Get templates recommended for user's industry
  - Uses user's profile industry
  - Optional `task_type` filter

### 3. Chat Command (`/templates`)
Users can type `/templates` in the chat interface to:
1. View templates relevant to their industry
2. See numbered list with name, description, and preview
3. Select a template by number (e.g., "3" or "use template 3")
4. Generate content immediately using template's default parameters

## Industry Template Packs

### Restaurant/Food (7 templates)
- Daily Special Announcement
- Weekend Brunch Promo
- Behind the Scenes Kitchen
- Customer Review Highlight
- New Menu Item Launch
- Holiday Hours Notice
- Chef's Table Story

### Fitness/Gym (7 templates)
- Monday Motivation
- Workout Tip Tuesday
- Transformation Tuesday
- Class Schedule Reminder
- Nutrition Tip
- Member Spotlight
- Challenge Announcement

### Retail/E-commerce (7 templates)
- Flash Sale Alert
- New Arrival Announcement
- Customer Review Feature
- Behind the Scenes
- Seasonal Collection
- Restock Alert
- Thank You Post

### Professional Services (7 templates)
- Industry Insight
- Team Member Spotlight
- Case Study Teaser
- Tips & Tricks
- Company Milestone
- Event Announcement
- Thought Leadership

### General/Default (7 templates)
- Company Update
- Team Spotlight
- Customer Success Story
- Tips & Insights
- Special Promotion
- Milestone Celebration
- Behind the Scenes

## Usage Examples

### Via API
```bash
# List all templates
curl https://eazeily.com/api/templates

# Filter by industry
curl https://eazeily.com/api/templates?industry=restaurant

# Get recommended templates
curl https://eazeily.com/api/templates/recommended
```

### Via Chat Interface
```
User: /templates
Bot: Shows list of templates...

User: 3
Bot: Generates content using template #3
```

## Testing
- **49 comprehensive tests** covering:
  - Template service (26 tests)
  - API routes (13 tests)
  - Chat integration (10 tests)
- All tests passing

## Technical Details

### Template Data Structure
```python
{
    'id': 'restaurant_daily_special',
    'name': 'Daily Special Announcement',
    'description': 'Promote today\'s special dish or menu item',
    'industry': 'restaurant',
    'task_type': 'post',
    'default_params': {
        'topic': 'today\'s daily special',
        'platform': 'instagram',
        'mood': 'appetizing and inviting'
    },
    'example_output': '🍝 Today\'s Special Alert! ...'
}
```

### Files Modified
- `app.py` - Register template routes
- `services/conversation_router.py` - Add /templates command
- `routes/chat_routes.py` - Handle template selection flow

### Files Created
- `services/template_service.py` - Core template service
- `routes/template_routes.py` - API endpoints
- `tests/test_template_service.py` - Service tests
- `tests/test_template_routes.py` - Route tests  
- `tests/test_templates_chat_command.py` - Chat integration tests
