#!/usr/bin/env python3
"""
CET-6 Vocabulary Trainer - Wrong Words Manager

Manages the wrong word list for spaced repetition review.
Wrong words are stored in a JSON file for persistence across sessions.

Usage:
    python wrong_words.py add <word> <meaning> <error_type> [wrong_answer]
    python wrong_words.py list [--limit N]
    python wrong_words.py review [--count N]
    python wrong_words.py mastered <word>
    python wrong_words.py stats
"""

import json
import os
import sys
from datetime import datetime

# Default wrong words file location (current working directory)
# Caller should specify --filepath or set CET6_WRONG_WORDS env var for persistence
DEFAULT_FILE = os.path.join(os.getcwd(), "cet6_wrong_words.json")


def load_words(filepath=None):
    """Load wrong words from JSON file."""
    path = filepath or DEFAULT_FILE
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_words(words, filepath=None):
    """Save wrong words to JSON file."""
    path = filepath or DEFAULT_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


def add_word(word, meaning, error_type, wrong_answer="", filepath=None):
    """
    Add a word to the wrong list, or increment error count if already exists.

    Args:
        word: The English word
        meaning: Chinese meaning
        error_type: Type of error (spelling, meaning, part_of_speech, close_but_imprecise)
        wrong_answer: The incorrect answer the user gave
    """
    words = load_words(filepath)
    word_lower = word.lower()

    if word_lower in words:
        words[word_lower]["error_count"] += 1
        words[word_lower]["last_error"] = datetime.now().isoformat()
        if wrong_answer:
            words[word_lower]["wrong_answers"].append(wrong_answer)
    else:
        words[word_lower] = {
            "word": word,
            "meaning": meaning,
            "error_type": error_type,
            "error_count": 1,
            "first_error": datetime.now().isoformat(),
            "last_error": datetime.now().isoformat(),
            "wrong_answers": [wrong_answer] if wrong_answer else [],
            "mastered": False
        }

    save_words(words, filepath)
    print(f"✅ Added '{word}' to review list (error count: {words[word_lower]['error_count']})")


def list_words(limit=None, filepath=None):
    """List all wrong words sorted by error count (descending)."""
    words = load_words(filepath)
    if not words:
        print("📭 No wrong words yet. Keep practicing!")
        return

    sorted_words = sorted(words.values(), key=lambda x: x["error_count"], reverse=True)

    if limit:
        sorted_words = sorted_words[:limit]

    print(f"\n📋 Wrong Words Review List ({len(sorted_words)} words total):")
    print("-" * 60)
    for i, w in enumerate(sorted_words, 1):
        status = "✅" if w.get("mastered") else "❌"
        print(f"{i:2d}. {w['word']:20s} - {w['meaning']}  "
              f"[错误次数: {w['error_count']}] {status}")
    print("-" * 60)


def get_review_words(count=10, filepath=None):
    """
    Get words for review, prioritizing:
    1. Words with highest error count
    2. Most recently missed words
    3. Not yet mastered

    Returns list of word dicts.
    """
    words = load_words(filepath)
    if not words:
        return []

    # Filter out mastered words
    active = [w for w in words.values() if not w.get("mastered", False)]

    # Sort by error count (desc), then by last_error (most recent first)
    active.sort(key=lambda x: (-x["error_count"], x["last_error"]), reverse=False)
    # Actually we want highest error count first, and for ties most recent first
    active.sort(key=lambda x: (-x["error_count"], -datetime.fromisoformat(x["last_error"]).timestamp()))

    return active[:count]


def review_words(count=10, filepath=None):
    """Print review words for the next quiz."""
    review_list = get_review_words(count, filepath)
    if not review_list:
        print("🎉 No words need review! Great job!")
        return

    print(f"\n🔄 Words to Review in Next Quiz ({len(review_list)} words):")
    print("-" * 50)
    for w in review_list:
        print(f"  • {w['word']} — {w['meaning']} (错 {w['error_count']} 次)")
    print("-" * 50)


def mark_mastered(word, filepath=None):
    """Mark a word as mastered (remove from active review)."""
    words = load_words(filepath)
    word_lower = word.lower()

    if word_lower in words:
        words[word_lower]["mastered"] = True
        words[word_lower]["mastered_date"] = datetime.now().isoformat()
        save_words(words, filepath)
        print(f"🎉 '{word}' marked as mastered! Great job!")
    else:
        print(f"⚠️ Word '{word}' not found in the list.")


def show_stats(filepath=None):
    """Show statistics about wrong words."""
    words = load_words(filepath)
    if not words:
        print("📭 No data yet.")
        return

    total = len(words)
    mastered = sum(1 for w in words.values() if w.get("mastered"))
    active = total - mastered
    total_errors = sum(w["error_count"] for w in words.values())
    most_wrong = max(words.values(), key=lambda x: x["error_count"])

    print("\n📊 Wrong Words Statistics")
    print("=" * 40)
    print(f"  Total words tracked:  {total}")
    print(f"  Active (need review): {active}")
    print(f"  Mastered:             {mastered}")
    print(f"  Total errors:         {total_errors}")
    print(f"  Most missed word:     {most_wrong['word']} ({most_wrong['error_count']} times)")
    print("=" * 40)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "add" and len(sys.argv) >= 4:
        word = sys.argv[2]
        meaning = sys.argv[3]
        error_type = sys.argv[4] if len(sys.argv) > 4 else "spelling"
        wrong_answer = sys.argv[5] if len(sys.argv) > 5 else ""
        add_word(word, meaning, error_type, wrong_answer)

    elif command == "list":
        limit = None
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            if idx + 1 < len(sys.argv):
                limit = int(sys.argv[idx + 1])
        list_words(limit)

    elif command == "review":
        count = 10
        if "--count" in sys.argv:
            idx = sys.argv.index("--count")
            if idx + 1 < len(sys.argv):
                count = int(sys.argv[idx + 1])
        review_words(count)

    elif command == "mastered" and len(sys.argv) >= 3:
        mark_mastered(sys.argv[2])

    elif command == "stats":
        show_stats()

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
