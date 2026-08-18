from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/"
)

DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "bodex_ai"
)

COLLECTION_NAME = "knowledge"

# ============================================================
# MONGODB
# ============================================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DB_NAME]

knowledge_collection = db[COLLECTION_NAME]


# ============================================================
# DATABASE TEST
# ============================================================

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


# ============================================================
# GET ALL KNOWLEDGE
# ============================================================

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


# ============================================================
# NORMALIZE QUERY
# ============================================================

def normalize_query(query):

    if not query:
        return ""

    query = query.lower().strip()

    # Common spelling corrections
    corrections = {
        "braches": "branches",
        "brances": "branches",
        "branchs": "branches",
        "ceo's": "ceo",
        "ceo?": "ceo",
        "mission?": "mission",
        "projects?": "projects",
        "product?": "products",
        "products?": "products",
        "website?": "website",
        "founder?": "founder"
    }

    for wrong, correct in corrections.items():

        query = query.replace(
            wrong,
            correct
        )

    return query


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "the",
    "is",
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
    "how",
    "does",
    "do",
    "tell",
    "about",
    "me",
    "please",

    # Hindi / Hinglish
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
    "bataye",
    "batao",
    "bata",
    "mujhe",
    "ke",
    "baare",
    "barae"
}


# ============================================================
# GET SEARCH TERMS
# ============================================================

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


# ============================================================
# SEARCH KNOWLEDGE
# ============================================================

def search_knowledge(query, limit=5):

    if not query:
        return []

    words = query.lower().split()

    # Common words ignore karo
    stop_words = {
        "what",
        "is",
        "are",
        "the",
        "a",
        "an",
        "how",
        "can",
        "does",
        "do",
        "did",
        "for",
        "to",
        "of",
        "in",
        "on",
        "at",
        "and",
        "or",
        "with",
        "about",
        "from",
        "tell",
        "me",
        "please",
        "who",
        "which",
        "why"
    }

    keywords = [
        word
        for word in words
        if len(word) >= 3
        and word not in stop_words
    ]

    if not keywords:
        return []

    # OR search:
    # kisi bhi important keyword ka match mil jaye
    conditions = []

    for word in keywords:

        conditions.append({
            "$or": [
                {
                    "title": {
                        "$regex": word,
                        "$options": "i"
                    }
                },
                {
                    "content": {
                        "$regex": word,
                        "$options": "i"
                    }
                }
            ]
        })

    results = knowledge_collection.find(
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
    # --------------------------------------------------------
    # Relevance scoring
    # --------------------------------------------------------

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

        title_lower = title.lower()

        content_lower = content.lower()

        score = 0

        for term in terms:

            # Title match is more important
            if term in title_lower:

                score += 10

            # Content match
            if term in content_lower:

                score += 3

        if score > 0:

            scored.append(
                (
                    score,
                    item
                )
            )

    # --------------------------------------------------------
    # Sort by relevance
    # --------------------------------------------------------

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        item
        for score, item in scored[:limit]
    ]


# ============================================================
# EXTRACT RELEVANT CONTENT
# ============================================================

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

    if len(content) <= max_chars:

        return content

    terms = get_search_terms(
        query
    )

    if not terms:

        return content[
            :max_chars
        ]

    # --------------------------------------------------------
    # Split content into chunks
    # --------------------------------------------------------

    chunks = re.split(
        r"\n\s*\n|(?<=[.!?])\s+",
        content
    )

    relevant = []

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

    # --------------------------------------------------------
    # If relevant chunks found
    # --------------------------------------------------------

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

                break

            selected.append(
                chunk
            )

            current_length += (
                len(chunk)
            )

        if selected:

            return "\n".join(
                selected
            )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return content[
        :max_chars
    ]


# ============================================================
# BUILD CONTEXT
# ============================================================

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

    # --------------------------------------------------------
    # Each document
    # --------------------------------------------------------

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

        # Extract only relevant part
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

        # ----------------------------------------------------
        # Context limit
        # ----------------------------------------------------

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

        current_length += (
            len(part)
        )

    return "\n\n---\n\n".join(
        context_parts
    )


# ============================================================
# COUNT DOCUMENTS
# ============================================================

def knowledge_count():

    return knowledge_collection.count_documents(
        {}
    )


# ============================================================
# STARTUP CHECK
# ============================================================

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