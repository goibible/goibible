"""GOI Translation Quality Assurance Validator

Enforces semantic integrity and naturalness metrics per gameplan.
"""
import os
import json
import argparse
import sqlite3
from textstat import flesch_kincaid_grade, lexicon_count

# SECURITY ENFORCEMENT
if os.environ.get('NETWORK_ACCESS') != 'BLOCKED':
    raise RuntimeError("SECURITY VIOLATION: Network access not permitted")

DB_PATH = 'translation_rails.db'


class QualityValidator:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        
    def validate_book(self, book):
        """Run full QA validation for a book"""
        results = {
            'semantic_integrity': self._check_semantics(book),
            'naturalness': self._check_naturalness(book),
            'consistency': self._check_consistency(book)
        }
        
        # Calculate overall score
        scores = [v['score'] for v in results.values()]
        results['overall'] = {
            'score': sum(scores) / len(scores),
            'pass': all(v['pass'] for v in results.values())
        }
        
        return results

    def _check_semantics(self, book):
        """Verify semantic integrity per gameplan"""
        # Check 1: Article usage
        self.cursor.execute("""
            SELECT COUNT(*) FROM decisions
            WHERE verse_id IN (
                SELECT verse_id FROM verses WHERE book = ?
            ) AND has_unauthorized_article = 1
        """, (book,))
        article_errors = self.cursor.fetchone()[0]

        # Check 2: אֶת omission
        self.cursor.execute("""
            SELECT COUNT(*) FROM translations
            WHERE verse_id IN (
                SELECT id FROM verses WHERE book = ?
            ) AND contains_et = 1
        """, (book,))
        et_errors = self.cursor.fetchone()[0]

        total = self._get_verse_count(book)
        error_rate = (article_errors + et_errors) / total
        
        return {
            'name': 'Semantic Integrity',
            'score': max(0, 100 - (error_rate * 100)),
            'pass': error_rate <= 0.05,
            'details': f"{article_errors} article errors, {et_errors} 'et' violations"
        }

    def _check_naturalness(self, book):
        """Validate English readability metrics"""
        self.cursor.execute("""
            SELECT translation_text FROM translations
            WHERE verse_id IN (
                SELECT id FROM verses WHERE book = ?
            )
        """, (book,))
        
        texts = [row[0] for row in self.cursor.fetchall()]
        if not texts:
            return {'score': 0, 'pass': False}

        # Flesch-Kincaid grade level
        fk_grade = flesch_kincaid_grade(' '.join(texts))
        
        # Preposition density
        total_words = lexicon_count(' '.join(texts), removepunct=True)
        prepositions = sum(t.count(' of ') + t.count(' in ') for t in texts)
        prep_density = (prepositions / total_words) * 100

        # Passive voice check (simplified)
        passives = sum(' be ' in t.lower() for t in texts)
        passive_rate = (passives / len(texts)) * 100

        # Scoring (target: FK 8-10, prep <15%, passive <5%)
        fk_score = 100 if 8 <= fk_grade <= 10 else max(0, 100 - abs(fk_grade - 9) * 20)
        prep_score = 100 if prep_density < 15 else max(0, 100 - (prep_density - 15) * 10)
        passive_score = 100 if passive_rate < 5 else max(0, 100 - (passive_rate - 5) * 20)
        
        score = (fk_score + prep_score + passive_score) / 3
        
        return {
            'name': 'Naturalness',
            'score': score,
            'pass': score >= 90,
            'details': f"FK: {fk_grade:.1f}, Prep: {prep_density:.1f}%, Passive: {passive_rate:.1f}%"
        }

    def _check_consistency(self, book):
        """Verify noun translation consistency"""
        # Check top 200 nouns for consistent translation
        self.cursor.execute("""
            SELECT strongs_id, COUNT(DISTINCT translation) AS variants
            FROM translations
            JOIN lexemes USING(strongs_id)
            WHERE lexemes.freq_rank <= 200
            AND verse_id IN (SELECT id FROM verses WHERE book = ?)
            GROUP BY strongs_id
            HAVING variants > 1
        """, (book,))
        
        inconsistent = self.cursor.fetchall()
        total_nouns = self._get_top_noun_count(book)
        
        error_rate = len(inconsistent) / total_nouns if total_nouns else 0
        return {
            'name': 'Noun Consistency',
            'score': max(0, 100 - (error_rate * 100)),
            'pass': error_rate == 0,
            'details': f"{len(inconsistent)}/{total_nouns} top nouns inconsistent"
        }

    def _get_verse_count(self, book):
        self.cursor.execute("SELECT COUNT(*) FROM verses WHERE book = ?", (book,))
        return self.cursor.fetchone()[0]

    def _get_top_noun_count(self, book):
        self.cursor.execute("""
            SELECT COUNT(DISTINCT strongs_id)
            FROM verse_lexemes
            JOIN lexemes USING(strongs_id)
            WHERE lexemes.freq_rank <= 200
            AND verse_id IN (SELECT id FROM verses WHERE book = ?)
        """, (book,))
        return self.cursor.fetchone()[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--book', required=True, help='Book to validate')
    parser.add_argument('--last-error', action='store_true', 
                        help='Generate error report for last failure')
    args = parser.parse_args()

    validator = QualityValidator()
    results = validator.validate_book(args.book)

    if args.last_error:
        # Generate harness-compatible error report
        print(f"Semantic integrity: {results['semantic_integrity']['score']:.1f}%")
        print(f"Naturalness: {results['naturalness']['score']:.1f}%")
        print(f"Noun consistency: {results['consistency']['score']:.1f}%")
        print(f"resume={args.book}:{results.get('last_failed_verse', '1')}")
    else:
        print(json.dumps(results, indent=2))