"""
Response Post-Processor for Legal AI Assistant

PURPOSE:
Cleans and enforces response structure, removes unwanted phrases,
fixes incorrect escalation suggestions, adds state variation awareness,
and ensures all responses follow the mandated format with proper safety.
"""
import re
from typing import Dict, Any, List, Tuple


# ============================================================================
# FORBIDDEN PHRASES - Replace with safer alternatives
# ============================================================================
FORBIDDEN_PHRASES = [
    # Document references
    (r"[Bb]ased on the provided documents?", "Generally"),
    (r"[Bb]ased on the context provided", "Under Indian law"),
    (r"[Bb]ased on the legal documents?", "Typically"),
    (r"[Tt]he documents? do(?:es)? not contain", "While specific details may vary"),
    (r"[Tt]he provided context", "the available information"),
    (r"[Aa]ccording to the documents?", "Under Indian law"),
    (r"[Ff]rom the retrieved documents?", "Generally"),
    (r"[Aa]ccording to the text", "Generally"),
    (r"[Tt]he text (?:does not |doesn't )", "The specific provision "),
    
    # Information limitations
    (r"[Ii] don'?t have (?:enough )?information", "While specifics may vary"),
    (r"[Ii] cannot find", "The specific provision may vary, but"),
    (r"[Nn]o information (?:is )?available", "While specific details may vary"),
    (r"[Ii] (?:do not|don't) have access", "The specific details may vary"),
    
    # Absolute commands
    (r"[Yy]ou should", "You may consider"),
    (r"[Yy]ou must", "It may be advisable to"),
    (r"[Yy]ou need to", "You might want to"),
    (r"[Yy]ou have to", "It can be helpful to"),
    (r"[Dd]o this", "consider this approach"),
    (r"[Ii]t is mandatory", "It is often required"),
    (r"[Ii]t is illegal", "It may be considered unlawful"),
    (r"[Ii]t is legal", "It is generally permissible"),
    (r"[Tt]his is always", "This is typically"),
    (r"[Tt]his is never", "This is generally not"),
    
    # Absolute certainty
    (r"\balways\b", "typically"),
    (r"\bnever\b", "generally not"),
    (r"\bdefinitely\b", "likely"),
    (r"\bcertainly\b", "generally"),
    
    # DANGEROUS LANGUAGE - "threaten" must never be used
    (r"[Yy]ou can threaten", "You may inform them of your intention to pursue"),
    (r"[Tt]hreaten(?:ing)? legal action", "informing of your intention to pursue legal remedies"),
    (r"[Tt]hreaten(?:ing)? to (?:sue|file)", "communicating your intention to pursue"),
    (r"\bthreaten\b", "inform"),
    (r"\bthreatening\b", "communicating"),
]

# ============================================================================
# DANGEROUS ESCALATION - Police for civil matters
# ============================================================================
CIVIL_MATTERS_NO_POLICE = [
    r"\b(?:debt|money\s+owed|loan|lent\s+money|borrowed|repay|payment\s+due)\b",
    r"\b(?:contract\s+(?:dispute|breach)|agreement|civil\s+suit)\b",
    r"\b(?:rent\s+(?:due|unpaid)|deposit\s+(?:return|refund))\b",
]

# Topics where police is WRONG escalation
CIVIL_ONLY_TOPICS = ["debt", "contract", "civil", "money_recovery"]

# ============================================================================
# INCORRECT ESCALATION FIXES
# ============================================================================
ESCALATION_FIXES = [
    # Employment disputes - NOT Consumer Forum
    (r"[Cc]onsumer [Ff]orum.*(?:employ|labour|labor|salary|termination|workplace|job|dismissal)",
     "Labour Commissioner, Industrial Tribunal, or Labour Court"),
    (r"(?:employ|labour|labor|salary|termination|workplace|job|dismissal).*[Cc]onsumer [Ff]orum",
     "Labour Commissioner, Industrial Tribunal, or Labour Court"),
    
    # Tenancy disputes - NOT Consumer Forum
    (r"[Cc]onsumer [Ff]orum.*(?:tenant|landlord|rent|tenancy|eviction|lease)",
     "Rent Controller, Rent Tribunal, or Civil Court"),
    (r"(?:tenant|landlord|rent|tenancy|eviction|lease).*[Cc]onsumer [Ff]orum",
     "Rent Controller, Rent Tribunal, or Civil Court"),
]

# ============================================================================
# TOPIC DETECTION FOR CORRECT ESCALATION
# ============================================================================
TOPIC_PATTERNS = {
    "employment": [
        r"\b(?:employ|job|salary|wages|termination|fired|dismissal|workplace|labour|labor|worker|workman)\b",
        r"\b(?:HR|employer|employee|contract\s+(?:job|work)|permanent|probation)\b"
    ],
    "tenancy": [
        r"\b(?:tenant|landlord|rent|lease|eviction|tenancy|rental|paying\s+guest|PG)\b",
        r"\b(?:flat|apartment|house|property).*(?:rent|lease|owner)\b"
    ],
    "consumer": [
        r"\b(?:product|service|defective|refund|warranty|consumer|purchase|bought|seller)\b",
        r"\b(?:online\s+(?:order|shopping)|e-commerce|delivery)\b"
    ],
    "family": [
        r"\b(?:divorce|marriage|custody|alimony|maintenance|domestic|spouse|husband|wife)\b",
        r"\b(?:child\s+support|matrimonial|dowry|DV|domestic\s+violence)\b"
    ],
    "criminal": [
        r"\b(?:FIR|arrested|bail|crime|criminal|theft|assault|murder)\b",
        r"\b(?:forgery|defamation|cyber\s*crime)\b"
    ],
    "debt": [
        r"\b(?:debt|owe[sd]?|loan|repay|recover\s+money)\b",
        r"\b(?:money\s+(?:lent|borrowed|due)|(?:lent|borrowed|lend)\s+money)\b",
        r"\b(?:not\s+(?:paying|returning|repaying)|cheque\s+bounce|dishonour)\b",
        r"\b(?:gave\s+(?:money|loan)|took\s+(?:money|loan)|won'?t\s+(?:pay|return))\b"
    ],
    "privacy": [
        r"\b(?:privacy|surveillance|spy|spying|recording|camera|tracking|hack)\b",
        r"\b(?:phone\s+tap|monitor|digital|screenshot|chat|message)\b"
    ],
    "property": [
        r"\b(?:property|land|plot|real\s+estate|registration|mutation|inheritance)\b",
        r"\b(?:will|succession|partition|boundary|encroachment)\b"
    ]
}

# Correct escalation paths by topic
CORRECT_ESCALATIONS = {
    "employment": "Labour Commissioner, Industrial Tribunal, or Labour Court",
    "tenancy": "Rent Controller, Rent Tribunal, or Civil Court",
    "consumer": "Consumer Forum or Consumer Disputes Redressal Commission",
    "family": "Family Court or Mediation Center",
    "criminal": "Police Station (FIR), Magistrate Court",
    "debt": "Civil Court (money suit), legal notice, or mediation",
    "property": "Civil Court, Revenue Court, or Tehsildar office",
    "privacy": "Cyber Cell (if criminal), or Civil Court for injunction",
    "default": "appropriate legal forum or Civil Court"
}

# ============================================================================
# STATE-SPECIFIC LAW TOPICS
# ============================================================================
STATE_SPECIFIC_TOPICS = [
    r"\b(?:rent\s+control|tenancy|landlord|tenant)\b",
    r"\b(?:labour|labor|minimum\s+wage|shop.*establishment)\b",
    r"\b(?:stamp\s+duty|registration|property\s+tax)\b",
    r"\b(?:excise|liquor|alcohol)\b",
    r"\b(?:agricultural|farming|land\s+reform)\b",
    r"\b(?:municipal|local\s+body|panchayat)\b",
]

# ============================================================================
# PRIVACY & EVIDENCE WARNINGS - CRITICAL SAFETY
# ============================================================================
PRIVACY_WARNING_STRONG = """
⚠️ **Critical Privacy Warning:**
• Accessing someone's phone, messages, or accounts WITHOUT their consent may be illegal (privacy violation, IT Act offenses, or theft)
• Admissibility ≠ Permission — courts may accept evidence, but OBTAINING it illegally is a separate offense
• Evidence ≠ Proof — screenshots or messages alone rarely prove anything conclusively in court
• Obtaining evidence without consent carries its own legal risks and may harm your case ethically
"""

FAMILY_EVIDENCE_WARNING = """
⚠️ **Important for Family/Divorce Matters:**
• Private messages showing infidelity are NOT automatic grounds for divorce in India
• Family courts evaluate overall conduct and circumstances, not just digital evidence
• Illegally obtained evidence may be admitted but could affect your credibility
• The burden of proof in family matters differs from criminal cases
"""

# Keywords that trigger privacy warnings - must indicate OBTAINING evidence (not just mentioning)
EVIDENCE_KEYWORDS = [
    r"\b(?:record(?:ing)?|spy|surveillance|monitor|track|hack)\b",  # Active surveillance
    r"\b(?:screenshot|phone\s+tap|hidden\s+camera)\b",  # Covert collection
    r"\b(?:collect\s+evidence|gather\s+evidence)\b",  # Explicit collection
    r"\b(?:whatsapp.*(?:evidence|proof)|sms.*(?:evidence|proof))\b",  # Messaging as evidence
    # Note: "cheating" moved to context-aware check - IPC 420 cheating is different from relationship cheating
]

# Keywords that should NOT trigger privacy warnings (normal evidence discussion)
NORMAL_EVIDENCE_CONTEXTS = [
    r"\b(?:bank\s+statement|receipt|invoice|contract|agreement)\b",
    r"\b(?:witness|testimony|document|letter|notice)\b",
    r"\b(?:IPC|section\s+\d+|penal\s+code|criminal)\b",  # Criminal law contexts
]

# IPC/Criminal law keywords - these indicate criminal cheating (Section 420), NOT relationship cheating
CRIMINAL_CHEATING_CONTEXT = [
    r"\b(?:IPC|section|penal\s+code|BNS)\b",
    r"\b(?:420|fraud|dishonest|property|induce)\b",
    r"\b(?:criminal|offense|offence|punishment|imprisonment)\b",
]

FAMILY_EVIDENCE_KEYWORDS = [
    r"\b(?:divorce|spouse|husband|wife|marriage)\b.*\b(?:affair|cheating|infidelity|adultery)\b",
    r"\b(?:affair|infidelity|adultery)\b.*\b(?:divorce|spouse|husband|wife|marriage)\b",
    r"\b(?:whatsapp|message|chat|screenshot).*(?:court|evidence|proof)\b",
    r"\b(?:evidence|proof).*(?:divorce|cheating|affair)\b",
    r"\b(?:my\s+(?:husband|wife|spouse).*(?:cheating|affair))\b",
    r"\b(?:prove.*(?:cheating|affair|infidelity))\b",
]

# Blocks to remove from responses
BLOCKS_TO_REMOVE = [
    r"\n*\*?\*?Sources?:?\*?\*?:?\s*\n[-•*].*?(?=\n\n|\n\*\*|$)",
    r"\n*\*?\*?References?:?\*?\*?:?\s*\n[-•*].*?(?=\n\n|\n\*\*|$)",
    r"\n*\*?\*?Referenced Sections?:?\*?\*?:?\s*\n[-•*].*?(?=\n\n|\n\*\*|$)",
    r"\n*\*?\*?Legal Sources?:?\*?\*?:?\s*\n[-•*].*?(?=\n\n|\n\*\*|$)",
]

# ============================================================================
# DEFAULT SECTIONS
# ============================================================================
DEFAULT_JURISDICTION = """
**Jurisdiction Note:**
This applies to Indian law, which can vary significantly by state. Your state may have specific provisions that differ from general principles.
"""

DEFAULT_DISCLAIMER = """
---
⚠️ **Disclaimer:** This is general legal information, not legal advice. Consult a qualified lawyer for advice specific to your situation.
"""

DEFAULT_NEXT_STEPS_TEMPLATE = """
**Suggested Next Steps:**
• Document all relevant details and preserve any evidence
• Consider direct communication or mediation first
• {escalation_path}
• Consulting a local lawyer can provide guidance tailored to your state and situation
"""

SAFE_FALLBACK = "This can vary based on specific facts, your state's laws, and individual circumstances. "


# ============================================================================
# TOPIC DETECTION
# ============================================================================
def detect_topic(text: str, query: str = "") -> str:
    """
    Detect the primary legal topic from text.
    
    Args:
        text: Combined text (or just response)
        query: Original user query - weighted more heavily for topic detection
        
    Returns:
        Detected topic string
    """
    # If query is provided separately, weight it more heavily
    if query:
        query_topic = _detect_topic_from_text(query.lower())
        # If query clearly identifies a topic, use that
        # This prevents response content (like "FIR") from overriding user intent
        if query_topic != "default":
            return query_topic
    
    return _detect_topic_from_text(text.lower())


def _detect_topic_from_text(text_lower: str) -> str:
    """Internal helper to detect topic from text."""
    topic_scores = {}
    for topic, patterns in TOPIC_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, text_lower, re.IGNORECASE))
        if score > 0:
            topic_scores[topic] = score
    
    if topic_scores:
        return max(topic_scores, key=topic_scores.get)
    return "default"


def needs_state_variation_note(text: str) -> bool:
    """Check if the topic requires state-specific law notice."""
    text_lower = text.lower()
    return any(re.search(p, text_lower, re.IGNORECASE) for p in STATE_SPECIFIC_TOPICS)


def needs_privacy_warning(text: str) -> bool:
    """
    Check if the topic involves privacy/evidence concerns that warrant a warning.
    Only trigger for surveillance/covert evidence collection, not normal evidence mentions.
    """
    text_lower = text.lower()
    
    # First check if this is a criminal law context (IPC 420 cheating, etc.)
    # IPC 420 "cheating" is about fraud, not relationship infidelity
    is_criminal_context = any(re.search(p, text_lower, re.IGNORECASE) for p in CRIMINAL_CHEATING_CONTEXT)
    if is_criminal_context:
        return False  # Don't show privacy warning for criminal law questions
    
    # Check for surveillance/covert collection keywords
    has_evidence_concern = any(re.search(p, text_lower, re.IGNORECASE) for p in EVIDENCE_KEYWORDS)
    
    # Check for normal evidence contexts (bank statements, witnesses, etc.)
    has_normal_evidence = any(re.search(p, text_lower, re.IGNORECASE) for p in NORMAL_EVIDENCE_CONTEXTS)
    
    # Check for relationship infidelity (not IPC 420 criminal cheating)
    is_relationship_infidelity = bool(re.search(
        r"\b(?:spouse|husband|wife|marriage|divorce).*(?:cheating|affair|infidelity)\b|\b(?:cheating|affair|infidelity).*(?:spouse|husband|wife|marriage|divorce)\b",
        text_lower, re.IGNORECASE
    ))
    
    return has_evidence_concern and (is_relationship_infidelity or not has_normal_evidence)


# ============================================================================
# RESPONSE CLEANING
# ============================================================================
def clean_response(response: str) -> str:
    """Remove forbidden phrases and replace with appropriate alternatives."""
    cleaned = response
    
    for pattern, replacement in FORBIDDEN_PHRASES:
        cleaned = re.sub(pattern, replacement, cleaned)
    
    return cleaned


def fix_escalation_paths(response: str, topic: str) -> str:
    """Fix incorrect escalation suggestions based on topic."""
    fixed = response
    
    # Apply specific fixes
    for pattern, replacement in ESCALATION_FIXES:
        fixed = re.sub(pattern, replacement, fixed, flags=re.IGNORECASE)
    
    # If Consumer Forum mentioned for non-consumer topics, fix it
    if topic in ["employment", "tenancy"] and re.search(r"[Cc]onsumer\s+[Ff]orum", fixed):
        correct_path = CORRECT_ESCALATIONS.get(topic, CORRECT_ESCALATIONS["default"])
        fixed = re.sub(
            r"[Cc]onsumer\s+[Ff]orum(?:\s+or\s+[Cc]onsumer\s+[Cc]ommission)?",
            correct_path,
            fixed
        )
    
    # CRITICAL: Block police escalation for civil matters
    fixed = block_police_for_civil_matters(fixed, topic)
    
    return fixed


def block_police_for_civil_matters(response: str, topic: str) -> str:
    """
    Remove police/FIR suggestions for civil matters like debt, money recovery.
    Police should NOT be contacted for civil disputes - this is a common misconception
    that can waste police resources and harm the person following the advice.
    """
    # Only apply to civil-only topics
    if topic not in CIVIL_ONLY_TOPICS:
        return response
    
    fixed = response
    civil_remedy = "Civil Court, legal notice, or mediation"
    
    # Patterns that wrongly suggest police for civil matters - order matters!
    # More specific patterns first, then general ones
    police_patterns = [
        # Combined patterns first
        (r"[Ff]ile\s+(?:an?\s+)?FIR\s+at\s+(?:the\s+)?police\s+station", f"pursue civil remedies through {civil_remedy}"),
        (r"[Ll]odge\s+(?:an?\s+)?FIR\s+(?:at|with)\s+(?:the\s+)?police", f"file a civil suit or send a legal notice"),
        # Misleading statements about police helping with debt
        (r"[Tt]he\s+police\s+(?:will|can)\s+help(?:\s+you)?(?:\s+recover)?(?:\s+the\s+money)?", "Civil courts can help through a money suit to recover the amount"),
        (r"[Pp]olice\s+(?:will|can)\s+(?:help|assist|recover)(?:\s+the\s+money)?", "Civil remedies through courts can help"),
        # Individual patterns
        (r"[Ff]ile\s+(?:an?\s+)?FIR", "send a legal notice or file a civil suit"),
        (r"[Ll]odge\s+(?:an?\s+)?FIR", "send a legal notice"),
        (r"[Aa]pproach\s+(?:the\s+)?police", f"approach {civil_remedy}"),
        (r"[Gg]o\s+to\s+(?:the\s+)?police", f"go to {civil_remedy}"),
        (r"[Cc]ontact\s+(?:the\s+)?police", f"send a legal notice or approach {civil_remedy}"),
        (r"[Rr]eport\s+to\s+(?:the\s+)?police", "pursue civil remedies"),
        (r"[Pp]olice\s+complaint", "legal notice or civil suit"),
        (r"(?:at\s+)?(?:the\s+)?[Pp]olice\s+station", "through civil courts"),
    ]
    
    for pattern, replacement in police_patterns:
        fixed = re.sub(pattern, replacement, fixed, flags=re.IGNORECASE)
    
    # Add clarification if police was mentioned
    if re.search(r"\bpolice\b|\bFIR\b", response, re.IGNORECASE) and topic == "debt":
        civil_note = "\n\n**Important:** Non-payment of debt is generally a civil matter, not a criminal offense. Police typically cannot help recover private debts. The proper remedy is through civil courts or legal notice."
        if civil_note not in fixed:
            # Add before disclaimer
            if "**Disclaimer" in fixed:
                fixed = fixed.replace("**Disclaimer", civil_note + "\n\n**Disclaimer")
            else:
                fixed = fixed.rstrip() + civil_note
    
    return fixed


def add_state_variation_note(response: str) -> str:
    """Add state variation warning if not present."""
    state_phrases = [
        "vary by state", "state's law", "state-specific", 
        "depends on.*state", "your state", "some states"
    ]
    
    has_state_note = any(re.search(p, response, re.IGNORECASE) for p in state_phrases)
    
    if not has_state_note:
        # Add to Important Context section if exists
        if "**Important Context:**" in response:
            response = response.replace(
                "**Important Context:**",
                "**Important Context:**\n• This may vary by state - some states have specific laws that differ"
            )
        elif "**Quick Answer:**" in response:
            # Add after Quick Answer
            parts = response.split("**Quick Answer:**", 1)
            if len(parts) == 2:
                answer_parts = parts[1].split("\n\n", 1)
                if len(answer_parts) == 2:
                    response = (
                        parts[0] + "**Quick Answer:**" + answer_parts[0] +
                        "\n\n**Important Context:**\n• State laws may vary - check your state's specific provisions\n\n" +
                        answer_parts[1]
                    )
    
    return response


def add_privacy_warning(response: str, query: str = "") -> str:
    """Add strong privacy warning for evidence/surveillance topics."""
    combined = f"{query} {response}".lower()
    
    # Check if already has adequate privacy warning
    strong_warning_phrases = [
        "without consent", "illegal", "separate offense", 
        "legal risk", "privacy violation", "obtaining it"
    ]
    has_strong_warning = sum(1 for p in strong_warning_phrases if p in response.lower()) >= 2
    
    if has_strong_warning:
        return response
    
    # Check if this is a family/divorce + evidence question
    is_family_evidence = any(
        re.search(p, combined, re.IGNORECASE) for p in FAMILY_EVIDENCE_KEYWORDS
    )
    
    # Choose appropriate warning
    if is_family_evidence:
        warning = FAMILY_EVIDENCE_WARNING + PRIVACY_WARNING_STRONG
    else:
        warning = PRIVACY_WARNING_STRONG
    
    # Add before disclaimer
    if "**Disclaimer" in response:
        response = response.replace("**Disclaimer", warning + "\n**Disclaimer")
    elif "Disclaimer:" in response:
        response = response.replace("Disclaimer:", warning + "\nDisclaimer:")
    elif "---" in response:
        parts = response.rsplit("---", 1)
        if len(parts) == 2:
            response = parts[0] + warning + "\n---" + parts[1]
    else:
        response = response.rstrip() + "\n" + warning
    
    return response


def remove_source_blocks(response: str) -> str:
    """Remove any Sources/References blocks that falsely imply verified legal texts."""
    cleaned = response
    
    for pattern in BLOCKS_TO_REMOVE:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.MULTILINE)
    
    # Also remove simple "Sources:" lines
    cleaned = re.sub(r"\n\*?\*?Sources?:?\*?\*?\s*\n", "\n", cleaned)
    cleaned = re.sub(r"\n\*?\*?References?:?\*?\*?\s*\n", "\n", cleaned)
    cleaned = re.sub(r"\n\*?\*?Referenced Sections?:?\*?\*?\s*\n", "\n", cleaned)
    
    return cleaned


def needs_family_evidence_warning(text: str) -> bool:
    """Check if query involves family matters + evidence collection."""
    text_lower = text.lower()
    
    # First check if this is a criminal law context (IPC 420 cheating, etc.)
    is_criminal_context = any(re.search(p, text_lower, re.IGNORECASE) for p in CRIMINAL_CHEATING_CONTEXT)
    if is_criminal_context:
        return False  # Don't show family warning for criminal law questions
    
    return any(re.search(p, text_lower, re.IGNORECASE) for p in FAMILY_EVIDENCE_KEYWORDS)


# ============================================================================
# STRUCTURE ENFORCEMENT
# ============================================================================
def ensure_jurisdiction_note(response: str) -> str:
    """Ensure the response includes jurisdiction information with state variation."""
    jurisdiction_phrases = ["Jurisdiction Note", "Indian law", "state's law", "vary by state"]
    
    has_jurisdiction = any(phrase in response for phrase in jurisdiction_phrases)
    
    if not has_jurisdiction:
        if "**Disclaimer" in response:
            response = response.replace("**Disclaimer", DEFAULT_JURISDICTION + "\n**Disclaimer")
        elif "---" in response:
            parts = response.rsplit("---", 1)
            if len(parts) == 2:
                response = parts[0] + DEFAULT_JURISDICTION + "---" + parts[1]
        else:
            response += DEFAULT_JURISDICTION
    
    return response


def ensure_disclaimer(response: str) -> str:
    """Ensure the response ends with the safety disclaimer."""
    disclaimer_patterns = [
        r"[Dd]isclaimer",
        r"not legal advice",
        r"consult.*lawyer",
        r"⚠️.*[Dd]isclaimer"
    ]
    
    has_disclaimer = any(re.search(p, response) for p in disclaimer_patterns)
    
    if not has_disclaimer:
        response = response.rstrip() + DEFAULT_DISCLAIMER
    
    return response


def ensure_next_steps(response: str, topic: str) -> str:
    """Ensure the response includes correct suggested next steps."""
    if "Next Steps" in response or "Suggested Next Steps" in response:
        return response
    
    escalation_path = CORRECT_ESCALATIONS.get(topic, CORRECT_ESCALATIONS["default"])
    next_steps = DEFAULT_NEXT_STEPS_TEMPLATE.format(
        escalation_path=f"If unresolved, {escalation_path} may be appropriate"
    )
    
    if "**Disclaimer" in response:
        response = response.replace("**Disclaimer", next_steps + "\n**Disclaimer")
    elif "---" in response:
        parts = response.rsplit("---", 1)
        if len(parts) == 2:
            response = parts[0] + next_steps + "\n---" + parts[1]
    else:
        response += next_steps
    
    return response


def truncate_case_law(response: str, max_case_length: int = 80) -> str:
    """Truncate long case law citations."""
    case_pattern = r'(\b[A-Z][a-z]+ v\.? [A-Z][a-z]+.*?)(\n|$)'
    
    def truncate_match(match):
        case_text = match.group(1)
        if len(case_text) > max_case_length:
            case_name_match = re.match(r'([A-Z][a-z]+ v\.? [A-Z][a-z]+)', case_text)
            if case_name_match:
                return case_name_match.group(1) + " (landmark case)" + match.group(2)
        return match.group(0)
    
    return re.sub(case_pattern, truncate_match, response)


def format_response_structure(response: str) -> str:
    """Format response into required structure if not already formatted."""
    if "**Quick Answer:**" in response or "Quick Answer:" in response:
        return response
    
    lines = response.strip().split('\n')
    quick_answer_lines = []
    remaining_lines = []
    sentence_count = 0
    
    for line in lines:
        if sentence_count < 4 and not line.startswith('•') and not line.startswith('-') and not line.startswith('**'):
            quick_answer_lines.append(line)
            sentence_count += line.count('.') + line.count('?') + line.count('!')
        else:
            remaining_lines.append(line)
    
    structured = "**Quick Answer:**\n"
    structured += '\n'.join(quick_answer_lines) + "\n\n"
    
    if remaining_lines:
        structured += "**Important Context:**\n"
        for line in remaining_lines[:4]:
            if line.strip() and not line.startswith('**'):
                if not line.startswith('•'):
                    structured += f"• {line.strip()}\n"
                else:
                    structured += f"{line}\n"
    
    return structured


def enforce_word_limit(response: str, max_words: int = 220) -> str:
    """Trim response if it exceeds word limit while preserving structure."""
    words = response.split()
    if len(words) <= max_words:
        return response
    
    # Keep essential sections, trim content
    sections = ["Quick Answer", "Important Context", "Jurisdiction", "Next Steps", "Disclaimer"]
    
    # Find disclaimer position and preserve it
    disclaimer_match = re.search(r'(---\s*\n*⚠️\s*\*\*Disclaimer.*)', response, re.DOTALL)
    disclaimer = disclaimer_match.group(1) if disclaimer_match else DEFAULT_DISCLAIMER
    
    # Remove disclaimer from main text
    main_text = re.sub(r'---\s*\n*⚠️\s*\*\*Disclaimer.*', '', response, flags=re.DOTALL)
    
    # Trim main text
    main_words = main_text.split()
    if len(main_words) > max_words - 30:  # Reserve words for disclaimer
        main_text = ' '.join(main_words[:max_words - 30]) + "..."
    
    return main_text.strip() + "\n" + disclaimer


# ============================================================================
# MAIN POST-PROCESSOR
# ============================================================================
def post_process_response(response: str, query: str = "") -> str:
    """
    Main post-processing function that applies all transformations.
    
    Args:
        response: Raw LLM response
        query: Original user query (for topic detection)
        
    Returns:
        Cleaned, formatted response with all required sections
    """
    if not response or response.startswith("Error"):
        return response
    
    # Detect topic - prioritize query over response to prevent response content
    # (like "FIR" in bad advice) from overriding user's actual question topic
    combined_text = f"{query} {response}"
    topic = detect_topic(combined_text, query=query)
    
    # Step 1: Remove source/reference blocks first
    processed = remove_source_blocks(response)
    
    # Step 2: Clean forbidden phrases
    processed = clean_response(processed)
    
    # Step 3: Fix incorrect escalation paths
    processed = fix_escalation_paths(processed, topic)
    
    # Step 4: Truncate long case law citations
    processed = truncate_case_law(processed)
    
    # Step 5: Format structure if needed
    processed = format_response_structure(processed)
    
    # Step 6: Add state variation note if needed
    if needs_state_variation_note(combined_text):
        processed = add_state_variation_note(processed)
    
    # Step 7: Add privacy/evidence warning if needed (with query for context)
    if needs_privacy_warning(combined_text) or needs_family_evidence_warning(combined_text):
        processed = add_privacy_warning(processed, query)
    
    # Step 8: Ensure jurisdiction note
    processed = ensure_jurisdiction_note(processed)
    
    # Step 9: Ensure next steps with correct escalation
    processed = ensure_next_steps(processed, topic)
    
    # Step 10: Ensure disclaimer at end
    processed = ensure_disclaimer(processed)
    
    # Step 11: Enforce word limit (increased for warnings)
    processed = enforce_word_limit(processed, max_words=280)
    
    return processed.strip()


# ============================================================================
# QUALITY CHECK
# ============================================================================
def check_response_quality(response: str) -> Dict[str, Any]:
    """Check if response meets quality requirements."""
    word_count = len(response.split())
    
    has_quick_answer = "Quick Answer" in response
    has_context = "Important Context" in response or "Context" in response
    has_jurisdiction = "Jurisdiction" in response or "state" in response.lower()
    has_next_steps = "Next Steps" in response
    has_disclaimer = "Disclaimer" in response or "not legal advice" in response.lower()
    
    # Check for remaining forbidden phrases
    has_forbidden = any(
        re.search(pattern, response) 
        for pattern, _ in FORBIDDEN_PHRASES
    )
    
    # Check for incorrect escalation
    has_wrong_escalation = bool(re.search(
        r"[Cc]onsumer\s+[Ff]orum.*(?:employ|tenant|rent|labour)",
        response
    ))
    
    return {
        "word_count": word_count,
        "within_word_limit": 150 <= word_count <= 250,
        "has_quick_answer": has_quick_answer,
        "has_context": has_context,
        "has_jurisdiction": has_jurisdiction,
        "has_next_steps": has_next_steps,
        "has_disclaimer": has_disclaimer,
        "has_forbidden_phrases": has_forbidden,
        "has_wrong_escalation": has_wrong_escalation,
        "quality_score": sum([
            has_quick_answer,
            has_context,
            has_jurisdiction,
            has_next_steps,
            has_disclaimer,
            not has_forbidden,
            not has_wrong_escalation
        ]) / 7.0
    }
