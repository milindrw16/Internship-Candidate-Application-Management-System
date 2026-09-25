# ============================================================
#  ai_engine.py
#  NLP screening engine + database helpers
# ============================================================
import re
import numpy as np
import pandas as pd
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ------------------------------------------------------------------
# TUNABLES  (change these to recalibrate the model)
# ------------------------------------------------------------------
SEMANTIC_WEIGHT     = 0.45   # weight of TF-IDF text similarity
SKILL_WEIGHT        = 0.55   # weight of hard skill overlap
SEMANTIC_GAIN       = 2.2    # TF-IDF cosine on short docs is compressed -> boost it

STRONG_THRESHOLD    = 60     # >= 60  -> Strong match
MODERATE_THRESHOLD  = 35     # >= 35  -> Moderate match

DB_CONFIG = dict(
    host="localhost",
    user="root",
    password="root",
    database="Internship_Management",
)

# alias -> canonical form
SKILL_ALIASES = {
    "ml": "machine learning",
    "machine-learning": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "ai": "artificial intelligence",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "postgres": "postgresql",
    "powerbi": "power bi",
    "node": "node.js",
    "nodejs": "node.js",
    "reactjs": "react",
    "react.js": "react",
    "sklearn": "scikit-learn",
    "scikit": "scikit-learn",
    "tf": "tensorflow",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "excel": "microsoft excel",
    "ms excel": "microsoft excel",
    "rest api": "rest api",
    "restful": "rest api",
}


# ==================================================================
# 1. DATABASE
# ==================================================================
def get_connection():
    """Open a live MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


# Columns the engine needs. Missing ones are auto-created on startup.
REQUIRED_COLUMNS = {
    "Applications": {
        "AI_Match_Score":  "DECIMAL(5,2)  DEFAULT NULL",
        "Semantic_Score":  "DECIMAL(5,2)  DEFAULT NULL",
        "Skill_Score":     "DECIMAL(5,2)  DEFAULT NULL",
        "Matched_Skills":  "TEXT          DEFAULT NULL",
        "Missing_Skills":  "TEXT          DEFAULT NULL",
        "Recommendation":  "VARCHAR(48)   DEFAULT NULL",
        "Screened_At":     "DATETIME      DEFAULT NULL",
    }
}


def ensure_schema(conn):
    """
    Auto-migrate: add any missing AI columns to the Applications table.
    Returns a list of columns that were created.
    """
    created = []
    cur = conn.cursor()
    for table, cols in REQUIRED_COLUMNS.items():
        cur.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """,
            (DB_CONFIG["database"], table),
        )
        existing = {r[0] for r in cur.fetchall()}
        for col, ddl in cols.items():
            if col not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
                created.append(f"{table}.{col}")
    conn.commit()
    cur.close()
    return created


# ==================================================================
# 2. TEXT UTILITIES
# ==================================================================
def clean_text(text):
    """Lowercase + strip everything that isn't a letter/digit/+#."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[^a-zA-Z0-9+#.\s]", " ", text)
    return re.sub(r"\s+", " ", text).lower().strip()


def _canonical(skill: str) -> str:
    s = re.sub(r"\s+", " ", str(skill).strip().lower())
    return SKILL_ALIASES.get(s, s)


def parse_skills(raw) -> list:
    """Turn 'Python, ML; SQL / React' into ['python','machine learning','sql','react']."""
    if not isinstance(raw, str):
        return []
    parts = re.split(r"[,;/\n|•·]+", raw)
    out = []
    for p in parts:
        s = _canonical(p)
        if s and len(s) > 1 and s not in out:
            out.append(s)
    return out


def _skill_present(skill: str, resume_norm: str) -> bool:
    """Word-boundary search for a skill (and all of its aliases) in the resume."""
    variants = {skill}
    for alias, canonical in SKILL_ALIASES.items():
        if canonical == skill:
            variants.add(alias)
    for v in variants:
        pattern = r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])"
        if re.search(pattern, resume_norm):
            return True
    return False


# ==================================================================
# 3. THE MODEL
# ==================================================================
def score_application(job_text: str, required_skills: str, resume_text: str) -> dict:
    """
    Hybrid NLP scorer.

        final = SKILL_WEIGHT * skill_overlap + SEMANTIC_WEIGHT * tfidf_similarity

    Returns a dict with every value the dashboard needs.
    """
    job_clean    = clean_text(f"{job_text or ''} {required_skills or ''}")
    resume_clean = clean_text(resume_text)

    empty = {
        "final_score": 0.0, "semantic_score": 0.0, "skill_score": 0.0,
        "matched_skills": [], "missing_skills": [],
        "recommendation": "Not Recommended",
    }
    if not resume_clean or not job_clean:
        return empty

    # ---------- 3a. semantic similarity (TF-IDF + cosine) ----------
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )
        matrix = vectorizer.fit_transform([job_clean, resume_clean])
        cosine = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        cosine = 0.0

    semantic_pct = min(100.0, cosine * 100.0 * SEMANTIC_GAIN)

    # ---------- 3b. hard-skill overlap ----------
    skills = parse_skills(required_skills)
    if skills:
        matched = [s for s in skills if _skill_present(s, resume_clean)]
        missing = [s for s in skills if s not in matched]
        skill_pct = len(matched) / len(skills) * 100.0
    else:
        matched, missing = [], []
        skill_pct = semantic_pct

    # ---------- 3c. blended score ----------
    final = SKILL_WEIGHT * skill_pct + SEMANTIC_WEIGHT * semantic_pct

    if final >= 75:
        rec = "Strongly Recommended"
    elif final >= STRONG_THRESHOLD:
        rec = "Recommended"
    elif final >= MODERATE_THRESHOLD:
        rec = "Consider"
    else:
        rec = "Not Recommended"

    return {
        "final_score":     round(final, 2),
        "semantic_score":  round(semantic_pct, 2),
        "skill_score":     round(skill_pct, 2),
        "matched_skills":  matched,
        "missing_skills":  missing,
        "recommendation":  rec,
    }


# ==================================================================
# 4. BATCH RUNNER
# ==================================================================
PENDING_QUERY = """
    SELECT a.AppID,
           c.FullName,
           c.Resume_Text,
           j.JobID,
           j.Title,
           j.Job_Description,
           j.Required_Skills
    FROM Applications a
    JOIN Candidates   c ON a.CandidateID = c.CandidateID
    JOIN Job_Postings j ON a.JobID       = j.JobID
    WHERE a.Status = 'Applied'
"""

UPDATE_SQL = """
    UPDATE Applications
    SET AI_Match_Score = %s,
        Semantic_Score = %s,
        Skill_Score    = %s,
        Matched_Skills = %s,
        Missing_Skills = %s,
        Recommendation = %s,
        Status         = 'AI Screened',
        Screened_At    = NOW()
    WHERE AppID = %s
"""


def fetch_pending(conn) -> pd.DataFrame:
    return pd.read_sql(PENDING_QUERY, conn)


def run_screening(conn, on_progress=None) -> dict:
    """
    Score every 'Applied' application and write results back to MySQL.

    on_progress(done, total, candidate_name) is called after each row
    so Streamlit can drive a live progress bar.
    """
    pending = fetch_pending(conn)
    total = len(pending)

    summary = {
        "processed": total, "strong": 0, "moderate": 0,
        "low": 0, "avg_score": 0.0, "top_score": 0.0,
    }
    if total == 0:
        return summary

    cur = conn.cursor()
    scores = []

    for i, row in pending.iterrows():
        result = score_application(
            job_text=row["Job_Description"],
            required_skills=row["Required_Skills"],
            resume_text=row["Resume_Text"],
        )

        cur.execute(
            UPDATE_SQL,
            (
                result["final_score"],
                result["semantic_score"],
                result["skill_score"],
                ", ".join(result["matched_skills"])[:2000],
                ", ".join(result["missing_skills"])[:2000],
                result["recommendation"],
                int(row["AppID"]),
            ),
        )

        scores.append(result["final_score"])
        if result["final_score"] >= STRONG_THRESHOLD:
            summary["strong"] += 1
        elif result["final_score"] >= MODERATE_THRESHOLD:
            summary["moderate"] += 1
        else:
            summary["low"] += 1

        if on_progress:
            on_progress(i + 1, total, row["FullName"])

    conn.commit()
    cur.close()

    summary["avg_score"] = round(float(np.mean(scores)), 2)
    summary["top_score"] = round(float(np.max(scores)), 2)
    return summary


# ------------------------------------------------------------------
# CLI:  python ai_engine.py
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("Connecting to MySQL …")
    cn = get_connection()
    print("Schema check:", ensure_schema(cn) or "already up to date")

    def cli_progress(done, total, name):
        print(f"  [{done}/{total}] {name}")

    print("\n--- Running AI Candidate Profiling ---")
    stats = run_screening(cn, on_progress=cli_progress)
    print("\nDone:", stats)

    print("\n--- Final Analytics ---")
    dash = pd.read_sql(
        """
        SELECT j.Title AS Job_Role, c.FullName AS Candidate,
               a.AI_Match_Score, a.Recommendation, a.Status
        FROM Applications a
        JOIN Candidates   c ON a.CandidateID = c.CandidateID
        JOIN Job_Postings j ON a.JobID       = j.JobID
        ORDER BY j.JobID, a.AI_Match_Score DESC
        """,
        cn,
    )
    print(dash.to_string(index=False))
    cn.close()