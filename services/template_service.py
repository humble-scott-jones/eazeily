"""Template Service for Content Templates Library.

Provides pre-built content templates organized by industry to help users
overcome blank-canvas paralysis and quickly generate relevant content.

Templates include:
- Industry-specific content suggestions
- Pre-filled parameters for quick generation
- Example outputs for preview
- Task type mappings (post, email, script, etc.)
"""

from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


# Template data structure
class ContentTemplate:
    """Represents a content template with pre-configured parameters."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        industry: str,
        task_type: str,
        default_params: Dict[str, Any],
        example_output: str
    ):
        self.id = id
        self.name = name
        self.description = description
        self.industry = industry
        self.task_type = task_type
        self.default_params = default_params
        self.example_output = example_output
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'industry': self.industry,
            'task_type': self.task_type,
            'default_params': self.default_params,
            'example_output': self.example_output
        }


# Industry Template Definitions

# Restaurant/Food Templates
RESTAURANT_TEMPLATES = [
    ContentTemplate(
        id='restaurant_daily_special',
        name='Daily Special Announcement',
        description='Promote today\'s special dish or menu item',
        industry='restaurant',
        task_type='post',
        default_params={
            'topic': 'today\'s daily special',
            'platform': 'instagram',
            'mood': 'appetizing and inviting',
            'cta': 'Visit us today'
        },
        example_output='🍝 Today\'s Special Alert! Our chef has prepared a mouthwatering Tuscan Shrimp Pasta with sun-dried tomatoes, fresh basil, and garlic cream sauce. Available while supplies last! Visit us today and treat yourself to something extraordinary. #DailySpecial #FreshEats'
    ),
    ContentTemplate(
        id='restaurant_weekend_brunch',
        name='Weekend Brunch Promo',
        description='Invite customers to weekend brunch service',
        industry='restaurant',
        task_type='post',
        default_params={
            'topic': 'weekend brunch special',
            'platform': 'facebook',
            'mood': 'warm and welcoming',
            'cta': 'Reserve your table'
        },
        example_output='☀️ Weekend Brunch is Calling! Join us Saturday & Sunday 9am-2pm for bottomless mimosas, fluffy pancakes, and our famous eggs benedict. Bring your family, bring your friends, bring your appetite! Reserve your table now - seats fill up fast! 🥞🍳'
    ),
    ContentTemplate(
        id='restaurant_behind_scenes',
        name='Behind the Scenes Kitchen',
        description='Show the kitchen team and food prep process',
        industry='restaurant',
        task_type='script',
        default_params={
            'topic': 'behind the scenes in our kitchen',
            'platform': 'tiktok',
            'video_length': '30s',
            'reel_style': 'fast-paced and energetic'
        },
        example_output='[0-3s] Hook: "Ever wonder what happens before your plate arrives?"\n[4-10s] Quick cuts of chef prepping ingredients\n[11-20s] Cooking action shots with sizzling sounds\n[21-27s] Final plating with garnish\n[28-30s] CTA: "Come taste the magic tonight!"'
    ),
    ContentTemplate(
        id='restaurant_review_highlight',
        name='Customer Review Highlight',
        description='Showcase a positive customer review',
        industry='restaurant',
        task_type='post',
        default_params={
            'topic': 'customer review appreciation',
            'platform': 'instagram',
            'mood': 'grateful and proud'
        },
        example_output='⭐️⭐️⭐️⭐️⭐️ "The best Italian food I\'ve had outside of Italy! The service was impeccable and the atmosphere perfect for date night." - Sarah M.\n\nReviews like this make our day! Thank you for trusting us with your special moments. We can\'t wait to welcome you back! ❤️ #CustomerLove #FiveStars'
    ),
    ContentTemplate(
        id='restaurant_new_menu_item',
        name='New Menu Item Launch',
        description='Announce a new dish or menu addition',
        industry='restaurant',
        task_type='post',
        default_params={
            'topic': 'new menu item launch',
            'platform': 'instagram',
            'mood': 'exciting and appetizing',
            'cta': 'Try it today'
        },
        example_output='🎉 NEW on the Menu! Introducing our Korean BBQ Tacos - crispy tortillas packed with tender marinated beef, kimchi slaw, and spicy gochujang aioli. It\'s the fusion you didn\'t know you needed! Available now for dine-in and takeout. Try it today! 🌮🔥'
    ),
    ContentTemplate(
        id='restaurant_holiday_hours',
        name='Holiday Hours Notice',
        description='Inform customers about holiday schedule',
        industry='restaurant',
        task_type='post',
        default_params={
            'topic': 'holiday hours announcement',
            'platform': 'facebook',
            'mood': 'informative and festive'
        },
        example_output='🎄 Holiday Hours Update 🎄\n\nChristmas Eve: 11am - 8pm\nChristmas Day: CLOSED (spending time with our families!)\nNew Year\'s Eve: 11am - 11pm\nNew Year\'s Day: 12pm - 8pm\n\nThank you for another amazing year. We\'re grateful for each of you! ❤️'
    ),
    ContentTemplate(
        id='restaurant_chef_story',
        name='Chef\'s Table Story',
        description='Share the chef\'s inspiration or journey',
        industry='restaurant',
        task_type='post',
        default_params={
            'topic': 'chef\'s story and inspiration',
            'platform': 'linkedin',
            'mood': 'personal and inspiring'
        },
        example_output='👨‍🍳 From the Chef\'s Table:\n\n"My grandmother taught me that food is love made visible. Every dish I create carries a piece of her wisdom, her recipes, and her generous spirit. When you dine with us, you\'re not just tasting food - you\'re experiencing generations of tradition and passion." - Chef Marco\n\nMeet our culinary team and hear more stories at our Chef\'s Table events every first Friday. #ChefsLife #FoodIsLove'
    )
]

# Fitness/Gym Templates
FITNESS_TEMPLATES = [
    ContentTemplate(
        id='fitness_monday_motivation',
        name='Monday Motivation',
        description='Motivational post to start the week strong',
        industry='fitness',
        task_type='post',
        default_params={
            'topic': 'Monday motivation for fitness goals',
            'platform': 'instagram',
            'mood': 'energizing and motivational',
            'cta': 'Crush your goals today'
        },
        example_output='💪 MONDAY MOTIVATION 💪\n\nNew week = New opportunities to become stronger! Don\'t wait for the perfect moment - make THIS moment count. Your future self will thank you for starting today.\n\nWhat\'s your fitness goal this week? Drop it in the comments! 👇\n\n#MondayMotivation #FitnessGoals #NoExcuses'
    ),
    ContentTemplate(
        id='fitness_workout_tip',
        name='Workout Tip Tuesday',
        description='Share a helpful workout or form tip',
        industry='fitness',
        task_type='post',
        default_params={
            'topic': 'workout technique tip',
            'platform': 'instagram',
            'mood': 'educational and encouraging'
        },
        example_output='💡 TIP TUESDAY 💡\n\nSquat Check: Your knees should track over your toes, not cave inward. This simple cue can prevent injury and maximize gains!\n\n✅ Keep your core engaged\n✅ Push through your heels\n✅ Maintain neutral spine\n\nTag a friend who needs to see this! 🏋️\n\n#WorkoutTips #FormMatters #SquatGoals'
    ),
    ContentTemplate(
        id='fitness_transformation',
        name='Transformation Tuesday',
        description='Feature a member transformation story',
        industry='fitness',
        task_type='post',
        default_params={
            'topic': 'member transformation success story',
            'platform': 'instagram',
            'mood': 'inspirational and proud'
        },
        example_output='🌟 TRANSFORMATION TUESDAY 🌟\n\nMeet Sarah! In just 6 months, she\'s lost 30 pounds, gained incredible strength, and most importantly - found her confidence again.\n\n"I never thought I could do a pull-up. Now I can do 5! This gym changed my life."\n\nYour journey starts with one step. Ready to write your own success story? Link in bio! 💪\n\n#TransformationTuesday #SuccessStory #FitnessJourney'
    ),
    ContentTemplate(
        id='fitness_class_schedule',
        name='Class Schedule Reminder',
        description='Promote this week\'s class schedule',
        industry='fitness',
        task_type='post',
        default_params={
            'topic': 'weekly class schedule',
            'platform': 'facebook',
            'mood': 'informative and inviting'
        },
        example_output='📅 THIS WEEK\'S SCHEDULE 📅\n\nMonday: 6am Spin, 6pm HIIT\nTuesday: 6am Yoga, 7pm Bootcamp\nWednesday: 6am Spin, 6pm Strength\nThursday: 6am Yoga, 7pm Boxing\nFriday: 6am HIIT, 6pm Dance Fitness\nSaturday: 9am Outdoor Bootcamp\n\nAll levels welcome! Reserve your spot in the app. See you there! 🏃‍♀️'
    ),
    ContentTemplate(
        id='fitness_nutrition_tip',
        name='Nutrition Tip',
        description='Share a nutrition or meal prep tip',
        industry='fitness',
        task_type='post',
        default_params={
            'topic': 'nutrition advice',
            'platform': 'instagram',
            'mood': 'helpful and practical'
        },
        example_output='🥗 NUTRITION TIP 🥗\n\nProtein after your workout? Yes! But timing isn\'t as critical as you think. Focus on getting 20-30g of protein within 2 hours post-workout.\n\nQuick options:\n• Greek yogurt with berries\n• Protein shake with banana\n• Chicken and sweet potato\n• Tuna wrap\n\nFuel your recovery! 💪 #NutritionTips #PostWorkout #FitnessFuel'
    ),
    ContentTemplate(
        id='fitness_member_spotlight',
        name='Member Spotlight',
        description='Celebrate a dedicated member',
        industry='fitness',
        task_type='post',
        default_params={
            'topic': 'member spotlight and appreciation',
            'platform': 'instagram',
            'mood': 'celebratory and warm'
        },
        example_output='⭐ MEMBER SPOTLIGHT ⭐\n\nShoutout to Mike, who just hit his 1-year anniversary with us! He hasn\'t missed a Monday in 52 weeks. That\'s dedication!\n\n"The gym became my second home. The community here keeps me accountable and motivated."\n\nThis is what it\'s all about! Thanks for inspiring us, Mike! 🙌\n\n#MemberSpotlight #CommunityFirst #Consistency'
    ),
    ContentTemplate(
        id='fitness_challenge',
        name='Challenge Announcement',
        description='Launch a fitness challenge or competition',
        industry='fitness',
        task_type='post',
        default_params={
            'topic': '30-day fitness challenge',
            'platform': 'facebook',
            'mood': 'exciting and motivating',
            'cta': 'Sign up now'
        },
        example_output='🚀 30-DAY CHALLENGE STARTS MONDAY! 🚀\n\nReady to push your limits? Join our "Spring Into Shape" challenge:\n\n✅ Custom workout plan\n✅ Nutrition guide\n✅ Weekly check-ins\n✅ Prizes for top performers\n✅ Supportive community\n\nEarly bird pricing ends Friday! Sign up now and let\'s do this together! 💪\n\nComment "I\'M IN!" to reserve your spot!\n\n#FitnessChallenge #30DayChallenge'
    )
]

# Retail/E-commerce Templates
RETAIL_TEMPLATES = [
    ContentTemplate(
        id='retail_flash_sale',
        name='Flash Sale Alert',
        description='Announce a limited-time sale or discount',
        industry='retail',
        task_type='post',
        default_params={
            'topic': 'flash sale announcement',
            'platform': 'instagram',
            'mood': 'urgent and exciting',
            'cta': 'Shop now'
        },
        example_output='⚡ FLASH SALE ALERT ⚡\n\n24 HOURS ONLY!\n\n30% OFF EVERYTHING with code FLASH30\n\nYes, you read that right. EVERYTHING. 😱\n\nSale ends tomorrow at midnight. Don\'t miss out!\n\nShop now: [link in bio]\n\n#FlashSale #LimitedTime #ShopSmall'
    ),
    ContentTemplate(
        id='retail_new_arrival',
        name='New Arrival Announcement',
        description='Showcase newly stocked products',
        industry='retail',
        task_type='post',
        default_params={
            'topic': 'new product arrival',
            'platform': 'instagram',
            'mood': 'exciting and trendy',
            'cta': 'Shop the collection'
        },
        example_output='✨ NEW ARRIVALS ✨\n\nFresh styles just dropped! Our Spring Collection is here and it\'s everything you\'ve been waiting for.\n\n🌸 Flowy sundresses\n🌸 Lightweight cardigans\n🌸 Statement accessories\n🌸 Sustainable fabrics\n\nShop the collection before your size sells out! Link in bio 👆\n\n#NewArrivals #SpringFashion #ShopLocal'
    ),
    ContentTemplate(
        id='retail_customer_review',
        name='Customer Review Feature',
        description='Highlight positive customer feedback',
        industry='retail',
        task_type='post',
        default_params={
            'topic': 'customer review showcase',
            'platform': 'instagram',
            'mood': 'grateful and authentic'
        },
        example_output='💬 WHAT OUR CUSTOMERS ARE SAYING 💬\n\n"I ordered the blue dress for my sister\'s wedding and received SO many compliments! The quality is incredible and it fits perfectly. Already planning my next order!" ⭐⭐⭐⭐⭐\n\n- Rachel T.\n\nReviews like this make our hearts full! Thank you for choosing us and sharing your experience! 💙\n\n#CustomerLove #Reviews #ShopWithConfidence'
    ),
    ContentTemplate(
        id='retail_behind_scenes',
        name='Behind the Scenes',
        description='Show the business operations or product creation',
        industry='retail',
        task_type='script',
        default_params={
            'topic': 'behind the scenes packing orders',
            'platform': 'tiktok',
            'video_length': '30s',
            'reel_style': 'fun and authentic'
        },
        example_output='[0-3s] Hook: "Packing your orders is our favorite part! 📦"\n[4-12s] Fast montage of picking products from shelves\n[13-20s] Careful wrapping with tissue paper\n[21-26s] Adding thank you note and stickers\n[27-30s] Sealing box with branded tape + CTA: "Your order could be next! 💕"'
    ),
    ContentTemplate(
        id='retail_seasonal_collection',
        name='Seasonal Collection',
        description='Launch a seasonal product line',
        industry='retail',
        task_type='post',
        default_params={
            'topic': 'seasonal collection launch',
            'platform': 'facebook',
            'mood': 'exciting and timely',
            'cta': 'Browse the collection'
        },
        example_output='🍂 FALL COLLECTION IS HERE 🍂\n\nCozy sweaters, warm tones, and all the autumn vibes you need.\n\nWe\'ve curated the perfect pieces for:\n✅ Pumpkin patch visits\n✅ Coffee shop dates\n✅ Crisp morning walks\n✅ Fireside evenings\n\nEarly access starts now for email subscribers! Everyone else - shop opens Thursday at 9am EST.\n\nBrowse the collection: [link]\n\n#FallFashion #AutumnStyle #NewCollection'
    ),
    ContentTemplate(
        id='retail_restock_alert',
        name='Restock Alert',
        description='Notify customers about restocked popular items',
        industry='retail',
        task_type='post',
        default_params={
            'topic': 'restock announcement',
            'platform': 'instagram',
            'mood': 'urgent and exciting',
            'cta': 'Get yours now'
        },
        example_output='🚨 RESTOCK ALERT 🚨\n\nBy popular demand... they\'re BACK!\n\nOur best-selling boyfriend jeans are back in stock in ALL sizes (for now 😅)\n\nThese sold out in 3 days last time, so if you\'ve been waiting - NOW is your chance!\n\nGet yours now before they\'re gone again! Link in bio 👖\n\n#RestockAlert #BackInStock #ShopNow'
    ),
    ContentTemplate(
        id='retail_thank_you',
        name='Thank You Post',
        description='Express gratitude to customers',
        industry='retail',
        task_type='post',
        default_params={
            'topic': 'customer appreciation',
            'platform': 'instagram',
            'mood': 'heartfelt and genuine'
        },
        example_output='💛 THANK YOU 💛\n\nTo everyone who supported our small business this year - THANK YOU from the bottom of our hearts.\n\nEvery order, every review, every share means the world to us. You make this dream possible.\n\nWe\'re so grateful for this community. Here\'s to more style, more smiles, and more supporting small businesses together! 🙏\n\n#ThankYou #SmallBusiness #Grateful'
    )
]

# Professional Services Templates
PROFESSIONAL_TEMPLATES = [
    ContentTemplate(
        id='professional_industry_insight',
        name='Industry Insight',
        description='Share valuable industry knowledge',
        industry='software',
        task_type='post',
        default_params={
            'topic': 'industry trend or insight',
            'platform': 'linkedin',
            'mood': 'professional and authoritative'
        },
        example_output='📊 INDUSTRY INSIGHT:\n\nThe shift to hybrid work is here to stay. Our recent analysis shows that 67% of companies are now offering flexible work arrangements - up from 32% pre-pandemic.\n\nWhat does this mean for businesses?\n✅ Need for better digital collaboration tools\n✅ Rethinking office space utilization\n✅ Focus on results over presence\n\nHow is your organization adapting? Share your experience in the comments.\n\n#FutureOfWork #BusinessTrends #Leadership'
    ),
    ContentTemplate(
        id='professional_team_spotlight',
        name='Team Member Spotlight',
        description='Highlight a team member and their expertise',
        industry='software',
        task_type='post',
        default_params={
            'topic': 'team member introduction',
            'platform': 'linkedin',
            'mood': 'professional and warm'
        },
        example_output='👋 MEET THE TEAM: Sarah Chen\n\nSarah joined us 3 years ago as a Senior Consultant and has been instrumental in transforming how our clients approach digital strategy.\n\nHer expertise:\n• 12+ years in tech consulting\n• Specializes in AI implementation\n• Speaker at 6 industry conferences\n• Mentor to 15+ junior consultants\n\n"I love helping businesses unlock their potential through technology. Every client teaches me something new."\n\nWant to work with Sarah? Learn more about our services: [link]\n\n#TeamSpotlight #Expertise'
    ),
    ContentTemplate(
        id='professional_case_study',
        name='Case Study Teaser',
        description='Tease a successful client project',
        industry='software',
        task_type='post',
        default_params={
            'topic': 'client success case study preview',
            'platform': 'linkedin',
            'mood': 'professional and compelling'
        },
        example_output='📈 CLIENT SUCCESS STORY\n\nHow we helped a mid-size retailer increase online revenue by 240% in 6 months.\n\nThe Challenge: Outdated e-commerce platform, low conversion rates, struggling to compete with larger brands.\n\nOur Approach:\n• Complete platform overhaul\n• UX optimization\n• Targeted digital marketing\n• Data-driven decision making\n\nThe Results: 240% revenue increase, 3.5x more qualified leads, 89% customer satisfaction score.\n\nRead the full case study: [link]\n\n#CaseStudy #ClientSuccess #DigitalTransformation'
    ),
    ContentTemplate(
        id='professional_tips_tricks',
        name='Tips & Tricks',
        description='Share actionable professional advice',
        industry='software',
        task_type='post',
        default_params={
            'topic': 'professional development tip',
            'platform': 'linkedin',
            'mood': 'helpful and practical'
        },
        example_output='💡 QUICK TIP: Improve Your Client Presentations\n\nStop leading with features. Start with the problem.\n\nInstead of: "Our platform has 50+ integrations..."\n\nTry: "Tired of juggling 5 different tools? Here\'s how we simplified everything for [Client Name]..."\n\nThe formula:\n1. Identify their pain point\n2. Show empathy\n3. Present your solution\n4. Prove it with results\n\nWhat presentation tips work for you? Comment below! 👇\n\n#ProfessionalDevelopment #BusinessTips #ClientRelations'
    ),
    ContentTemplate(
        id='professional_milestone',
        name='Company Milestone',
        description='Celebrate a business achievement',
        industry='software',
        task_type='post',
        default_params={
            'topic': 'company milestone celebration',
            'platform': 'linkedin',
            'mood': 'proud and grateful'
        },
        example_output='🎉 MILESTONE ALERT 🎉\n\nWe just completed our 500th successful project!\n\nFrom our humble beginnings in a garage 8 years ago to serving clients across 30 states, this journey has been incredible.\n\nThank you to:\n✅ Our amazing team who brings their A-game every day\n✅ Our clients who trust us with their business\n✅ Our partners who help us deliver excellence\n\nHere\'s to the next 500! 🚀\n\n#Milestone #Growth #BusinessSuccess'
    ),
    ContentTemplate(
        id='professional_event',
        name='Event Announcement',
        description='Promote an upcoming event or webinar',
        industry='software',
        task_type='post',
        default_params={
            'topic': 'webinar or event promotion',
            'platform': 'linkedin',
            'mood': 'informative and inviting',
            'cta': 'Register now'
        },
        example_output='📅 FREE WEBINAR: Digital Transformation in 2026\n\nJoin us Thursday, Jan 30th at 2pm EST for a deep dive into:\n\n✅ Emerging tech trends\n✅ AI integration strategies\n✅ Common implementation pitfalls\n✅ Real-world success stories\n✅ Q&A with our experts\n\nPerfect for: Business owners, IT leaders, and decision-makers ready to modernize their operations.\n\nLimited spots available. Register now: [link]\n\nCan\'t make it live? Register anyway and we\'ll send you the recording!\n\n#Webinar #DigitalTransformation #BusinessGrowth'
    ),
    ContentTemplate(
        id='professional_thought_leadership',
        name='Thought Leadership',
        description='Share an opinion on industry trends',
        industry='software',
        task_type='post',
        default_params={
            'topic': 'thought leadership perspective',
            'platform': 'linkedin',
            'mood': 'thoughtful and authoritative'
        },
        example_output='🤔 THOUGHT OF THE DAY:\n\nAI won\'t replace professionals. Professionals who use AI will replace those who don\'t.\n\nWe\'re not in a technology revolution - we\'re in an adaptation revolution.\n\nThe question isn\'t "Should we adopt AI?" It\'s "How do we integrate it thoughtfully while maintaining human expertise and judgment?"\n\nAt our firm, we see AI as an enhancement tool, not a replacement. It handles repetitive tasks, freeing our team to focus on strategy, creativity, and client relationships.\n\nThe future belongs to those who blend human insight with technological efficiency.\n\nWhat\'s your take? 💭\n\n#ThoughtLeadership #AI #FutureOfWork'
    )
]

# Default/General Templates
GENERAL_TEMPLATES = [
    ContentTemplate(
        id='general_company_update',
        name='Company Update',
        description='Share news about your business',
        industry='general',
        task_type='post',
        default_params={
            'topic': 'company news or update',
            'platform': 'facebook',
            'mood': 'informative and positive'
        },
        example_output='📢 COMPANY UPDATE\n\nExciting news! We\'re expanding our services to better serve you.\n\nStarting next month, we\'ll be offering:\n✅ Extended hours (now open until 7pm)\n✅ Weekend appointments\n✅ Online booking system\n✅ Same-day service options\n\nOur commitment to quality and customer service remains unchanged - we\'re just making it easier for you to work with us!\n\nQuestions? Drop them below or give us a call. 📞'
    ),
    ContentTemplate(
        id='general_team_spotlight',
        name='Team Spotlight',
        description='Introduce a team member',
        industry='general',
        task_type='post',
        default_params={
            'topic': 'team member introduction',
            'platform': 'instagram',
            'mood': 'friendly and warm'
        },
        example_output='✨ TEAM SPOTLIGHT ✨\n\nMeet Jessica! She\'s been with us for 2 years and is the friendly face you see when you walk in.\n\n"I love being part of a team that genuinely cares about making people\'s day better. Every customer interaction is an opportunity to spread joy!"\n\nOutside of work: Coffee enthusiast ☕, dog mom to two rescue pups 🐕, and amateur baker 🧁\n\nNext time you\'re in, say hi to Jessica! 👋\n\n#TeamSpotlight #MeetTheTeam'
    ),
    ContentTemplate(
        id='general_customer_success',
        name='Customer Success Story',
        description='Share a satisfied customer\'s experience',
        industry='general',
        task_type='post',
        default_params={
            'topic': 'customer testimonial',
            'platform': 'facebook',
            'mood': 'grateful and inspiring'
        },
        example_output='💙 CUSTOMER STORY 💙\n\n"I was skeptical at first, but after working with this team, I\'m a customer for life. They listened to my needs, offered expert advice, and delivered beyond my expectations. Highly recommend!" - Michael R.\n\nStories like Michael\'s remind us why we do what we do. Thank you for trusting us!\n\nHave you worked with us? We\'d love to hear your story too! Share in the comments or leave us a review. 🙏\n\n#CustomerSuccess #Testimonial'
    ),
    ContentTemplate(
        id='general_tips_insights',
        name='Tips & Insights',
        description='Share helpful advice in your area of expertise',
        industry='general',
        task_type='post',
        default_params={
            'topic': 'expert tip or advice',
            'platform': 'instagram',
            'mood': 'helpful and knowledgeable'
        },
        example_output='💡 PRO TIP:\n\n[Your expert advice here]\n\nThis simple change can save you time, money, and hassle. We\'ve helped hundreds of customers with this exact issue.\n\nWant more tips like this? Follow us for weekly insights!\n\nHave a question? Drop it in the comments - we love helping! 👇\n\n#ProTip #ExpertAdvice #HelpfulHints'
    ),
    ContentTemplate(
        id='general_special_promo',
        name='Special Promotion',
        description='Announce a sale or special offer',
        industry='general',
        task_type='post',
        default_params={
            'topic': 'special promotion',
            'platform': 'facebook',
            'mood': 'exciting and clear',
            'cta': 'Book now'
        },
        example_output='🎉 SPECIAL OFFER 🎉\n\nFor a limited time: Get 20% off your first service!\n\nNew customers only. Use code WELCOME20 when booking.\n\nWhy choose us?\n✅ [Your key benefit 1]\n✅ [Your key benefit 2]\n✅ [Your key benefit 3]\n\nOffer expires [date]. Book now and experience the difference!\n\nCall us: [phone] or Book online: [link]\n\n#SpecialOffer #LimitedTime'
    ),
    ContentTemplate(
        id='general_milestone',
        name='Milestone Celebration',
        description='Celebrate a business milestone',
        industry='general',
        task_type='post',
        default_params={
            'topic': 'business milestone',
            'platform': 'instagram',
            'mood': 'celebratory and grateful'
        },
        example_output='🎊 WE DID IT! 🎊\n\n[Your milestone - e.g., "5 years in business", "1000th customer", "Opened our 2nd location"]\n\nWe couldn\'t have done this without YOU. Thank you for your support, trust, and loyalty.\n\nWhat started as [your origin story] has grown into [current state] - and we\'re just getting started!\n\nHere\'s to many more milestones together! 🥂\n\n#Milestone #ThankYou #Celebration'
    ),
    ContentTemplate(
        id='general_behind_scenes',
        name='Behind the Scenes',
        description='Show the work that goes into your service/product',
        industry='general',
        task_type='post',
        default_params={
            'topic': 'behind the scenes look',
            'platform': 'instagram',
            'mood': 'authentic and engaging'
        },
        example_output='🎬 BEHIND THE SCENES 🎬\n\nEver wondered what goes into [your product/service]?\n\nHere\'s a peek at our process:\n\n1️⃣ [Step 1]\n2️⃣ [Step 2]\n3️⃣ [Step 3]\n4️⃣ [Final result]\n\nQuality takes time, and we never cut corners. Every detail matters!\n\nWhat would you like to see next? Comment below! 👇\n\n#BehindTheScenes #HowItsMade #QualityMatters'
    )
]

# Combine all templates
ALL_TEMPLATES = (
    RESTAURANT_TEMPLATES +
    FITNESS_TEMPLATES +
    RETAIL_TEMPLATES +
    PROFESSIONAL_TEMPLATES +
    GENERAL_TEMPLATES
)


def get_all_templates() -> List[ContentTemplate]:
    """Return all available templates."""
    return ALL_TEMPLATES


def get_template_by_id(template_id: str) -> Optional[ContentTemplate]:
    """Get a specific template by ID."""
    for template in ALL_TEMPLATES:
        if template.id == template_id:
            return template
    return None


def get_templates_by_industry(industry: str) -> List[ContentTemplate]:
    """Get all templates for a specific industry.
    
    Args:
        industry: Industry key (e.g., 'restaurant', 'fitness', 'retail')
    
    Returns:
        List of templates matching the industry, plus general templates
    """
    # Always include general templates as fallback
    templates = [t for t in ALL_TEMPLATES if t.industry == industry or t.industry == 'general']
    return templates


def get_templates_by_task_type(task_type: str) -> List[ContentTemplate]:
    """Get all templates for a specific task type.
    
    Args:
        task_type: Task type (e.g., 'post', 'email', 'script')
    
    Returns:
        List of templates matching the task type
    """
    return [t for t in ALL_TEMPLATES if t.task_type == task_type]


def get_recommended_templates(industry: Optional[str] = None, task_type: Optional[str] = None) -> List[ContentTemplate]:
    """Get recommended templates based on user's industry and/or task type.
    
    Args:
        industry: Optional industry filter
        task_type: Optional task type filter
    
    Returns:
        List of recommended templates
    """
    templates = ALL_TEMPLATES
    
    if industry:
        # Get industry-specific templates + general ones
        templates = [t for t in templates if t.industry == industry or t.industry == 'general']
    
    if task_type:
        templates = [t for t in templates if t.task_type == task_type]
    
    return templates


def search_templates(query: str) -> List[ContentTemplate]:
    """Search templates by name or description.
    
    Args:
        query: Search query string
    
    Returns:
        List of templates matching the search
    """
    query_lower = query.lower()
    return [
        t for t in ALL_TEMPLATES
        if query_lower in t.name.lower() or query_lower in t.description.lower()
    ]
