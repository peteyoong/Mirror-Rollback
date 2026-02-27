"""
Enneagram V4 Full Question Bank
===============================
108 core questions (12 per type) + 24 validation questions = 132 total
Distributed across 5 scenario categories:
- Workplace/Professional
- Relationships/Intimacy  
- Stress/Conflict Response
- Decision-Making
- Social/Group Dynamics
"""

QUESTION_BANK_V4_FULL = [
    # =========================================================================
    # TYPE 1 - THE REFORMER (12 questions)
    # Core motivation: Being good, right, ethical
    # =========================================================================
    
    # T1-01: Workplace
    {
        "id": "T1-01-WORK",
        "text": "When you notice a colleague taking ethical shortcuts at work, you:",
        "primary_type": 1,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Feel compelled to address it or report it"},
            {"value": 4, "text": "Struggle internally but eventually speak up"},
            {"value": 3, "text": "Document it but wait to see if it continues"},
            {"value": 2, "text": "Focus on your own work and standards"},
            {"value": 1, "text": "Let it go—it's not your responsibility"},
        ]
    },
    # T1-02: Workplace
    {
        "id": "T1-02-WORK",
        "text": "When giving feedback on someone's work, you:",
        "primary_type": 1,
        "secondary_influence": 8,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Point out every flaw so they can improve to the right standard"},
            {"value": 4, "text": "Balance criticism with praise but focus on corrections needed"},
            {"value": 3, "text": "Highlight both strengths and areas for improvement equally"},
            {"value": 2, "text": "Focus mainly on positives to encourage them"},
            {"value": 1, "text": "Avoid giving critical feedback to keep things positive"},
        ]
    },
    # T1-03: Relationships
    {
        "id": "T1-03-REL",
        "text": "When your partner does something you consider wrong or unfair, you:",
        "primary_type": 1,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Feel a strong need to correct them and explain why it's wrong"},
            {"value": 4, "text": "Point it out clearly but try to stay calm about it"},
            {"value": 3, "text": "Mention it once and let them decide what to do"},
            {"value": 2, "text": "Keep your opinion to yourself unless asked"},
            {"value": 1, "text": "Accept different standards—not everyone thinks like you"},
        ]
    },
    # T1-04: Stress/Conflict
    {
        "id": "T1-04-STRESS",
        "text": "When you make a mistake on an important task, you:",
        "primary_type": 1,
        "secondary_influence": 4,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Feel intense self-criticism and replay what went wrong"},
            {"value": 4, "text": "Immediately work to fix it and prevent future errors"},
            {"value": 3, "text": "Acknowledge it and move on after correcting it"},
            {"value": 2, "text": "Feel briefly disappointed but let it go"},
            {"value": 1, "text": "Shrug it off—mistakes happen to everyone"},
        ]
    },
    # T1-05: Decision-Making
    {
        "id": "T1-05-DECIDE",
        "text": "When faced with a gray-area ethical decision, you:",
        "primary_type": 1,
        "secondary_influence": 5,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Research the 'right' answer thoroughly before acting"},
            {"value": 4, "text": "Apply your personal moral code consistently"},
            {"value": 3, "text": "Consider multiple perspectives and choose pragmatically"},
            {"value": 2, "text": "Go with what feels right in the moment"},
            {"value": 1, "text": "Do what's convenient—ethics are relative anyway"},
        ]
    },
    # T1-06: Social
    {
        "id": "T1-06-SOCIAL",
        "text": "When organizing a shared living space, you tend to:",
        "primary_type": 1,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Create systems and expect everyone to follow them"},
            {"value": 4, "text": "Keep your own areas perfect, frustrated by others' mess"},
            {"value": 3, "text": "Suggest guidelines but stay flexible"},
            {"value": 2, "text": "Adapt to whatever system emerges naturally"},
            {"value": 1, "text": "Don't worry much about organization"},
        ]
    },
    # T1-07: Stress/Conflict
    {
        "id": "T1-07-STRESS",
        "text": "When someone criticizes your work as 'good enough,' you:",
        "primary_type": 1,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Feel frustrated—'good enough' isn't the goal"},
            {"value": 4, "text": "Want to explain why excellence matters"},
            {"value": 3, "text": "Accept the feedback but plan improvements"},
            {"value": 2, "text": "Feel relieved that it passed"},
            {"value": 1, "text": "Don't care—'good enough' is fine"},
        ]
    },
    # T1-08: Relationships
    {
        "id": "T1-08-REL",
        "text": "Your inner voice most often sounds like:",
        "primary_type": 1,
        "secondary_influence": 4,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "A critic pointing out what could be better"},
            {"value": 4, "text": "A teacher guiding you toward improvement"},
            {"value": 3, "text": "A balanced advisor weighing pros and cons"},
            {"value": 2, "text": "A supportive friend offering encouragement"},
            {"value": 1, "text": "Mostly quiet—I don't overthink things"},
        ]
    },
    # T1-09: Decision-Making
    {
        "id": "T1-09-DECIDE",
        "text": "When planning a project, you focus first on:",
        "primary_type": 1,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Getting every detail right from the start"},
            {"value": 4, "text": "Establishing clear standards and procedures"},
            {"value": 3, "text": "Balancing quality with practical timelines"},
            {"value": 2, "text": "Getting started and refining as you go"},
            {"value": 1, "text": "The minimum viable outcome"},
        ]
    },
    # T1-10: Workplace
    {
        "id": "T1-10-WORK",
        "text": "When a team decision goes against your principles, you:",
        "primary_type": 1,
        "secondary_influence": 8,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Voice strong dissent and advocate for the right approach"},
            {"value": 4, "text": "Express concerns but ultimately comply"},
            {"value": 3, "text": "Document your objection and move forward"},
            {"value": 2, "text": "Accept the group decision without comment"},
            {"value": 1, "text": "Go along—it's not worth the conflict"},
        ]
    },
    # T1-11: Social
    {
        "id": "T1-11-SOCIAL",
        "text": "At social gatherings, you often find yourself:",
        "primary_type": 1,
        "secondary_influence": 5,
        "triad": "body",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Mentally critiquing how things could be run better"},
            {"value": 4, "text": "Helping ensure everything is organized properly"},
            {"value": 3, "text": "Participating while noting areas for improvement"},
            {"value": 2, "text": "Relaxing and enjoying without judgment"},
            {"value": 1, "text": "Not caring about the logistics at all"},
        ]
    },
    # T1-12: Stress/Conflict
    {
        "id": "T1-12-STRESS",
        "text": "When feeling overwhelmed, you tend to:",
        "primary_type": 1,
        "secondary_influence": 7,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Become more rigid and demanding of yourself"},
            {"value": 4, "text": "Make detailed lists and impose more structure"},
            {"value": 3, "text": "Prioritize tasks and work through them systematically"},
            {"value": 2, "text": "Lower your standards temporarily to cope"},
            {"value": 1, "text": "Let things slide—perfection isn't worth the stress"},
        ]
    },

    # =========================================================================
    # TYPE 2 - THE HELPER (12 questions)
    # Core motivation: Being loved, needed, appreciated
    # =========================================================================
    
    # T2-01: Relationships
    {
        "id": "T2-01-REL",
        "text": "When a friend is going through a difficult time, you typically:",
        "primary_type": 2,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Drop everything to be there and help in any way possible"},
            {"value": 4, "text": "Reach out frequently and offer specific support"},
            {"value": 3, "text": "Check in regularly and offer help when asked"},
            {"value": 2, "text": "Send supportive messages but give them space"},
            {"value": 1, "text": "Wait for them to reach out if they need something"},
        ]
    },
    # T2-02: Relationships
    {
        "id": "T2-02-REL",
        "text": "When you've done a lot for someone and they don't acknowledge it, you:",
        "primary_type": 2,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Feel hurt and resentful, questioning if they value you"},
            {"value": 4, "text": "Drop hints about what you've done hoping they notice"},
            {"value": 3, "text": "Feel disappointed but tell yourself it doesn't matter"},
            {"value": 2, "text": "Directly ask for appreciation or acknowledgment"},
            {"value": 1, "text": "Genuinely don't need recognition—helping is enough"},
        ]
    },
    # T2-03: Social
    {
        "id": "T2-03-SOCIAL",
        "text": "When meeting new people, you often find yourself:",
        "primary_type": 2,
        "secondary_influence": 3,
        "triad": "heart",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Quickly identifying what they need and how you can help"},
            {"value": 4, "text": "Being warm and making them feel welcomed and comfortable"},
            {"value": 3, "text": "Finding common interests to connect over"},
            {"value": 2, "text": "Sharing about yourself while showing interest in them"},
            {"value": 1, "text": "Staying reserved until you know them better"},
        ]
    },
    # T2-04: Stress/Conflict
    {
        "id": "T2-04-STRESS",
        "text": "When you're overwhelmed with your own problems, you:",
        "primary_type": 2,
        "secondary_influence": 4,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Focus on helping others—it distracts from your own issues"},
            {"value": 4, "text": "Struggle to ask for help even when you need it"},
            {"value": 3, "text": "Reach out to trusted friends for support"},
            {"value": 2, "text": "Take time alone to process and recover"},
            {"value": 1, "text": "Easily ask for and accept help from others"},
        ]
    },
    # T2-05: Workplace
    {
        "id": "T2-05-WORK",
        "text": "In workplace relationships, you tend to:",
        "primary_type": 2,
        "secondary_influence": 3,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Become the go-to person for emotional support and favors"},
            {"value": 4, "text": "Build close relationships by anticipating others' needs"},
            {"value": 3, "text": "Maintain friendly, helpful relationships with colleagues"},
            {"value": 2, "text": "Keep work relationships professional but cordial"},
            {"value": 1, "text": "Focus on tasks rather than workplace relationships"},
        ]
    },
    # T2-06: Decision-Making
    {
        "id": "T2-06-DECIDE",
        "text": "When making decisions that affect others, you:",
        "primary_type": 2,
        "secondary_influence": 6,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Prioritize what will make others happy, even at your expense"},
            {"value": 4, "text": "Consider everyone's needs and try to please most people"},
            {"value": 3, "text": "Balance others' needs with your own preferences"},
            {"value": 2, "text": "Make decisions based on what's best overall"},
            {"value": 1, "text": "Focus mainly on what you want—others can adapt"},
        ]
    },
    # T2-07: Stress/Conflict
    {
        "id": "T2-07-STRESS",
        "text": "When someone you've helped doesn't return the favor, you:",
        "primary_type": 2,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Feel betrayed and may become passive-aggressive"},
            {"value": 4, "text": "Keep mental track and feel resentful"},
            {"value": 3, "text": "Note it but try not to keep score"},
            {"value": 2, "text": "Expect nothing in return from the start"},
            {"value": 1, "text": "Don't help expecting reciprocation"},
        ]
    },
    # T2-08: Social
    {
        "id": "T2-08-SOCIAL",
        "text": "At a party, you're most likely to:",
        "primary_type": 2,
        "secondary_influence": 7,
        "triad": "heart",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Help the host and make sure everyone is comfortable"},
            {"value": 4, "text": "Circulate and connect with people who seem alone"},
            {"value": 3, "text": "Mix socializing with occasional helping"},
            {"value": 2, "text": "Focus on enjoying yourself and your friends"},
            {"value": 1, "text": "Stay in one spot and let others come to you"},
        ]
    },
    # T2-09: Workplace
    {
        "id": "T2-09-WORK",
        "text": "When a coworker is struggling with their workload, you:",
        "primary_type": 2,
        "secondary_influence": 1,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Volunteer to take on their tasks, even if overloaded yourself"},
            {"value": 4, "text": "Offer help and check on them repeatedly"},
            {"value": 3, "text": "Offer to help if you have time"},
            {"value": 2, "text": "Empathize but focus on your own responsibilities"},
            {"value": 1, "text": "Assume they'll figure it out themselves"},
        ]
    },
    # T2-10: Relationships
    {
        "id": "T2-10-REL",
        "text": "In romantic relationships, you tend to:",
        "primary_type": 2,
        "secondary_influence": 4,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Anticipate your partner's needs before they ask"},
            {"value": 4, "text": "Show love through acts of service and care"},
            {"value": 3, "text": "Balance giving with receiving"},
            {"value": 2, "text": "Expect mutual effort from both sides"},
            {"value": 1, "text": "Let your partner take the lead in caregiving"},
        ]
    },
    # T2-11: Decision-Making
    {
        "id": "T2-11-DECIDE",
        "text": "When choosing between your needs and someone else's, you:",
        "primary_type": 2,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Almost always put their needs first—it's just who you are"},
            {"value": 4, "text": "Usually sacrifice your needs to avoid disappointing them"},
            {"value": 3, "text": "Try to find compromises that work for both"},
            {"value": 2, "text": "Consider both but prioritize your own when important"},
            {"value": 1, "text": "Put yourself first—you can't pour from an empty cup"},
        ]
    },
    # T2-12: Stress/Conflict
    {
        "id": "T2-12-STRESS",
        "text": "When feeling unappreciated, you cope by:",
        "primary_type": 2,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Reminding people of everything you've done for them"},
            {"value": 4, "text": "Withdrawing warmth until they notice"},
            {"value": 3, "text": "Expressing your feelings directly"},
            {"value": 2, "text": "Focusing on self-care instead"},
            {"value": 1, "text": "Moving on—validation isn't your motivation"},
        ]
    },

    # =========================================================================
    # TYPE 3 - THE ACHIEVER (12 questions)
    # Core motivation: Being valuable, successful, admired
    # =========================================================================
    
    # T3-01: Workplace
    {
        "id": "T3-01-WORK",
        "text": "When preparing for an important presentation, you focus most on:",
        "primary_type": 3,
        "secondary_influence": 1,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "How you'll come across and the impression you'll make"},
            {"value": 4, "text": "Achieving the best possible outcome and metrics"},
            {"value": 3, "text": "Delivering accurate, well-organized content"},
            {"value": 2, "text": "Connecting authentically with your audience"},
            {"value": 1, "text": "Just getting through it—presentations aren't your thing"},
        ]
    },
    # T3-02: Stress/Conflict
    {
        "id": "T3-02-STRESS",
        "text": "When you fail at something publicly, your first instinct is to:",
        "primary_type": 3,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 1.3,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Quickly reframe it as a learning experience to save face"},
            {"value": 4, "text": "Feel deeply embarrassed and work to recover your image"},
            {"value": 3, "text": "Analyze what went wrong to do better next time"},
            {"value": 2, "text": "Accept it openly and move on without dwelling"},
            {"value": 1, "text": "Not care much what others think about the failure"},
        ]
    },
    # T3-03: Workplace
    {
        "id": "T3-03-WORK",
        "text": "When your accomplishments go unrecognized at work, you:",
        "primary_type": 3,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Find subtle ways to make your achievements visible"},
            {"value": 4, "text": "Feel frustrated and consider if you're in the right place"},
            {"value": 3, "text": "Directly ask for feedback and recognition"},
            {"value": 2, "text": "Trust that good work speaks for itself eventually"},
            {"value": 1, "text": "Don't need external validation to feel successful"},
        ]
    },
    # T3-04: Social
    {
        "id": "T3-04-SOCIAL",
        "text": "In social situations, you often find yourself:",
        "primary_type": 3,
        "secondary_influence": 7,
        "triad": "heart",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Adapting your personality to fit what the group values"},
            {"value": 4, "text": "Highlighting your achievements when relevant"},
            {"value": 3, "text": "Being charming and making good impressions"},
            {"value": 2, "text": "Showing up as your authentic self regardless of context"},
            {"value": 1, "text": "Staying quiet and observing rather than performing"},
        ]
    },
    # T3-05: Decision-Making
    {
        "id": "T3-05-DECIDE",
        "text": "When choosing between personal fulfillment and career advancement, you:",
        "primary_type": 3,
        "secondary_influence": 4,
        "triad": "heart",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Choose advancement—success is fulfillment"},
            {"value": 4, "text": "Lean toward advancement but feel conflicted"},
            {"value": 3, "text": "Try to find a path that offers both"},
            {"value": 2, "text": "Lean toward fulfillment—success isn't everything"},
            {"value": 1, "text": "Choose fulfillment without hesitation"},
        ]
    },
    # T3-06: Relationships
    {
        "id": "T3-06-REL",
        "text": "In romantic relationships, you value a partner who:",
        "primary_type": 3,
        "secondary_influence": 2,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Enhances your image and supports your ambitions"},
            {"value": 4, "text": "Is successful in their own right"},
            {"value": 3, "text": "Balances being supportive and independent"},
            {"value": 2, "text": "Accepts you regardless of your achievements"},
            {"value": 1, "text": "Doesn't care about status or success at all"},
        ]
    },
    # T3-07: Stress/Conflict
    {
        "id": "T3-07-STRESS",
        "text": "When experiencing burnout, you:",
        "primary_type": 3,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Push through—stopping would mean falling behind"},
            {"value": 4, "text": "Hide it from others while searching for solutions"},
            {"value": 3, "text": "Acknowledge it but keep working at reduced capacity"},
            {"value": 2, "text": "Take a break openly without worrying about perception"},
            {"value": 1, "text": "Don't experience burnout—you pace yourself well"},
        ]
    },
    # T3-08: Social
    {
        "id": "T3-08-SOCIAL",
        "text": "When introducing yourself to new people, you tend to:",
        "primary_type": 3,
        "secondary_influence": 7,
        "triad": "heart",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Lead with your title, accomplishments, or affiliations"},
            {"value": 4, "text": "Mention impressive things casually in conversation"},
            {"value": 3, "text": "Share relevant background when it comes up naturally"},
            {"value": 2, "text": "Focus on personal interests over professional identity"},
            {"value": 1, "text": "Keep introductions minimal—achievements aren't your identity"},
        ]
    },
    # T3-09: Workplace
    {
        "id": "T3-09-WORK",
        "text": "When assigned to a high-visibility project, your first thought is:",
        "primary_type": 3,
        "secondary_influence": 6,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "How to excel and make yourself look good"},
            {"value": 4, "text": "The opportunity for recognition and advancement"},
            {"value": 3, "text": "How to deliver quality results"},
            {"value": 2, "text": "Whether the work aligns with your interests"},
            {"value": 1, "text": "Hoping someone else will volunteer instead"},
        ]
    },
    # T3-10: Decision-Making
    {
        "id": "T3-10-DECIDE",
        "text": "When setting goals for yourself, you:",
        "primary_type": 3,
        "secondary_influence": 1,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Set ambitious targets that will impress others"},
            {"value": 4, "text": "Create measurable goals tied to visible outcomes"},
            {"value": 3, "text": "Balance challenging goals with realistic expectations"},
            {"value": 2, "text": "Set goals based on personal meaning, not external validation"},
            {"value": 1, "text": "Don't set formal goals—you go with the flow"},
        ]
    },
    # T3-11: Relationships
    {
        "id": "T3-11-REL",
        "text": "When your partner achieves something you haven't, you feel:",
        "primary_type": 3,
        "secondary_influence": 4,
        "triad": "heart",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Competitive—you want to match or exceed them"},
            {"value": 4, "text": "Happy for them but privately motivated to catch up"},
            {"value": 3, "text": "Genuinely happy while reflecting on your own path"},
            {"value": 2, "text": "Purely supportive without comparison"},
            {"value": 1, "text": "Indifferent—their success has nothing to do with you"},
        ]
    },
    # T3-12: Stress/Conflict
    {
        "id": "T3-12-STRESS",
        "text": "When facing criticism of your work, you:",
        "primary_type": 3,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Take it as an attack on your worth and become defensive"},
            {"value": 4, "text": "Feel wounded but try to appear receptive"},
            {"value": 3, "text": "Evaluate the feedback objectively"},
            {"value": 2, "text": "Welcome it as a chance to improve"},
            {"value": 1, "text": "Brush it off—criticism doesn't bother you"},
        ]
    },

    # =========================================================================
    # TYPE 4 - THE INDIVIDUALIST (12 questions)
    # Core motivation: Finding identity, being unique, authentic
    # =========================================================================
    
    # T4-01: Relationships
    {
        "id": "T4-01-REL",
        "text": "When you see others living seemingly perfect lives, you tend to:",
        "primary_type": 4,
        "secondary_influence": 2,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Feel a deep sense of longing for what's missing in your life"},
            {"value": 4, "text": "Wonder what's wrong with you that you can't have that"},
            {"value": 3, "text": "Remind yourself that appearances aren't reality"},
            {"value": 2, "text": "Feel happy for them while content with your own path"},
            {"value": 1, "text": "Not compare yourself—their life has nothing to do with yours"},
        ]
    },
    # T4-02: Stress/Conflict
    {
        "id": "T4-02-STRESS",
        "text": "When experiencing intense emotions, you typically:",
        "primary_type": 4,
        "secondary_influence": 5,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Dive deep into them—intensity feels more authentic than numbness"},
            {"value": 4, "text": "Express them creatively through art, writing, or music"},
            {"value": 3, "text": "Process them internally while maintaining composure"},
            {"value": 2, "text": "Share them with trusted people to work through them"},
            {"value": 1, "text": "Try to regulate them quickly and return to neutral"},
        ]
    },
    # T4-03: Relationships
    {
        "id": "T4-03-REL",
        "text": "When you feel like no one truly understands you, you:",
        "primary_type": 4,
        "secondary_influence": 1,
        "triad": "heart",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Find a melancholic comfort in your unique perspective"},
            {"value": 4, "text": "Withdraw and spend time in introspection"},
            {"value": 3, "text": "Seek out people or communities who might relate"},
            {"value": 2, "text": "Express yourself more clearly to bridge the gap"},
            {"value": 1, "text": "Accept that complete understanding isn't necessary"},
        ]
    },
    # T4-04: Social
    {
        "id": "T4-04-SOCIAL",
        "text": "When choosing how to decorate your personal space, you prioritize:",
        "primary_type": 4,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Creating a unique aesthetic that reflects your inner world"},
            {"value": 4, "text": "Surrounding yourself with meaningful, beautiful objects"},
            {"value": 3, "text": "Balance of style and functionality"},
            {"value": 2, "text": "Comfort and practicality over aesthetics"},
            {"value": 1, "text": "Not caring much—it's just a space"},
        ]
    },
    # T4-05: Workplace
    {
        "id": "T4-05-WORK",
        "text": "In your career, you most value:",
        "primary_type": 4,
        "secondary_influence": 3,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Work that expresses your authentic self and creativity"},
            {"value": 4, "text": "Meaningful contribution that aligns with your values"},
            {"value": 3, "text": "Balance of meaning and practical rewards"},
            {"value": 2, "text": "Stability and good compensation"},
            {"value": 1, "text": "Whatever pays the bills—work is just work"},
        ]
    },
    # T4-06: Decision-Making
    {
        "id": "T4-06-DECIDE",
        "text": "When making important life choices, you rely most on:",
        "primary_type": 4,
        "secondary_influence": 5,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Deep emotional resonance—does this feel authentically 'you'?"},
            {"value": 4, "text": "How the choice aligns with your personal narrative"},
            {"value": 3, "text": "A mix of emotional and practical considerations"},
            {"value": 2, "text": "Logical analysis of pros and cons"},
            {"value": 1, "text": "What's most practical or convenient"},
        ]
    },
    # T4-07: Stress/Conflict
    {
        "id": "T4-07-STRESS",
        "text": "When feeling emotionally low, you tend to:",
        "primary_type": 4,
        "secondary_influence": 2,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Dwell in the feeling—sadness has a certain beauty"},
            {"value": 4, "text": "Use creative outlets to process the emotion"},
            {"value": 3, "text": "Allow yourself to feel it before moving on"},
            {"value": 2, "text": "Seek comfort from others"},
            {"value": 1, "text": "Push through and focus on something else"},
        ]
    },
    # T4-08: Social
    {
        "id": "T4-08-SOCIAL",
        "text": "In group settings, you often feel:",
        "primary_type": 4,
        "secondary_influence": 5,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Like an outsider who doesn't quite fit in"},
            {"value": 4, "text": "Different from others in ways they don't understand"},
            {"value": 3, "text": "Sometimes connected, sometimes apart"},
            {"value": 2, "text": "Generally comfortable and part of the group"},
            {"value": 1, "text": "Completely at ease—groups are energizing"},
        ]
    },
    # T4-09: Relationships
    {
        "id": "T4-09-REL",
        "text": "In romantic relationships, you most want a partner who:",
        "primary_type": 4,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Sees and appreciates your unique, complex inner world"},
            {"value": 4, "text": "Shares deep emotional conversations and intensity"},
            {"value": 3, "text": "Is emotionally available and supportive"},
            {"value": 2, "text": "Is stable and reliable"},
            {"value": 1, "text": "Keeps things light and uncomplicated"},
        ]
    },
    # T4-10: Workplace
    {
        "id": "T4-10-WORK",
        "text": "When receiving the same feedback as others, you:",
        "primary_type": 4,
        "secondary_influence": 3,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Feel it doesn't apply to you—your situation is different"},
            {"value": 4, "text": "Wish for more personalized, nuanced feedback"},
            {"value": 3, "text": "Consider how it applies to your specific context"},
            {"value": 2, "text": "Accept it as generally applicable"},
            {"value": 1, "text": "Prefer standardized feedback—it's more fair"},
        ]
    },
    # T4-11: Decision-Making
    {
        "id": "T4-11-DECIDE",
        "text": "When considering a major purchase, you think about:",
        "primary_type": 4,
        "secondary_influence": 7,
        "triad": "heart",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "How it reflects your unique taste and identity"},
            {"value": 4, "text": "The aesthetic and emotional appeal"},
            {"value": 3, "text": "Balance of beauty and functionality"},
            {"value": 2, "text": "Practical value and cost-effectiveness"},
            {"value": 1, "text": "Just the price—utility over aesthetics"},
        ]
    },
    # T4-12: Stress/Conflict
    {
        "id": "T4-12-STRESS",
        "text": "When someone doesn't appreciate your creative work, you:",
        "primary_type": 4,
        "secondary_influence": 8,
        "triad": "heart",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Feel personally rejected—your work is part of you"},
            {"value": 4, "text": "Question if they truly understand what you're expressing"},
            {"value": 3, "text": "Feel disappointed but value your own assessment"},
            {"value": 2, "text": "Consider their perspective objectively"},
            {"value": 1, "text": "Not take it personally—art is subjective"},
        ]
    },

    # =========================================================================
    # TYPE 5 - THE INVESTIGATOR (12 questions)
    # Core motivation: Being capable, understanding, having resources
    # =========================================================================
    
    # T5-01: Workplace
    {
        "id": "T5-01-WORK",
        "text": "When faced with a complex problem at work, you prefer to:",
        "primary_type": 5,
        "secondary_influence": 6,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Research extensively before taking any action"},
            {"value": 4, "text": "Think through all possibilities independently first"},
            {"value": 3, "text": "Gather some information then discuss with colleagues"},
            {"value": 2, "text": "Jump in and figure it out as you go"},
            {"value": 1, "text": "Delegate it to someone with more expertise"},
        ]
    },
    # T5-02: Social
    {
        "id": "T5-02-SOCIAL",
        "text": "When attending a large social event, you typically:",
        "primary_type": 5,
        "secondary_influence": 4,
        "triad": "head",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Feel drained and need alone time to recharge afterward"},
            {"value": 4, "text": "Find one or two people to have deep conversations with"},
            {"value": 3, "text": "Participate moderately then take breaks"},
            {"value": 2, "text": "Enjoy mingling and meeting new people"},
            {"value": 1, "text": "Thrive on the energy and stay until the end"},
        ]
    },
    # T5-03: Relationships
    {
        "id": "T5-03-REL",
        "text": "When someone asks for your emotional support, you:",
        "primary_type": 5,
        "secondary_influence": 9,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Feel uncomfortable and try to solve the problem instead"},
            {"value": 4, "text": "Listen but struggle to express emotional warmth"},
            {"value": 3, "text": "Offer both practical help and emotional presence"},
            {"value": 2, "text": "Focus on being present and empathetic"},
            {"value": 1, "text": "Easily provide comfort and emotional connection"},
        ]
    },
    # T5-04: Stress/Conflict
    {
        "id": "T5-04-STRESS",
        "text": "When your personal boundaries are pushed, you tend to:",
        "primary_type": 5,
        "secondary_influence": 8,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Withdraw completely and cut off contact"},
            {"value": 4, "text": "Create more distance without explicit confrontation"},
            {"value": 3, "text": "Calmly communicate your boundaries"},
            {"value": 2, "text": "Accommodate somewhat while feeling uncomfortable"},
            {"value": 1, "text": "Assert yourself forcefully and immediately"},
        ]
    },
    # T5-05: Decision-Making
    {
        "id": "T5-05-DECIDE",
        "text": "Before making a major purchase, you:",
        "primary_type": 5,
        "secondary_influence": 6,
        "triad": "head",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Spend days or weeks researching every option"},
            {"value": 4, "text": "Read reviews and compare specifications thoroughly"},
            {"value": 3, "text": "Do reasonable research before deciding"},
            {"value": 2, "text": "Get a quick overview and trust your gut"},
            {"value": 1, "text": "Buy impulsively if it looks good"},
        ]
    },
    # T5-06: Workplace
    {
        "id": "T5-06-WORK",
        "text": "When asked to share your expertise in a meeting, you:",
        "primary_type": 5,
        "secondary_influence": 3,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Feel protective of your knowledge and share selectively"},
            {"value": 4, "text": "Share but worry about being seen as incompetent"},
            {"value": 3, "text": "Contribute confidently on topics you know well"},
            {"value": 2, "text": "Freely share what you know without hesitation"},
            {"value": 1, "text": "Enjoy being the expert and sharing extensively"},
        ]
    },
    # T5-07: Social
    {
        "id": "T5-07-SOCIAL",
        "text": "Your ideal weekend involves:",
        "primary_type": 5,
        "secondary_influence": 4,
        "triad": "head",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Uninterrupted time alone with books, projects, or research"},
            {"value": 4, "text": "Mostly solitary activities with brief social contact"},
            {"value": 3, "text": "Balance of alone time and meaningful social connection"},
            {"value": 2, "text": "Activities with friends and family"},
            {"value": 1, "text": "Packed social calendar with lots of people"},
        ]
    },
    # T5-08: Stress/Conflict
    {
        "id": "T5-08-STRESS",
        "text": "When emotionally overwhelmed, you tend to:",
        "primary_type": 5,
        "secondary_influence": 7,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Retreat into your mind and analyze instead of feel"},
            {"value": 4, "text": "Withdraw from others to process alone"},
            {"value": 3, "text": "Take time to think before addressing feelings"},
            {"value": 2, "text": "Reach out to trusted people for support"},
            {"value": 1, "text": "Express emotions openly and immediately"},
        ]
    },
    # T5-09: Relationships
    {
        "id": "T5-09-REL",
        "text": "In close relationships, you need:",
        "primary_type": 5,
        "secondary_influence": 9,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Significant alone time, even from loved ones"},
            {"value": 4, "text": "Regular periods of solitude to recharge"},
            {"value": 3, "text": "Balance of togetherness and independence"},
            {"value": 2, "text": "Mostly shared time with occasional alone time"},
            {"value": 1, "text": "Constant connection and togetherness"},
        ]
    },
    # T5-10: Decision-Making
    {
        "id": "T5-10-DECIDE",
        "text": "When asked your opinion before you've fully formed one, you:",
        "primary_type": 5,
        "secondary_influence": 6,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Say you need more time to think—you won't speak prematurely"},
            {"value": 4, "text": "Give a tentative answer with many caveats"},
            {"value": 3, "text": "Share initial thoughts while noting they're preliminary"},
            {"value": 2, "text": "Offer a quick take based on current knowledge"},
            {"value": 1, "text": "Speak confidently even without full information"},
        ]
    },
    # T5-11: Workplace
    {
        "id": "T5-11-WORK",
        "text": "When learning something new, you prefer to:",
        "primary_type": 5,
        "secondary_influence": 1,
        "triad": "head",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Master the theory completely before attempting practice"},
            {"value": 4, "text": "Study extensively, then practice carefully"},
            {"value": 3, "text": "Balance theory and hands-on learning"},
            {"value": 2, "text": "Jump into practice and learn as you go"},
            {"value": 1, "text": "Skip theory entirely—learning by doing is best"},
        ]
    },
    # T5-12: Social
    {
        "id": "T5-12-SOCIAL",
        "text": "When people make small talk, you:",
        "primary_type": 5,
        "secondary_influence": 4,
        "triad": "head",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Find it exhausting and try to steer toward substance"},
            {"value": 4, "text": "Participate minimally while waiting for depth"},
            {"value": 3, "text": "Engage politely but prefer meaningful topics"},
            {"value": 2, "text": "Enjoy it as a way to connect with others"},
            {"value": 1, "text": "Love it—light conversation is comfortable and fun"},
        ]
    },

    # =========================================================================
    # TYPE 6 - THE LOYALIST (12 questions)
    # Core motivation: Having security, support, certainty
    # =========================================================================
    
    # T6-01: Workplace
    {
        "id": "T6-01-WORK",
        "text": "When starting a new job or project, your first thoughts are often about:",
        "primary_type": 6,
        "secondary_influence": 1,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "What could go wrong and how to prepare for it"},
            {"value": 4, "text": "Who you can trust and rely on for support"},
            {"value": 3, "text": "Understanding the expectations and guidelines"},
            {"value": 2, "text": "The opportunities and possibilities ahead"},
            {"value": 1, "text": "Excitement about the new adventure"},
        ]
    },
    # T6-02: Stress/Conflict
    {
        "id": "T6-02-STRESS",
        "text": "When an authority figure gives you instructions you disagree with, you:",
        "primary_type": 6,
        "secondary_influence": 8,
        "triad": "head",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Question them internally while outwardly complying"},
            {"value": 4, "text": "Seek clarification to understand their reasoning"},
            {"value": 3, "text": "Respectfully voice your concerns"},
            {"value": 2, "text": "Follow instructions but adapt where you can"},
            {"value": 1, "text": "Push back directly and advocate for your approach"},
        ]
    },
    # T6-03: Decision-Making
    {
        "id": "T6-03-DECIDE",
        "text": "When making a significant life decision, you typically:",
        "primary_type": 6,
        "secondary_influence": 5,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Consult many trusted people and weigh all perspectives"},
            {"value": 4, "text": "Overthink scenarios and struggle to commit"},
            {"value": 3, "text": "Research carefully then make a reasoned choice"},
            {"value": 2, "text": "Trust your gut and decide relatively quickly"},
            {"value": 1, "text": "Make spontaneous decisions based on what feels right"},
        ]
    },
    # T6-04: Stress/Conflict
    {
        "id": "T6-04-STRESS",
        "text": "When things are going smoothly in your life, you often:",
        "primary_type": 6,
        "secondary_influence": 7,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Wait for the other shoe to drop—something will go wrong"},
            {"value": 4, "text": "Stay vigilant and prepare for potential problems"},
            {"value": 3, "text": "Enjoy it while maintaining reasonable caution"},
            {"value": 2, "text": "Fully enjoy the good times without worry"},
            {"value": 1, "text": "Feel confident that things will continue going well"},
        ]
    },
    # T6-05: Relationships
    {
        "id": "T6-05-REL",
        "text": "In close relationships, you tend to:",
        "primary_type": 6,
        "secondary_influence": 2,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Test people's loyalty repeatedly before fully trusting"},
            {"value": 4, "text": "Take time to build trust but become deeply loyal"},
            {"value": 3, "text": "Balance trust with healthy skepticism"},
            {"value": 2, "text": "Trust relatively easily once you connect"},
            {"value": 1, "text": "Trust people immediately until proven otherwise"},
        ]
    },
    # T6-06: Workplace
    {
        "id": "T6-06-WORK",
        "text": "When your company announces major changes, you:",
        "primary_type": 6,
        "secondary_influence": 3,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Immediately worry about worst-case scenarios"},
            {"value": 4, "text": "Seek information and allies to understand the impact"},
            {"value": 3, "text": "Assess how it affects you before reacting"},
            {"value": 2, "text": "Stay open to the possibilities it might bring"},
            {"value": 1, "text": "Get excited about new opportunities"},
        ]
    },
    # T6-07: Social
    {
        "id": "T6-07-SOCIAL",
        "text": "When meeting someone new, you tend to:",
        "primary_type": 6,
        "secondary_influence": 9,
        "triad": "head",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Stay guarded until you can assess their trustworthiness"},
            {"value": 4, "text": "Look for signs of reliability and shared values"},
            {"value": 3, "text": "Be friendly while forming impressions over time"},
            {"value": 2, "text": "Open up fairly quickly if they seem nice"},
            {"value": 1, "text": "Trust and like them immediately"},
        ]
    },
    # T6-08: Decision-Making
    {
        "id": "T6-08-DECIDE",
        "text": "When faced with an important choice and conflicting advice, you:",
        "primary_type": 6,
        "secondary_influence": 5,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Feel paralyzed trying to determine the 'safest' option"},
            {"value": 4, "text": "Keep seeking more opinions hoping for consensus"},
            {"value": 3, "text": "Weigh all input then make your own judgment"},
            {"value": 2, "text": "Trust one source and go with their recommendation"},
            {"value": 1, "text": "Ignore the advice and do what you feel is right"},
        ]
    },
    # T6-09: Stress/Conflict
    {
        "id": "T6-09-STRESS",
        "text": "When you sense hidden agendas in a group, you:",
        "primary_type": 6,
        "secondary_influence": 8,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Become hypervigilant and trust no one"},
            {"value": 4, "text": "Quietly investigate and watch people closely"},
            {"value": 3, "text": "Address it directly with key people"},
            {"value": 2, "text": "Give people the benefit of the doubt"},
            {"value": 1, "text": "Assume positive intent—you rarely sense hidden agendas"},
        ]
    },
    # T6-10: Relationships
    {
        "id": "T6-10-REL",
        "text": "In romantic relationships, your biggest concern is usually:",
        "primary_type": 6,
        "secondary_influence": 4,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Whether your partner is truly committed and reliable"},
            {"value": 4, "text": "Building security and preventing potential problems"},
            {"value": 3, "text": "Maintaining trust and open communication"},
            {"value": 2, "text": "Enjoying the connection and growing together"},
            {"value": 1, "text": "Having fun—commitment will work itself out"},
        ]
    },
    # T6-11: Workplace
    {
        "id": "T6-11-WORK",
        "text": "When assigned a task without clear instructions, you:",
        "primary_type": 6,
        "secondary_influence": 1,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Feel anxious and seek clarification before starting"},
            {"value": 4, "text": "Ask questions to understand expectations precisely"},
            {"value": 3, "text": "Make reasonable assumptions and verify if needed"},
            {"value": 2, "text": "Use your judgment and proceed confidently"},
            {"value": 1, "text": "Enjoy the freedom to do it your own way"},
        ]
    },
    # T6-12: Social
    {
        "id": "T6-12-SOCIAL",
        "text": "Your approach to rules and authority is generally:",
        "primary_type": 6,
        "secondary_influence": 8,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Question them but often follow—safety in compliance"},
            {"value": 4, "text": "Respect legitimate authority while staying skeptical"},
            {"value": 3, "text": "Follow rules that make sense, question others"},
            {"value": 2, "text": "Generally follow your own judgment"},
            {"value": 1, "text": "Rebel against authority—rules are made to be broken"},
        ]
    },

    # =========================================================================
    # TYPE 7 - THE ENTHUSIAST (12 questions)
    # Core motivation: Being satisfied, stimulated, avoiding pain
    # =========================================================================
    
    # T7-01: Stress/Conflict
    {
        "id": "T7-01-STRESS",
        "text": "When you have to deal with a boring but necessary task, you:",
        "primary_type": 7,
        "secondary_influence": 3,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Procrastinate by finding more interesting things to do"},
            {"value": 4, "text": "Rush through it to get back to enjoyable activities"},
            {"value": 3, "text": "Find ways to make it more interesting or gamify it"},
            {"value": 2, "text": "Buckle down and complete it methodically"},
            {"value": 1, "text": "Actually enjoy the structure of routine tasks"},
        ]
    },
    # T7-02: Stress/Conflict
    {
        "id": "T7-02-STRESS",
        "text": "When you're feeling sad or anxious, your instinct is to:",
        "primary_type": 7,
        "secondary_influence": 9,
        "triad": "head",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Find distractions—activities, people, or plans to look forward to"},
            {"value": 4, "text": "Reframe it positively and focus on silver linings"},
            {"value": 3, "text": "Acknowledge the feeling but not dwell on it"},
            {"value": 2, "text": "Sit with the emotion and process it fully"},
            {"value": 1, "text": "Talk about it deeply with someone you trust"},
        ]
    },
    # T7-03: Decision-Making
    {
        "id": "T7-03-DECIDE",
        "text": "When planning a vacation, you prefer:",
        "primary_type": 7,
        "secondary_influence": 2,
        "triad": "head",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "An adventure-packed itinerary with maximum experiences"},
            {"value": 4, "text": "Flexibility to explore spontaneously with loose plans"},
            {"value": 3, "text": "Balance of planned activities and free time"},
            {"value": 2, "text": "A relaxing trip with minimal scheduling"},
            {"value": 1, "text": "Detailed planning to ensure everything goes smoothly"},
        ]
    },
    # T7-04: Relationships
    {
        "id": "T7-04-REL",
        "text": "When someone shares their problems with you, you often:",
        "primary_type": 7,
        "secondary_influence": 6,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Try to cheer them up and offer optimistic perspectives"},
            {"value": 4, "text": "Suggest solutions and exciting alternatives"},
            {"value": 3, "text": "Listen while gently steering toward positive outcomes"},
            {"value": 2, "text": "Focus on understanding and validating their feelings"},
            {"value": 1, "text": "Sit with them in their pain without trying to fix it"},
        ]
    },
    # T7-05: Workplace
    {
        "id": "T7-05-WORK",
        "text": "In your career, you're most energized by:",
        "primary_type": 7,
        "secondary_influence": 3,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Variety, new projects, and brainstorming possibilities"},
            {"value": 4, "text": "Creative freedom and avoiding repetitive work"},
            {"value": 3, "text": "Mix of novel challenges and familiar tasks"},
            {"value": 2, "text": "Mastering a specialty through focused practice"},
            {"value": 1, "text": "Consistent, predictable work with clear routines"},
        ]
    },
    # T7-06: Social
    {
        "id": "T7-06-SOCIAL",
        "text": "At social gatherings, you typically:",
        "primary_type": 7,
        "secondary_influence": 2,
        "triad": "head",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Work the room, bounce between conversations, keep things lively"},
            {"value": 4, "text": "Seek out the most interesting people and topics"},
            {"value": 3, "text": "Enjoy socializing with a good mix of depth and fun"},
            {"value": 2, "text": "Stick with familiar friends mostly"},
            {"value": 1, "text": "Find a quiet corner and have one deep conversation"},
        ]
    },
    # T7-07: Decision-Making
    {
        "id": "T7-07-DECIDE",
        "text": "When faced with commitment (job, relationship, lease), you:",
        "primary_type": 7,
        "secondary_influence": 5,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Feel anxious about closing off other options"},
            {"value": 4, "text": "Delay as long as possible to keep options open"},
            {"value": 3, "text": "Commit after ensuring you have some flexibility"},
            {"value": 2, "text": "Commit once you find the right fit"},
            {"value": 1, "text": "Commit easily—you value stability"},
        ]
    },
    # T7-08: Stress/Conflict
    {
        "id": "T7-08-STRESS",
        "text": "When experiencing emotional pain, you:",
        "primary_type": 7,
        "secondary_influence": 1,
        "triad": "head",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Quickly move to planning something positive to escape it"},
            {"value": 4, "text": "Acknowledge it briefly then redirect your focus"},
            {"value": 3, "text": "Allow yourself to feel it before moving on"},
            {"value": 2, "text": "Process it thoroughly before continuing"},
            {"value": 1, "text": "Stay with difficult feelings as long as needed"},
        ]
    },
    # T7-09: Relationships
    {
        "id": "T7-09-REL",
        "text": "In romantic relationships, you most value:",
        "primary_type": 7,
        "secondary_influence": 8,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Adventure, spontaneity, and shared excitement"},
            {"value": 4, "text": "Freedom to pursue your interests while connected"},
            {"value": 3, "text": "Balance of togetherness and independence"},
            {"value": 2, "text": "Deep emotional connection and stability"},
            {"value": 1, "text": "Predictable routine and domestic comfort"},
        ]
    },
    # T7-10: Workplace
    {
        "id": "T7-10-WORK",
        "text": "When a project drags on longer than expected, you:",
        "primary_type": 7,
        "secondary_influence": 3,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Lose interest and get excited about new opportunities"},
            {"value": 4, "text": "Rush to finish so you can move on"},
            {"value": 3, "text": "Stay engaged while looking for ways to accelerate"},
            {"value": 2, "text": "Maintain focus until it's properly completed"},
            {"value": 1, "text": "Enjoy the sustained engagement with familiar work"},
        ]
    },
    # T7-11: Social
    {
        "id": "T7-11-SOCIAL",
        "text": "Your friends would describe you as:",
        "primary_type": 7,
        "secondary_influence": 2,
        "triad": "head",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "The one who always has ideas and brings the energy"},
            {"value": 4, "text": "Fun, optimistic, and up for anything"},
            {"value": 3, "text": "Enthusiastic but also reliable"},
            {"value": 2, "text": "Steady and thoughtful"},
            {"value": 1, "text": "Calm, grounded, and low-key"},
        ]
    },
    # T7-12: Decision-Making
    {
        "id": "T7-12-DECIDE",
        "text": "When something you planned falls through, you:",
        "primary_type": 7,
        "secondary_influence": 9,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Immediately start planning alternatives—more options!"},
            {"value": 4, "text": "Feel briefly disappointed but quickly pivot"},
            {"value": 3, "text": "Take time to adjust then explore new options"},
            {"value": 2, "text": "Feel quite disappointed before moving on"},
            {"value": 1, "text": "Struggle to let go of the original plan"},
        ]
    },

    # =========================================================================
    # TYPE 8 - THE CHALLENGER (12 questions)
    # Core motivation: Being strong, in control, protecting self/others
    # =========================================================================
    
    # T8-01: Workplace
    {
        "id": "T8-01-WORK",
        "text": "When a group project falls behind schedule, you typically:",
        "primary_type": 8,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Take charge immediately and delegate tasks with clear deadlines"},
            {"value": 4, "text": "Push the team harder and call out anyone slacking"},
            {"value": 3, "text": "Focus on the most critical tasks yourself"},
            {"value": 2, "text": "Try to motivate everyone while staying calm"},
            {"value": 1, "text": "Wait for someone else to step up and lead"},
        ]
    },
    # T8-02: Stress/Conflict
    {
        "id": "T8-02-STRESS",
        "text": "When someone criticizes your work unfairly in a meeting, you:",
        "primary_type": 8,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Directly confront them and demand they explain themselves"},
            {"value": 4, "text": "Stand your ground firmly and defend your work point by point"},
            {"value": 3, "text": "Ask clarifying questions to understand their perspective"},
            {"value": 2, "text": "Let it go in the moment but address it privately later"},
            {"value": 1, "text": "Stay quiet and process your feelings afterward"},
        ]
    },
    # T8-03: Relationships
    {
        "id": "T8-03-REL",
        "text": "When you discover a friend has been dishonest with you, you:",
        "primary_type": 8,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Confront them immediately and demand the truth"},
            {"value": 4, "text": "Test them with questions to see if they'll come clean"},
            {"value": 3, "text": "Distance yourself while deciding what to do"},
            {"value": 2, "text": "Give them a chance to explain before reacting"},
            {"value": 1, "text": "Avoid confrontation and quietly reassess the friendship"},
        ]
    },
    # T8-04: Social
    {
        "id": "T8-04-SOCIAL",
        "text": "When entering a new social situation, you tend to:",
        "primary_type": 8,
        "secondary_influence": 7,
        "triad": "body",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Scan for who has influence and position yourself strategically"},
            {"value": 4, "text": "Make your presence known and introduce yourself confidently"},
            {"value": 3, "text": "Observe the dynamics before engaging"},
            {"value": 2, "text": "Find someone approachable and start a conversation"},
            {"value": 1, "text": "Stay on the periphery until you feel comfortable"},
        ]
    },
    # T8-05: Decision-Making
    {
        "id": "T8-05-DECIDE",
        "text": "When making important decisions, you:",
        "primary_type": 8,
        "secondary_influence": 5,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Trust your gut and decide quickly—action beats hesitation"},
            {"value": 4, "text": "Gather key information then commit decisively"},
            {"value": 3, "text": "Consider input but ultimately trust your own judgment"},
            {"value": 2, "text": "Seek consensus before making major moves"},
            {"value": 1, "text": "Defer to others' expertise and opinions"},
        ]
    },
    # T8-06: Workplace
    {
        "id": "T8-06-WORK",
        "text": "When dealing with an incompetent boss, you:",
        "primary_type": 8,
        "secondary_influence": 1,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Challenge their decisions and work around them"},
            {"value": 4, "text": "Voice your concerns directly regardless of hierarchy"},
            {"value": 3, "text": "Express disagreement professionally when appropriate"},
            {"value": 2, "text": "Focus on your work and avoid confrontation"},
            {"value": 1, "text": "Accept their authority and follow their lead"},
        ]
    },
    # T8-07: Stress/Conflict
    {
        "id": "T8-07-STRESS",
        "text": "When someone tries to control or manipulate you, you:",
        "primary_type": 8,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "React with immediate anger and confrontation"},
            {"value": 4, "text": "Push back forcefully to establish boundaries"},
            {"value": 3, "text": "Calmly but firmly refuse to comply"},
            {"value": 2, "text": "Try to understand their motivation first"},
            {"value": 1, "text": "Go along with it to avoid conflict"},
        ]
    },
    # T8-08: Relationships
    {
        "id": "T8-08-REL",
        "text": "In romantic relationships, you:",
        "primary_type": 8,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Take the lead and protect your partner fiercely"},
            {"value": 4, "text": "Value honesty and directness above all"},
            {"value": 3, "text": "Share power and decision-making equally"},
            {"value": 2, "text": "Let your partner take the lead often"},
            {"value": 1, "text": "Prefer a partner who makes most decisions"},
        ]
    },
    # T8-09: Social
    {
        "id": "T8-09-SOCIAL",
        "text": "When you see someone being treated unfairly, you:",
        "primary_type": 8,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Intervene immediately—you can't stand by and watch injustice"},
            {"value": 4, "text": "Speak up for them or confront the aggressor"},
            {"value": 3, "text": "Assess the situation and help if appropriate"},
            {"value": 2, "text": "Feel concerned but hesitate to get involved"},
            {"value": 1, "text": "Mind your own business—it's not your problem"},
        ]
    },
    # T8-10: Decision-Making
    {
        "id": "T8-10-DECIDE",
        "text": "When negotiating, your approach is:",
        "primary_type": 8,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Assert your position strongly—never show weakness"},
            {"value": 4, "text": "Push for the best deal while respecting the other party"},
            {"value": 3, "text": "Aim for win-win while protecting your interests"},
            {"value": 2, "text": "Prioritize the relationship over winning"},
            {"value": 1, "text": "Avoid negotiation—you accept what's offered"},
        ]
    },
    # T8-11: Workplace
    {
        "id": "T8-11-WORK",
        "text": "Your leadership style is best described as:",
        "primary_type": 8,
        "secondary_influence": 1,
        "triad": "body",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Direct and decisive—you make the tough calls"},
            {"value": 4, "text": "Strong but fair—demanding with clear expectations"},
            {"value": 3, "text": "Collaborative but willing to assert when needed"},
            {"value": 2, "text": "Supportive and empowering others to lead"},
            {"value": 1, "text": "Prefer not to lead—you follow others well"},
        ]
    },
    # T8-12: Stress/Conflict
    {
        "id": "T8-12-STRESS",
        "text": "When you feel vulnerable, you typically:",
        "primary_type": 8,
        "secondary_influence": 5,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Double down on strength—showing vulnerability is weakness"},
            {"value": 4, "text": "Hide it and project confidence"},
            {"value": 3, "text": "Share only with trusted people"},
            {"value": 2, "text": "Open up to close friends and family"},
            {"value": 1, "text": "Express vulnerability openly—it's human"},
        ]
    },

    # =========================================================================
    # TYPE 9 - THE PEACEMAKER (12 questions)
    # Core motivation: Having peace, harmony, avoiding conflict
    # =========================================================================
    
    # T9-01: Stress/Conflict
    {
        "id": "T9-01-STRESS",
        "text": "When two friends are in conflict and both ask for your support, you:",
        "primary_type": 9,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Try to see both perspectives and help them find common ground"},
            {"value": 4, "text": "Avoid taking sides and hope it resolves itself"},
            {"value": 3, "text": "Listen to both but keep your own opinion to yourself"},
            {"value": 2, "text": "Support whoever you think is more right"},
            {"value": 1, "text": "Pick a side clearly and advocate for that friend"},
        ]
    },
    # T9-02: Decision-Making
    {
        "id": "T9-02-DECIDE",
        "text": "When you have a free weekend with no obligations, you typically:",
        "primary_type": 9,
        "secondary_influence": 4,
        "triad": "body",
        "difficulty_weight": 0.8,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Go with the flow and see what happens naturally"},
            {"value": 4, "text": "Enjoy relaxing activities without much structure"},
            {"value": 3, "text": "Make loose plans but stay flexible"},
            {"value": 2, "text": "Plan a few specific activities or goals"},
            {"value": 1, "text": "Create a detailed schedule to maximize the time"},
        ]
    },
    # T9-03: Relationships
    {
        "id": "T9-03-REL",
        "text": "When your partner wants to try a restaurant you're not interested in, you:",
        "primary_type": 9,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Happily agree because their happiness matters more"},
            {"value": 4, "text": "Go along with it to avoid conflict"},
            {"value": 3, "text": "Suggest a compromise or alternative"},
            {"value": 2, "text": "Express your preference but defer to them"},
            {"value": 1, "text": "Firmly state your preference and negotiate"},
        ]
    },
    # T9-04: Stress/Conflict
    {
        "id": "T9-04-STRESS",
        "text": "When you're angry at someone close to you, you typically:",
        "primary_type": 9,
        "secondary_influence": 1,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Suppress it and focus on maintaining harmony"},
            {"value": 4, "text": "Withdraw and become passive or distant"},
            {"value": 3, "text": "Wait until you've calmed down to discuss it"},
            {"value": 2, "text": "Express it indirectly through hints or tone"},
            {"value": 1, "text": "Address it directly and immediately"},
        ]
    },
    # T9-05: Workplace
    {
        "id": "T9-05-WORK",
        "text": "In team meetings, you usually:",
        "primary_type": 9,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Stay quiet unless directly asked, to keep things smooth"},
            {"value": 4, "text": "Support others' ideas rather than pushing your own"},
            {"value": 3, "text": "Contribute when you have something valuable to add"},
            {"value": 2, "text": "Share your perspective proactively"},
            {"value": 1, "text": "Dominate discussions with your ideas"},
        ]
    },
    # T9-06: Social
    {
        "id": "T9-06-SOCIAL",
        "text": "When making group plans with friends, you:",
        "primary_type": 9,
        "secondary_influence": 7,
        "triad": "body",
        "difficulty_weight": 0.9,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "Let others decide—you're happy with whatever"},
            {"value": 4, "text": "Agree with the emerging consensus"},
            {"value": 3, "text": "Offer suggestions but go with the group's choice"},
            {"value": 2, "text": "Advocate for what you actually want"},
            {"value": 1, "text": "Take charge of planning to ensure it happens"},
        ]
    },
    # T9-07: Decision-Making
    {
        "id": "T9-07-DECIDE",
        "text": "When asked directly what you want, you:",
        "primary_type": 9,
        "secondary_influence": 4,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "decision",
        "options": [
            {"value": 5, "text": "Struggle to answer—you're not sure what you want"},
            {"value": 4, "text": "Often say 'I don't know' or 'whatever you want'"},
            {"value": 3, "text": "Take a moment to think before answering"},
            {"value": 2, "text": "Know your preferences and share them"},
            {"value": 1, "text": "State exactly what you want without hesitation"},
        ]
    },
    # T9-08: Relationships
    {
        "id": "T9-08-REL",
        "text": "In close relationships, you tend to:",
        "primary_type": 9,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Merge with your partner's interests and priorities"},
            {"value": 4, "text": "Accommodate their needs, sometimes losing your own"},
            {"value": 3, "text": "Balance your needs with theirs"},
            {"value": 2, "text": "Maintain clear individual identity and interests"},
            {"value": 1, "text": "Prioritize your own needs first"},
        ]
    },
    # T9-09: Workplace
    {
        "id": "T9-09-WORK",
        "text": "When facing a deadline crunch, you:",
        "primary_type": 9,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "workplace",
        "options": [
            {"value": 5, "text": "Procrastinate until the last minute, then power through"},
            {"value": 4, "text": "Work steadily but sometimes get distracted"},
            {"value": 3, "text": "Focus well when the pressure is clear"},
            {"value": 2, "text": "Plan ahead to avoid last-minute stress"},
            {"value": 1, "text": "Thrive under pressure—it energizes you"},
        ]
    },
    # T9-10: Stress/Conflict
    {
        "id": "T9-10-STRESS",
        "text": "When someone asks you to do something you don't want to do, you:",
        "primary_type": 9,
        "secondary_influence": 8,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "category": "stress",
        "options": [
            {"value": 5, "text": "Say yes to avoid conflict, then feel resentful"},
            {"value": 4, "text": "Agree reluctantly or make excuses later"},
            {"value": 3, "text": "Consider it carefully before responding"},
            {"value": 2, "text": "Politely decline while explaining your reasons"},
            {"value": 1, "text": "Say no directly without feeling guilty"},
        ]
    },
    # T9-11: Social
    {
        "id": "T9-11-SOCIAL",
        "text": "Your approach to personal opinions is:",
        "primary_type": 9,
        "secondary_influence": 5,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "category": "social",
        "options": [
            {"value": 5, "text": "You see all sides and rarely take strong positions"},
            {"value": 4, "text": "You have opinions but keep them to yourself"},
            {"value": 3, "text": "You share opinions when relevant and safe"},
            {"value": 2, "text": "You express opinions clearly when you have them"},
            {"value": 1, "text": "You voice strong opinions frequently"},
        ]
    },
    # T9-12: Relationships
    {
        "id": "T9-12-REL",
        "text": "When your needs conflict with someone else's, you:",
        "primary_type": 9,
        "secondary_influence": 2,
        "triad": "body",
        "difficulty_weight": 1.2,
        "reverse_coded": False,
        "category": "relationships",
        "options": [
            {"value": 5, "text": "Prioritize their needs—your peace matters more than getting your way"},
            {"value": 4, "text": "Downplay your needs to maintain the relationship"},
            {"value": 3, "text": "Try to find a compromise that works for both"},
            {"value": 2, "text": "Assert your needs while respecting theirs"},
            {"value": 1, "text": "Put your needs first—self-care isn't selfish"},
        ]
    },

    # =========================================================================
    # VALIDATION PAIRS (24 questions - 12 pairs)
    # Reverse-coded pairs to detect inconsistent/gaming responses
    # =========================================================================
    
    # VALIDATION PAIR 1: Type 8 Confrontation
    {
        "id": "V01-T8-CONF-A",
        "text": "When someone cuts in line in front of you, you:",
        "primary_type": 8,
        "secondary_influence": 1,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V02-T8-CONF-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Call them out directly and assert your place"},
            {"value": 4, "text": "Make your displeasure known through body language"},
            {"value": 3, "text": "Feel annoyed but weigh if it's worth confronting"},
            {"value": 2, "text": "Let it go—not worth the conflict"},
            {"value": 1, "text": "Barely notice or care"},
        ]
    },
    {
        "id": "V02-T8-CONF-B",
        "text": "You prefer to avoid confrontation even when you've been wronged.",
        "primary_type": 8,
        "secondary_influence": 9,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V01-T8-CONF-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—peace is more valuable than being right"},
            {"value": 2, "text": "Somewhat agree—confrontation is uncomfortable"},
            {"value": 3, "text": "Neutral—depends on the situation"},
            {"value": 4, "text": "Somewhat disagree—I'll address it if important"},
            {"value": 5, "text": "Strongly disagree—I always stand up for myself"},
        ]
    },
    
    # VALIDATION PAIR 2: Type 2 Recognition needs
    {
        "id": "V03-T2-RECOG-A",
        "text": "You feel most fulfilled when:",
        "primary_type": 2,
        "secondary_influence": 3,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V04-T2-RECOG-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Others recognize how much you've helped them"},
            {"value": 4, "text": "You're making a tangible difference in someone's life"},
            {"value": 3, "text": "You're connected to people who appreciate you"},
            {"value": 2, "text": "You're achieving your personal goals"},
            {"value": 1, "text": "You have time for solitude and self-care"},
        ]
    },
    {
        "id": "V04-T2-RECOG-B",
        "text": "Your sense of worth comes primarily from your own self-assessment, not others' opinions.",
        "primary_type": 2,
        "secondary_influence": 5,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V03-T2-RECOG-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—I know my worth regardless of feedback"},
            {"value": 2, "text": "Somewhat agree—though appreciation is nice"},
            {"value": 3, "text": "Neutral—both internal and external matter"},
            {"value": 4, "text": "Somewhat disagree—others' views affect me significantly"},
            {"value": 5, "text": "Strongly disagree—I need others to feel valued"},
        ]
    },
    
    # VALIDATION PAIR 3: Type 5 Social energy
    {
        "id": "V05-T5-SOCIAL-A",
        "text": "After a day of meetings and social interaction, you:",
        "primary_type": 5,
        "secondary_influence": 4,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V06-T5-SOCIAL-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Need significant alone time to recover your energy"},
            {"value": 4, "text": "Prefer quiet activities rather than more socializing"},
            {"value": 3, "text": "Feel tired but could still see close friends"},
            {"value": 2, "text": "Feel energized and ready for more connection"},
            {"value": 1, "text": "Want to continue socializing—people energize you"},
        ]
    },
    {
        "id": "V06-T5-SOCIAL-B",
        "text": "Being around people gives you more energy than being alone.",
        "primary_type": 5,
        "secondary_influence": 7,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V05-T5-SOCIAL-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—people are energizing"},
            {"value": 2, "text": "Somewhat agree—with the right people"},
            {"value": 3, "text": "Neutral—depends on the context"},
            {"value": 4, "text": "Somewhat disagree—solitude often feels better"},
            {"value": 5, "text": "Strongly disagree—alone time is essential for me"},
        ]
    },
    
    # VALIDATION PAIR 4: Type 7 Pain avoidance
    {
        "id": "V07-T7-PAIN-A",
        "text": "When facing difficult emotions, your first instinct is:",
        "primary_type": 7,
        "secondary_influence": 3,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "validation_pair": "V08-T7-PAIN-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Find something fun or exciting to distract yourself"},
            {"value": 4, "text": "Look for the positive side of the situation"},
            {"value": 3, "text": "Acknowledge it briefly before moving on"},
            {"value": 2, "text": "Sit with it and process it fully"},
            {"value": 1, "text": "Dive deep into the feeling to understand it"},
        ]
    },
    {
        "id": "V08-T7-PAIN-B",
        "text": "You're comfortable sitting with uncomfortable emotions for extended periods.",
        "primary_type": 7,
        "secondary_influence": 4,
        "triad": "head",
        "difficulty_weight": 1.1,
        "reverse_coded": True,
        "validation_pair": "V07-T7-PAIN-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—emotions need to be fully felt"},
            {"value": 2, "text": "Somewhat agree—I can sit with discomfort when needed"},
            {"value": 3, "text": "Neutral—depends on the emotion"},
            {"value": 4, "text": "Somewhat disagree—I prefer to move on quickly"},
            {"value": 5, "text": "Strongly disagree—I avoid dwelling on negative feelings"},
        ]
    },
    
    # VALIDATION PAIR 5: Type 3 Image consciousness
    {
        "id": "V09-T3-IMAGE-A",
        "text": "How you're perceived by others is:",
        "primary_type": 3,
        "secondary_influence": 2,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V10-T3-IMAGE-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Very important—you actively manage your image"},
            {"value": 4, "text": "Important—you're aware of impressions you make"},
            {"value": 3, "text": "Moderately important—you care but don't obsess"},
            {"value": 2, "text": "Somewhat unimportant—you focus on being yourself"},
            {"value": 1, "text": "Not important at all—you don't care what others think"},
        ]
    },
    {
        "id": "V10-T3-IMAGE-B",
        "text": "You would rather be truly authentic than appear successful.",
        "primary_type": 3,
        "secondary_influence": 4,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V09-T3-IMAGE-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—authenticity is everything"},
            {"value": 2, "text": "Somewhat agree—but success matters too"},
            {"value": 3, "text": "Neutral—both are valuable"},
            {"value": 4, "text": "Somewhat disagree—appearing successful opens doors"},
            {"value": 5, "text": "Strongly disagree—perception creates reality"},
        ]
    },
    
    # VALIDATION PAIR 6: Type 6 Trust/Skepticism
    {
        "id": "V11-T6-TRUST-A",
        "text": "When someone new is overly friendly, you:",
        "primary_type": 6,
        "secondary_influence": 8,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V12-T6-TRUST-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Become suspicious of their motives"},
            {"value": 4, "text": "Stay guarded until you understand why"},
            {"value": 3, "text": "Appreciate it while remaining cautious"},
            {"value": 2, "text": "Accept it at face value"},
            {"value": 1, "text": "Embrace it warmly—friendliness is always welcome"},
        ]
    },
    {
        "id": "V12-T6-TRUST-B",
        "text": "You generally assume people have good intentions until proven otherwise.",
        "primary_type": 6,
        "secondary_influence": 9,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V11-T6-TRUST-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—trust first, question later"},
            {"value": 2, "text": "Somewhat agree—people are mostly good"},
            {"value": 3, "text": "Neutral—it depends on the situation"},
            {"value": 4, "text": "Somewhat disagree—trust must be earned"},
            {"value": 5, "text": "Strongly disagree—vigilance protects you"},
        ]
    },
    
    # VALIDATION PAIR 7: Type 9 Assertiveness
    {
        "id": "V13-T9-ASSERT-A",
        "text": "When you disagree with a group consensus, you:",
        "primary_type": 9,
        "secondary_influence": 6,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "validation_pair": "V14-T9-ASSERT-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Keep quiet to maintain harmony"},
            {"value": 4, "text": "Go along with it despite your reservations"},
            {"value": 3, "text": "Mention your view but don't push it"},
            {"value": 2, "text": "State your disagreement clearly"},
            {"value": 1, "text": "Argue your position strongly"},
        ]
    },
    {
        "id": "V14-T9-ASSERT-B",
        "text": "You have no trouble voicing unpopular opinions in groups.",
        "primary_type": 9,
        "secondary_influence": 8,
        "triad": "body",
        "difficulty_weight": 1.1,
        "reverse_coded": True,
        "validation_pair": "V13-T9-ASSERT-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—I speak my mind regardless"},
            {"value": 2, "text": "Somewhat agree—if it matters enough"},
            {"value": 3, "text": "Neutral—depends on the group"},
            {"value": 4, "text": "Somewhat disagree—I prefer not to create tension"},
            {"value": 5, "text": "Strongly disagree—I keep controversial views to myself"},
        ]
    },
    
    # VALIDATION PAIR 8: Type 1 Perfectionism
    {
        "id": "V15-T1-PERFECT-A",
        "text": "Your standards for your own work are:",
        "primary_type": 1,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V16-T1-PERFECT-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Extremely high—you're your own harshest critic"},
            {"value": 4, "text": "High—you push yourself toward excellence"},
            {"value": 3, "text": "Reasonable—you balance quality and practicality"},
            {"value": 2, "text": "Flexible—you adjust based on what's needed"},
            {"value": 1, "text": "Low—you're satisfied with 'good enough'"},
        ]
    },
    {
        "id": "V16-T1-PERFECT-B",
        "text": "You're comfortable submitting work that's 'good enough' rather than perfect.",
        "primary_type": 1,
        "secondary_influence": 7,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V15-T1-PERFECT-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—perfect is the enemy of done"},
            {"value": 2, "text": "Somewhat agree—sometimes you have to let go"},
            {"value": 3, "text": "Neutral—depends on the stakes"},
            {"value": 4, "text": "Somewhat disagree—quality matters"},
            {"value": 5, "text": "Strongly disagree—you can't rest until it's right"},
        ]
    },
    
    # VALIDATION PAIR 9: Type 4 Uniqueness
    {
        "id": "V17-T4-UNIQUE-A",
        "text": "When you feel like everyone else, you:",
        "primary_type": 4,
        "secondary_influence": 3,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V18-T4-UNIQUE-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Feel uncomfortable—you need to stand out"},
            {"value": 4, "text": "Seek ways to express your individuality"},
            {"value": 3, "text": "Notice it but don't mind much"},
            {"value": 2, "text": "Feel connected and part of something"},
            {"value": 1, "text": "Prefer it—fitting in is comfortable"},
        ]
    },
    {
        "id": "V18-T4-UNIQUE-B",
        "text": "You'd rather fit in seamlessly than stand out as different.",
        "primary_type": 4,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V17-T4-UNIQUE-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—belonging is most important"},
            {"value": 2, "text": "Somewhat agree—standing out can be isolating"},
            {"value": 3, "text": "Neutral—both have their place"},
            {"value": 4, "text": "Somewhat disagree—uniqueness is valuable"},
            {"value": 5, "text": "Strongly disagree—I embrace being different"},
        ]
    },
    
    # VALIDATION PAIR 10: Type 4/1 Emotional depth
    {
        "id": "V19-T4-DEPTH-A",
        "text": "Your emotional life compared to others is:",
        "primary_type": 4,
        "secondary_influence": 5,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": False,
        "validation_pair": "V20-T4-DEPTH-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Deeper and more intense—you feel things others don't"},
            {"value": 4, "text": "Rich and complex—emotions are central to your life"},
            {"value": 3, "text": "About average—you experience normal emotional range"},
            {"value": 2, "text": "More even-keeled than most"},
            {"value": 1, "text": "Relatively flat—you don't experience strong emotions"},
        ]
    },
    {
        "id": "V20-T4-DEPTH-B",
        "text": "You experience emotions about as intensely as most people.",
        "primary_type": 4,
        "secondary_influence": 9,
        "triad": "heart",
        "difficulty_weight": 1.1,
        "reverse_coded": True,
        "validation_pair": "V19-T4-DEPTH-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—I'm emotionally typical"},
            {"value": 2, "text": "Somewhat agree—nothing extraordinary"},
            {"value": 3, "text": "Neutral—hard to compare"},
            {"value": 4, "text": "Somewhat disagree—I feel things more deeply"},
            {"value": 5, "text": "Strongly disagree—my emotional experience is unique"},
        ]
    },
    
    # VALIDATION PAIR 11: Type 8/2 Control
    {
        "id": "V21-T8-CONTROL-A",
        "text": "In group situations, you naturally:",
        "primary_type": 8,
        "secondary_influence": 3,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V22-T8-CONTROL-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Take charge and direct the action"},
            {"value": 4, "text": "Assert influence over decisions"},
            {"value": 3, "text": "Participate actively as an equal"},
            {"value": 2, "text": "Support whoever is leading"},
            {"value": 1, "text": "Prefer to follow and let others lead"},
        ]
    },
    {
        "id": "V22-T8-CONTROL-B",
        "text": "You're comfortable letting others take control of situations.",
        "primary_type": 8,
        "secondary_influence": 9,
        "triad": "body",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V21-T8-CONTROL-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—I prefer others to lead"},
            {"value": 2, "text": "Somewhat agree—leadership is tiring"},
            {"value": 3, "text": "Neutral—depends on the situation"},
            {"value": 4, "text": "Somewhat disagree—I like having influence"},
            {"value": 5, "text": "Strongly disagree—I need to be in control"},
        ]
    },
    
    # VALIDATION PAIR 12: Type 6/7 Security vs Freedom
    {
        "id": "V23-T6-SECURITY-A",
        "text": "When making life choices, you prioritize:",
        "primary_type": 6,
        "secondary_influence": 1,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": False,
        "validation_pair": "V24-T6-SECURITY-B",
        "category": "validation",
        "options": [
            {"value": 5, "text": "Security and stability above all else"},
            {"value": 4, "text": "Safety with some room for growth"},
            {"value": 3, "text": "Balance of security and opportunity"},
            {"value": 2, "text": "Opportunity with acceptable risk"},
            {"value": 1, "text": "Freedom and possibility over security"},
        ]
    },
    {
        "id": "V24-T6-SECURITY-B",
        "text": "You'd rather take risks for exciting opportunities than play it safe.",
        "primary_type": 6,
        "secondary_influence": 7,
        "triad": "head",
        "difficulty_weight": 1.0,
        "reverse_coded": True,
        "validation_pair": "V23-T6-SECURITY-A",
        "category": "validation",
        "options": [
            {"value": 1, "text": "Strongly agree—life's too short to play safe"},
            {"value": 2, "text": "Somewhat agree—calculated risks are worth it"},
            {"value": 3, "text": "Neutral—depends on what's at stake"},
            {"value": 4, "text": "Somewhat disagree—security is underrated"},
            {"value": 5, "text": "Strongly disagree—safety first always"},
        ]
    },
]

print(f"Total questions: {len(QUESTION_BANK_V4_FULL)}")
print(f"Core questions: {sum(1 for q in QUESTION_BANK_V4_FULL if q.get('category') != 'validation')}")
print(f"Validation questions: {sum(1 for q in QUESTION_BANK_V4_FULL if q.get('category') == 'validation')}")

# Count by type
type_counts = {}

# Export the question bank
QUESTION_BANK = QUESTION_BANK_V4_FULL
