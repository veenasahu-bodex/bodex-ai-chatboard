from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

load_dotenv()


# =========================================================
# CONFIG
# =========================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/"
)

DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "bodex_ai"
)

COLLECTION_NAME = "knowledge"


# =========================================================
# MONGODB
# =========================================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DB_NAME]

knowledge_collection = db[COLLECTION_NAME]


# =========================================================
# DATABASE TEST
# =========================================================

def check_database():

    try:

        client.admin.command("ping")

        print("MongoDB connected")
        print("Database:", DB_NAME)
        print("Collection:", COLLECTION_NAME)

        return True

    except Exception as e:

        print(
            "MongoDB connection error:",
            repr(e)
        )

        return False


# =========================================================
# GET ALL KNOWLEDGE
# =========================================================

def get_all_knowledge():

    return list(
        knowledge_collection.find(
            {},
            {
                "_id": 0,
                "url": 1,
                "title": 1,
                "content": 1,
                "scraped_at": 1
            }
        )
    )


# =========================================================
# NORMALIZE QUERY
# =========================================================

def normalize_query(query):

    if not query:
        return ""

    query = str(query).lower().strip()

    corrections = {

        # Branch
        "braches": "branches",
        "brances": "branches",
        "branchs": "branches",

        # CEO
        "ceo's": "ceo",
        "ceo?": "ceo",

        # Mission
        "mission?": "mission",

        # Projects
        "project?": "project",
        "projects?": "projects",

        # Products
        "product?": "product",
        "products?": "products",

        # Website
        "website?": "website",

        # Founder
        "founder?": "founder",

        # Career
        "careers?": "career",
        "jobs": "job",
        "candidates": "candidate",

        # Services
        "services?": "service",

        # Solutions
        "solutions?": "solution",

        # Analytics
        "analytics?": "analytics",

        # Security
        "security?": "security"
    }

    for wrong, correct in corrections.items():

        query = query.replace(
            wrong,
            correct
        )

    return query


# =========================================================
# STOP WORDS
# =========================================================

STOP_WORDS = {

    # -------------------------
    # English
    # -------------------------

    "the",
    "is",
    "are",
    "was",
    "were",

    "of",
    "a",
    "an",

    "and",
    "or",

    "to",
    "for",

    "in",
    "on",
    "at",

    "what",
    "who",
    "which",
    "where",
    "when",
    "why",

    "how",

    "does",
    "do",
    "did",

    "can",
    "could",
    "would",
    "should",

    "tell",
    "about",
    "me",

    "please",

    "with",
    "from",

    "this",
    "that",

    "company",

    "their",
    "its",

    # -------------------------
    # Hindi / Hinglish
    # -------------------------

    "ka",
    "ki",
    "ke",
    "ko",

    "kya",

    "hai",
    "hain",

    "kaun",
    "kon",
    "koun",

    "kise",
    "kis",

    "mein",
    "me",

    "par",
    "se",

    "aur",

    "batao",
    "bata",
    "bataye",

    "mujhe",

    "baare",
    "barae"
}


# =========================================================
# GET SEARCH TERMS
# =========================================================

def get_search_terms(query):

    query = normalize_query(
        query
    )

    words = re.findall(
        r"[a-zA-Z0-9]+",
        query
    )

    terms = []

    for word in words:

        if len(word) < 2:
            continue

        if word in STOP_WORDS:
            continue

        if word not in terms:

            terms.append(word)

    return terms


# =========================================================
# SEARCH KNOWLEDGE
# =========================================================

def search_knowledge(
    query,
    limit=5
):

    if not query:
        return []

    # -----------------------------------------------------
    # Get important search terms
    # -----------------------------------------------------

    terms = get_search_terms(
        query
    )

    if not terms:
        return []

    # -----------------------------------------------------
    # MongoDB search conditions
    # -----------------------------------------------------

    conditions = []

    for term in terms:

        escaped_term = re.escape(
            term
        )

        conditions.append({

            "$or": [

                {
                    "title": {
                        "$regex": escaped_term,
                        "$options": "i"
                    }
                },

                {
                    "content": {
                        "$regex": escaped_term,
                        "$options": "i"
                    }
                }

            ]

        })

    # -----------------------------------------------------
    # Fetch matching documents
    # -----------------------------------------------------

    documents = list(
        knowledge_collection.find(
            {
                "$or": conditions
            },
            {
                "_id": 0,
                "url": 1,
                "title": 1,
                "content": 1
            }
        )
    )

    if not documents:

        return []

    # -----------------------------------------------------
    # Score documents
    # -----------------------------------------------------

    scored = []

    for item in documents:

        title = str(
            item.get(
                "title",
                ""
            )
        )

        content = str(
            item.get(
                "content",
                ""
            )
        )

        url = str(
            item.get(
                "url",
                ""
            )
        )

        title_lower = title.lower()

        content_lower = content.lower()

        url_lower = url.lower()

        combined = (
            title_lower
            + " "
            + content_lower
        )

        score = 0

        # =================================================
        # GENERAL KEYWORD SCORE
        # =================================================

        for term in terms:

            # Title match
            if term in title_lower:

                score += 15

            # Content match
            if term in content_lower:

                score += 3

            # URL match
            if term in url_lower:

                score += 5

        # =================================================
        # CAREERS / JOB
        # =================================================

        career_terms = {
            "candidate",
            "apply",
            "job",
            "career",
            "careers",
            "join",
            "hiring",
            "vacancy",
            "vacancies"
        }

        if any(
            term in career_terms
            for term in terms
        ):

            # Exact Careers URL
            if "/careers/" in url_lower:

                score += 500

            # Careers title
            if (
                "career" in title_lower
                or "careers" in title_lower
                or "join our tech team" in title_lower
            ):

                score += 300

            # Careers content
            if (
                "career" in combined
                or "careers" in combined
                or "join our" in combined
                or "hiring" in combined
            ):

                score += 100

        # =================================================
        # FOUNDER / CEO
        # =================================================

        leadership_terms = {
            "founder",
            "ceo",
            "leadership",
            "director"
        }

        if any(
            term in leadership_terms
            for term in terms
        ):

            if (
                "founder" in combined
                or "ceo" in combined
                or "leadership" in combined
                or "director" in combined
            ):

                score += 100

        # =================================================
        # MISSION / VISION
        # =================================================

        if (
            "mission" in terms
            or "vision" in terms
        ):

            if (
                "mission" in combined
                or "vision" in combined
                or "purpose" in combined
            ):

                score += 100

        # =================================================
        # PRODUCTS / PROJECTS
        # =================================================

        product_terms = {
            "product",
            "products",
            "project",
            "projects",
            "saas",
            "tool",
            "tools"
        }

        if any(
            term in product_terms
            for term in terms
        ):

            if (
                "product" in combined
                or "products" in combined
                or "project" in combined
                or "projects" in combined
                or "saas" in combined
                or "tool" in combined
            ):

                score += 80

        # =================================================
        # SERVICES / SOLUTIONS
        # =================================================

        service_terms = {
            "service",
            "services",
            "solution",
            "solutions",
            "software",
            "development"
        }

        if any(
            term in service_terms
            for term in terms
        ):

            if (
                "service" in combined
                or "services" in combined
                or "solution" in combined
                or "solutions" in combined
                or "software" in combined
                or "development" in combined
            ):

                score += 70

        # =================================================
        # DATA / ANALYTICS / SECURITY
        # =================================================

        data_terms = {
            "data",
            "analytics",
            "management",
            "security",
            "anomaly"
        }

        if any(
            term in data_terms
            for term in terms
        ):

            if (
                "data" in combined
                or "analytics" in combined
                or "management" in combined
                or "security" in combined
                or "anomaly" in combined
            ):

                score += 70

        # =================================================
        # AI
        # =================================================

        ai_terms = {
            "ai",
            "artificial",
            "intelligence",
            "model",
            "models"
        }

        if any(
            term in ai_terms
            for term in terms
        ):

            if (
                "ai" in combined
                or "artificial intelligence" in combined
                or "model" in combined
            ):

                score += 50

        # =================================================
        # WEBSITE
        # =================================================

        if (
            "website" in terms
            or "web" in terms
            or "link" in terms
        ):

            if (
                "bodex.io" in url_lower
                or "website" in combined
            ):

                score += 100

        # =================================================
        # ADD RESULT
        # =================================================

        if score > 0:

            scored.append(
                (
                    score,
                    item
                )
            )

    # =====================================================
    # SORT BY SCORE
    # =====================================================

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        item
        for score, item in scored[:limit]
    ]


# =========================================================
# EXTRACT RELEVANT CONTENT
# =========================================================

def extract_relevant_content(
    content,
    query,
    max_chars=3500
):

    if not content:

        return ""

    content = str(
        content
    ).strip()

    # Content already small
    if len(content) <= max_chars:

        return content

    terms = get_search_terms(
        query
    )

    if not terms:

        return content[
            :max_chars
        ]

    # -----------------------------------------------------
    # Split content
    # -----------------------------------------------------

    chunks = re.split(
        r"\n\s*\n|(?<=[.!?])\s+",
        content
    )

    relevant = []

    # -----------------------------------------------------
    # Score chunks
    # -----------------------------------------------------

    for chunk in chunks:

        chunk_clean = chunk.strip()

        if not chunk_clean:

            continue

        chunk_lower = (
            chunk_clean.lower()
        )

        score = 0

        for term in terms:

            if term in chunk_lower:

                score += 1

        if score > 0:

            relevant.append(
                (
                    score,
                    chunk_clean
                )
            )

    # -----------------------------------------------------
    # Return relevant chunks
    # -----------------------------------------------------

    if relevant:

        relevant.sort(
            key=lambda x: x[0],
            reverse=True
        )

        selected = []

        current_length = 0

        for score, chunk in relevant:

            if (
                current_length
                + len(chunk)
                > max_chars
            ):

                continue

            selected.append(
                chunk
            )

            current_length += len(
                chunk
            )

        if selected:

            return "\n".join(
                selected
            )

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    return content[
        :max_chars
    ]


# =========================================================
# BUILD KNOWLEDGE CONTEXT
# =========================================================

def get_knowledge_context(
    query,
    limit=3,
    max_chars=9000
):

    results = search_knowledge(
        query,
        limit
    )

    if not results:

        return ""

    context_parts = []

    current_length = 0

    # -----------------------------------------------------
    # Build context
    # -----------------------------------------------------

    for item in results:

        title = str(
            item.get(
                "title",
                ""
            )
        )

        url = str(
            item.get(
                "url",
                ""
            )
        )

        content = str(
            item.get(
                "content",
                ""
            )
        )

        relevant_content = (
            extract_relevant_content(
                content,
                query,
                max_chars=2500
            )
        )

        part = f"""
TITLE:
{title}

URL:
{url}

CONTENT:
{relevant_content}
""".strip()

        # -------------------------------------------------
        # Context limit
        # -------------------------------------------------

        if (
            current_length
            + len(part)
            > max_chars
        ):

            remaining = (
                max_chars
                - current_length
            )

            if remaining > 300:

                part = part[
                    :remaining
                ]

                context_parts.append(
                    part
                )

            break

        context_parts.append(
            part
        )

        current_length += len(
            part
        )

    return "\n\n---\n\n".join(
        context_parts
    )


# =========================================================
# COUNT DOCUMENTS
# =========================================================

def knowledge_count():

    return knowledge_collection.count_documents(
        {}
    )


# =========================================================
# STARTUP CHECK
# =========================================================

if __name__ == "__main__":

    print(
        "=============================="
    )

    if check_database():

        print(
            "Knowledge documents:",
            knowledge_count()
        )

    print(
        "=============================="
    )

    # -----------------------------------------------------
    # TEST QUERY
    # -----------------------------------------------------

    test_query = (
        "How can a candidate apply "
        "for a job at BODEX?"
    )

    print("")
    print("Test query:")
    print(test_query)

    results = search_knowledge(
        test_query,
        limit=5
    )

    print("")
    print("Search results:")

    for index, item in enumerate(
        results,
        start=1
    ):

        print(
            f"{index}. "
            f"{item.get('title', '')}"
        )

        print(
            f"   {item.get('url', '')}"
        )

    print(
        "=============================="
    )