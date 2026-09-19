import base64
import json
import os
import mimetypes

from dotenv import load_dotenv
from groq import Groq
from difflib import SequenceMatcher
from datetime import timedelta
from django.utils import timezone

load_dotenv()


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Check your .env file."
        )

    return Groq(api_key=api_key)


def classify_complaint(description):
    """
    Text-only fallback classification.
    """

    client = get_groq_client()

    prompt = f"""
You are CivicShield's AI civic issue classification engine.

Analyze this complaint:

{description}

Allowed categories:
garbage, road, streetlight, water, drainage, traffic, other

Allowed priorities:
low, medium, high, critical

Return ONLY valid JSON:

{{
    "category": "garbage",
    "priority": "high",
    "department": "Municipal Sanitation",
    "reason": "Short explanation"
}}
"""

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are CivicShield's AI classification engine. "
                    "Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_completion_tokens=300,
    )

    result = response.choices[0].message.content.strip()

    if result.startswith("```"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    return json.loads(result)


def analyze_complaint_image(image_path, description=""):

    client = get_groq_client()

    # Read image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    # Detect image MIME type
    mime_type, _ = mimetypes.guess_type(image_path)

    if not mime_type:
        mime_type = "image/jpeg"

    image_url = (
        f"data:{mime_type};base64,{image_data}"
    )

    prompt = f"""
Analyze this civic complaint image.

Citizen description:
{description}

Determine the civic issue visible in the image.

Allowed categories:
garbage
road
streetlight
water
drainage
traffic
other

Allowed priorities:
low
medium
high
critical

Return ONLY a JSON object with these fields:

category
priority
department
confidence
visual_evidence
reason

Example:

{{
    "category": "garbage",
    "priority": "high",
    "department": "Municipal Sanitation",
    "confidence": 90,
    "visual_evidence": "Garbage is overflowing from a public collection bin.",
    "reason": "The image shows a significant accumulation of garbage."
}}

Rules:
- confidence must be an integer from 0 to 100.
- category must use one of the allowed values.
- priority must use one of the allowed values.
- Do not use markdown.
- Do not use ``` characters.
- Do not add extra fields.
"""

    response = client.chat.completions.create(

        model="qwen/qwen3.8-27b",

        messages=[
            {
                "role": "system",
                "content": (
                    "You are CivicShield Vision AI. "
                    "Analyze civic issue images and return "
                    "ONLY a valid JSON object."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ],

        response_format={
            "type": "json_object"
        },

        temperature=0,

        max_completion_tokens=600,

        reasoning_effort="none"
    )

    # Get model output
    result = response.choices[0].message.content

    print("\n========== GROQ VISION RESPONSE ==========")
    print(result)
    print("==========================================\n")

    if not result:
        raise RuntimeError(
            "Groq Vision returned an empty response."
        )

    result = result.strip()

    # Remove markdown if model accidentally adds it
    if result.startswith("```"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    try:

        return json.loads(result)

    except json.JSONDecodeError:

        print("INVALID GROQ JSON:")
        print(result)

        raise RuntimeError(
            "Groq Vision returned invalid JSON."
        )
def calculate_severity(ai_result, description):
    """
    Calculate CivicShield severity score from
    AI priority and complaint context.
    """

    priority_scores = {
        "low": 25,
        "medium": 50,
        "high": 75,
        "critical": 95,
    }

    priority = str(
        ai_result.get("priority", "medium")
    ).lower()

    score = priority_scores.get(
        priority,
        50
    )

    text = description.lower()

    # Dangerous situations
    danger_keywords = [
        "accident",
        "danger",
        "dangerous",
        "injury",
        "injured",
        "fire",
        "open manhole",
        "electrical",
        "electric shock",
        "collapsed",
        "flood",
        "blocked road",
        "school",
        "hospital",
    ]

    if any(
        keyword in text
        for keyword in danger_keywords
    ):
        score += 8

    # Large-scale problems
    scale_keywords = [
        "huge",
        "large",
        "massive",
        "overflowing",
        "entire road",
        "many people",
        "several days",
        "multiple",
    ]

    for keyword in scale_keywords:

        if keyword in text:
            score += 5

    # Keep between 0 and 100
    score = min(
        max(score, 0),
        100
    )

    # Final priority
    if score >= 90:
        final_priority = "critical"

    elif score >= 70:
        final_priority = "high"

    elif score >= 40:
        final_priority = "medium"

    else:
        final_priority = "low"

    return {
        "score": score,
        "priority": final_priority
    }
def route_department(category):
    """
    CivicShield's deterministic department routing engine.
    """

    department_map = {
        "garbage": "Municipal Sanitation",
        "road": "Roads & Infrastructure",
        "streetlight": "Electrical Department",
        "water": "Water Supply Department",
        "drainage": "Drainage & Sewerage Department",
        "traffic": "Traffic Department",
        "other": "General Civic Services",
    }

    category = str(category).lower().strip()

    return department_map.get(
        category,
        "General Civic Services"
    )
def calculate_text_similarity(text1, text2):
    """
    Calculate similarity between two complaint descriptions.
    Returns a percentage from 0 to 100.
    """

    text1 = str(text1 or "").lower().strip()
    text2 = str(text2 or "").lower().strip()

    if not text1 or not text2:
        return 0

    similarity = SequenceMatcher(
        None,
        text1,
        text2
    ).ratio()

    return round(similarity * 100, 1)
def calculate_location_similarity(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Approximate geographic distance using
    latitude/longitude.

    Returns distance in meters.
    """

    if (
        lat1 is None
        or lon1 is None
        or lat2 is None
        or lon2 is None
    ):
        return None

    from math import radians, sin, cos, sqrt, atan2

    R = 6371000

    lat1 = radians(float(lat1))
    lat2 = radians(float(lat2))

    dlat = lat2 - lat1

    dlon = radians(
        float(lon2) - float(lon1)
    )

    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return round(R * c, 1)
def detect_duplicate_complaint(
    complaint,
    existing_complaints
):
    """
    Find whether a newly submitted complaint
    is likely a duplicate of an existing complaint.

    Returns:
        {
            "is_duplicate": bool,
            "score": float,
            "matched_complaint": object or None,
            "reason": str
        }
    """

    best_score = 0
    best_match = None
    best_reason = ""

    for existing in existing_complaints:

        # Don't compare with itself
        if existing.pk == complaint.pk:
            continue

        # Ignore resolved complaints
        if existing.status == "resolved":
            continue

        text_score = calculate_text_similarity(
            complaint.description,
            existing.description
        )

        # Category match
        category_score = 100 if (
            complaint.category
            and existing.category
            and complaint.category == existing.category
        ) else 0

        # Location score
        distance = calculate_location_similarity(
            complaint.latitude,
            complaint.longitude,
            existing.latitude,
            existing.longitude
        )

        if distance is None:

            location_score = 0

        elif distance <= 100:

            location_score = 100

        elif distance <= 250:

            location_score = 70

        elif distance <= 500:

            location_score = 40

        else:

            location_score = 0

        # Time similarity
        time_score = 0

        if (
            complaint.created_at
            and existing.created_at
        ):

            time_difference = abs(
                complaint.created_at
                - existing.created_at
            )

            if time_difference <= timedelta(hours=2):

                time_score = 100

            elif time_difference <= timedelta(hours=6):

                time_score = 60

            elif time_difference <= timedelta(hours=24):

                time_score = 30

        # Combined score
        score = (
            text_score * 0.45
            +
            category_score * 0.25
            +
            location_score * 0.20
            +
            time_score * 0.10
        )

        score = round(score, 1)

        if score > best_score:

            best_score = score
            best_match = existing

            best_reason = (
                f"Text similarity: {text_score}%, "
                f"Category match: {category_score}%, "
                f"Location distance: "
                f"{distance if distance is not None else 'N/A'}m, "
                f"Time similarity: {time_score}%."
            )

    return {
        "is_duplicate": best_score >= 70,
        "score": best_score,
        "matched_complaint": best_match,
        "reason": best_reason,
    }
def create_incident_title(category, description):
    """
    Generate a readable civic incident title
    without requiring another AI call.
    """

    category_titles = {
        "garbage": "Garbage Management Issue",
        "road": "Road Infrastructure Issue",
        "streetlight": "Streetlight Issue",
        "water": "Water Supply Issue",
        "drainage": "Drainage Issue",
        "traffic": "Traffic Issue",
        "other": "Civic Issue",
    }

    return category_titles.get(
        str(category).lower(),
        "Civic Issue"
    )
def get_or_create_incident(complaint, duplicate_result):
    """
    Attach duplicate/similar complaints to the same
    CivicIncident.

    Exact duplicate text is always grouped together.
    """

    from .models import CivicIncident, Complaint

    def normalize(text):
        if not text:
            return ""

        return " ".join(
            text.lower().strip().split()
        )

    current_text = normalize(
        complaint.description
    )

    # =================================================
    # 1. CHECK FOR EXACT SAME COMPLAINT
    # =================================================

    if current_text:

        existing_complaints = (
            Complaint.objects
            .exclude(pk=complaint.pk)
            .exclude(incident=None)
        )

        for existing in existing_complaints:

            if normalize(
                existing.description
            ) == current_text:

                # Same complaint already belongs
                # to an incident.
                return existing.incident

    # =================================================
    # 2. CHECK AI DUPLICATE RESULT
    # =================================================

    matched_complaint = (
        duplicate_result.get(
            "matched_complaint"
        )
    )

    if (
        duplicate_result.get("is_duplicate")
        and matched_complaint
    ):

        # Existing complaint already belongs
        # to an incident.
        if matched_complaint.incident:

            return matched_complaint.incident

        # Create incident and attach the
        # existing complaint to it.
        incident = CivicIncident.objects.create(

            title=create_incident_title(
                complaint.category,
                complaint.description
            ),

            category=complaint.category,

            department=(
                complaint.department
                or matched_complaint.department
            ),

            priority=complaint.priority,

            status=complaint.status,

            latitude=(
                complaint.latitude
                or matched_complaint.latitude
            ),

            longitude=(
                complaint.longitude
                or matched_complaint.longitude
            ),
        )

        matched_complaint.incident = incident

        matched_complaint.save(
            update_fields=["incident"]
        )

        return incident

    # =================================================
    # 3. NO DUPLICATE → CREATE NEW INCIDENT
    # =================================================

    return CivicIncident.objects.create(

        title=create_incident_title(
            complaint.category,
            complaint.description
        ),

        category=complaint.category,

        department=complaint.department,

        priority=complaint.priority,

        status=complaint.status,

        latitude=complaint.latitude,

        longitude=complaint.longitude,
    )