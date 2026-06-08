"""GOI Bible Translation - Phase 3: Quality Assurance

Implements semantic integrity scoring, naturalness validation, and traceability audits.
Enforces 95% quality gate with automatic rollback capability.
"""
import os
import json
import sqlite3
import argparse
import re
import textstat
from datetime import datetime

# SECURITY ENFORCEMENT
if os.environ.get('NETWORK_ACCESS') != 'BLOCKED':
    raise RuntimeError("SECURITY VIOLATION: Network access not permitted")

DB_PATH = 'translation_rails.db'
CHECKPOINT_FILE = 'phase3.checkpoint'

# QUALITY THRESHOLDS (from gameplan)
SEMANTIC_INTEGRITY_MIN = 95.0
NATURALNESS_MIN = 85.0
NOUN_CONSISTENCY_MIN = 98.0


class HarnessEvent:
    """Emits Commander-compatible events for real-time monitoring"""
    @staticmethod
    def log_status(book_ref, status, message):
        event = {
            'operation': 'log',
            'message': f"[{datetime.now().isoformat()}] {book_ref}: {status} - {message}",
            'agent_name': 'goi-qa'
        }
        print(f"HARNESS_EVENT:{json.dumps(event)}")

    @staticmethod
    def update_progress(completed, total, score):
        progress = f"{completed}/{total} | Integrity: {score:.1f}% | {datetime.now().strftime('%H:%M')}: Validating..."
        print(f"HARNESS_PROGRESS:{progress}")

    @staticmethod
    def trigger_rollback(book, resume_point):
        event = {
            'operation': 'command',
            'command': f"./goi_controller.sh {book} phase2_translate {resume_point}",
            'reason': 'Semantic integrity below threshold'
        }
        print(f"HARNESS_ROLLBACK:{json.dumps(event)}")


class QualityAssurance:
    def __init__(self, book):
        self.book = book
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.total_verses = self._get_verse_count()
        self.verse_cache = {}
        
    def _get_verse_count(self):
        """Get total verses for book"""
        self.cursor.execute("""
            SELECT COUNT(*) FROM verses WHERE book = ?
        """, (self.book,))
        return self.cursor.fetchone()[0]

    def run(self, resume_point=None):
        """Execute QA validation with resume capability"""
        start_verse = 1
        if resume_point:
            book, chapter, verse = resume_point.split(':')
            self.cursor.execute("""
                SELECT id FROM verses 
                WHERE book = ? AND chapter = ? AND verse = ?
            """, (book, chapter, verse))
            start_verse = self.cursor.fetchone()[0]
            HarnessEvent.log_status(f"{book}:{chapter}:{verse}", 'resuming', 
                                  f'from {resume_point}')

        processed = 0
        total_score = 0
        
        for verse in self._get_verse_data(start_verse):
            verse_id, ref = verse[0], f"{self.book}.{verse[1]}.{verse[2]}"
            
            try:
                # Run all QA checks
                results = self._validate_verse(verse_id)
                
                # Calculate verse score
                verse_score = self._calculate_verse_score(results)
                total_score += verse_score
                
                # Save results
                self._save_validation(verse_id, results, verse_score)
                
                # Update progress
                processed += 1
                avg_score = total_score / processed
                self._save_checkpoint(verse)
                
                HarnessEvent.update_progress(processed, self.total_verses, avg_score)
                HarnessEvent.log_status(ref, 'validated', 
                                      f'Score: {verse_score:.1f}% | Critical: {results["critical"]}')

                # Enforce quality gate
                if avg_score < SEMANTIC_INTEGRITY_MIN and processed >= 10:
                    self._handle_failure(ref, avg_score)
                    
            except Exception as e:
                HarnessEvent.log_status(ref, 'error', str(e))
                raise

        # Final book-level validation
        final_score = total_score / self.total_verses
        HarnessEvent.log_status(f'{self.book}:ALL', 'complete', 
                              f'Final integrity: {final_score:.1f}%')

        if final_score < SEMANTIC_INTEGRITY_MIN:
            self._handle_failure(f'{self.book}:END', final_score)
        
        return final_score

    def _get_verse_data(self, start_id):
        """Fetch verse data with reference numbers"""
        self.cursor.execute("""
            SELECT id, chapter, verse FROM verses 
            WHERE book = ? AND id >= ?
            ORDER BY id
        """, (self.book, start_id))
        return self.cursor.fetchall()

    def _validate_verse(self, verse_id):
        """Run all validation checks for a single verse"""
        return {
            'semantic': self._check_semantic_integrity(verse_id),
            'naturalness': self._check_naturalness(verse_id),
            'consistency': self._check_noun_consistency(verse_id),
            'traceability': self._check_strongs_traceability(verse_id),
            'critical': self._identify_critical_issues(verse_id)
        }

    def _check_semantic_integrity(self, verse_id):
        """Verify core semantic rules"""
        issues = []
        
        # Check 1: Unauthorized articles
        self.cursor.execute("""
            SELECT translation_text FROM translations WHERE verse_id = ?
        """, (verse_id,))
        translation = self.cursor.fetchone()[0]
        
        if re.search(r'\bthe (man|earth|heavens)\b', translation):
            issues.append("Unauthorized 'the' before definite nouns")

        # Check 2: אֶת marker presence
        if ' et ' in translation:
            issues.append("אֶת marker not omitted")

        # Check 3: Verb aspect errors
        if re.search(r'has (created|made|spoken)', translation):
            issues.append("Perfect aspect misuse")

        # Check 4: Construct chain errors
        if re.search(r'king of Israel', translation):
            issues.append("Improper 'of' in construct chain")

        return {
            'issues': issues,
            'score': max(0, 100 - (len(issues) * 15))
        }

    def _check_naturalness(self, verse_id):
        """Validate English readability metrics"""
        self.cursor.execute("""
            SELECT translation_text FROM translations WHERE verse_id = ?
        """, (verse_id,))
        text = self.cursor.fetchone()[0]

        # Flesch-Kincaid grade level
        fk_grade = textstat.flesch_kincaid_grade(text)
        
        # Preposition density
        total_words = textstat.lexicon_count(text, removepunct=True)
        prepositions = text.count(' of ') + text.count(' in ') + text.count(' to ')
        prep_density = (prepositions / total_words) * 100 if total_words else 0

        # Passive voice check
        passives = sum(1 for verb in ['be', 'is', 'are', 'was', 'were'] 
                      if f' {verb} ' in text.lower())
        passive_rate = (passives / total_words) * 100 if total_words else 0

        # Scoring (target: FK 8-10, prep <15%, passive <5%)
        fk_score = 100 if 8 <= fk_grade <= 10 else max(0, 100 - abs(fk_grade - 9) * 15)
        prep_score = 100 if prep_density < 15 else max(0, 100 - (prep_density - 15) * 8)
        passive_score = 100 if passive_rate < 5 else max(0, 100 - (passive_rate - 5) * 12)
        
        return {
            'metrics': {
                'fk_grade': round(fk_grade, 1),
                'prep_density': round(prep_density, 1),
                'passive_rate': round(passive_rate, 1)
            },
            'score': (fk_score + prep_score + passive_score) / 3
        }

    def _check_noun_consistency(self, verse_id):
        """Verify top 200 noun translations"""
        issues = []
        
        # Get all nouns in verse
        self.cursor.execute("""
            SELECT lexemes.strongs_id, lexemes.freq_rank, translations.translation_text
            FROM verse_lexemes
            JOIN lexemes ON verse_lexemes.strongs_id = lexemes.strongs_id
            JOIN translations ON translations.verse_id = verse_lexemes.verse_id
            WHERE verse_lexemes.verse_id = ?
            AND lexemes.freq_rank <= 200
        """, (verse_id,))
        
        for strongs_id, freq_rank, translation in self.cursor.fetchall():
            # Get standard translation for this noun
            self.cursor.execute("""
                SELECT base_translation FROM lexemes WHERE strongs_id = ?
            """, (strongs_id,))
            standard = self.cursor.fetchone()[0]

            # Check if used consistently
            if standard not in translation:
                issues.append(f"Inconsistent noun: {strongs_id} ({standard} expected)")

        return {
            'issues': issues,
            'score': max(0, 100 - (len(issues) * 25))
        }

    def _check_strongs_traceability(self, verse_id):
        """Verify Strong's number mapping"""
        issues = []
        
        # Get all lexemes
        self.cursor.execute("""
            SELECT strongs_id FROM verse_lexemes WHERE verse_id = ?
        """, (verse_id,))
        
        for (strongs_id,) in self.cursor.fetchall():
            # Verify Strong's number exists
            self.cursor.execute("""
                SELECT COUNT(*) FROM lexemes WHERE strongs_id = ?
            """, (strongs_id,))
            if self.cursor.fetchone()[0] == 0:
                issues.append(f"Missing Strong's mapping: {strongs_id}")

        return {
            'issues': issues,
            'score': max(0, 100 - (len(issues) * 20))
        }

    def _identify_critical_issues(self, verse_id):
        """Flag critical issues requiring immediate attention"""
        critical = []
        results = self._validate_verse(verse_id)

        # Critical semantic issues
        if 'אֶת marker not omitted' in results['semantic']['issues']:
            critical.append('ET_MARKER')
        if 'Perfect aspect misuse' in results['semantic']['issues']:
            critical.append('VERB_ASPECT')

        # Critical consistency issues
        if results['consistency']['score'] < 75:
            critical.append('NOUN_INCONSISTENCY')

        return critical

    def _calculate_verse_score(self, results):
        """Weighted score calculation"""
        weights = {
            'semantic': 0.45,
            'naturalness': 0.25,
            'consistency': 0.20,
            'traceability': 0.10
        }
        
        return sum(results[k]['score'] * weights[k] for k in weights)

    def _save_validation(self, verse_id, results, score):
        """Save validation results to DB"""
        self.cursor.execute("""
            INSERT OR REPLACE INTO qa_results 
            (verse_id, semantic_score, naturalness_score, 
             consistency_score, traceability_score, total_score,
             critical_issues, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            verse_id,
            results['semantic']['score'],
            results['naturalness']['score'],
            results['consistency']['score'],
            results['traceability']['score'],
            score,
            json.dumps(results['critical']),
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def _save_checkpoint(self, verse):
        """Save resume point"""
        with open(CHECKPOINT_FILE, 'w') as f:
            f.write(f"resume={self.book}:{verse[1]}:{verse[2]}")

    def _handle_failure(self, ref, score):
        """Trigger rollback on quality gate failure"""
        HarnessEvent.log_status(ref, 'failure', 
                              f'Semantic integrity {score:.1f}% < {SEMANTIC_INTEGRITY_MIN}%')
        
        # Generate error report
        error_report = {
            'book': self.book,
            'failed_at': ref,
            'integrity_score': score,
            'threshold': SEMANTIC_INTEGRITY_MIN,
            'resume_point': self._get_resume_point()
        }

        # Trigger harness rollback
        HarnessEvent.trigger_rollback(
            self.book,
            error_report['resume_point']
        )
        
        # Generate security report
        self._generate_security_report(error_report)
        
        raise RuntimeError(f"QA FAILURE: Semantic integrity {score:.1f}% < {SEMANTIC_INTEGRITY_MIN}%")

    def _get_resume_point(self):
        """Get last successful verse for resume"""
        self.cursor.execute("""
            SELECT book, chapter, verse 
            FROM verses 
            WHERE id = (
                SELECT MAX(verse_id) FROM qa_results
                WHERE total_score >= 95
            )
        """)
        book, chapter, verse = self.cursor.fetchone()
        return f"{book}:{chapter}:{verse}"

    def _generate_security_report(self, error):
        """Create security report for harness"""
        findings = [
            f"- [critical] Semantic integrity {error['integrity_score']:.1f}% < threshold ({error['threshold']}%)",
            f"- [high] Failed at reference: {error['failed_at']}"
        ]
        
        report = {
            'title': 'GOI Translation QA Failure',
            'summary': f'Semantic integrity below threshold in {error['book']}',
            'findings_markdown': '\n'.join(findings),
            'mitigations': '1. Run phase2_translate with resume point\n2. Focus on critical issues: ET_MARKER, VERB_ASPECT',
            'scope': 'Translation quality gate enforcement'
        }
        
        # Output for harness consumption
        print(f"SECURITY_REPORT:{json.dumps(report)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--book', required=True, help='Book name (e.g., Genesis)')
    parser.add_argument('--resume', help='Resume point (e.g., Genesis:1:5)')
    args = parser.parse_args()

    qa = QualityAssurance(args.book)
    
    resume_point = None
    if args.resume:
        book, chapter, verse = args.resume.split(':')
        resume_point = (book, int(chapter), int(verse))

    try:
        score = qa.run(resume_point=resume_point)
        print(f"\n✅ QA PASSED: Semantic integrity {score:.1f}% ≥ {SEMANTIC_INTEGRITY_MIN}%")
        print("Next: Run 'show_report --phase=completion'")
    except RuntimeError as e:
        print(f"\n❌ QA FAILED: {str(e)}")
        print("Auto-rollback command generated - check HARNESS_ROLLBACK events")