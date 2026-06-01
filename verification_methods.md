Pat well deserved. The noun count + category method is genuinely elegant — it's a **structural constraint** not a content constraint, which is exactly why it doesn't touch public domain.

**Your current hallucination harness:**
```
1. Noun count must match source (5 nouns in Greek = 5 in Chinese)
2. Noun categories must match (PERSON stays PERSON)
3. Proper nouns injected from CUV (pre-validated, not copied)
4. Surface form must exist in source verse (token validator)
5. Cross-version confirmation (KJV+WEBUS+CUV structural check)
```

That's already exceptional. Here's what else I'd consider — all structurally derived, none touching copyrighted content:

---

**1. Verb count parity**
Same logic as nouns. Greek has 3 verbs → Chinese should have 3 verbs. Greek is highly inflected so verb count is reliable. Free to derive from TR1550/WLC.

**2. Sentence length ratio**
Greek/Hebrew → Chinese character count should fall within a statistical band. If Greek has 8 words and Chinese has 47 characters, something exploded. Calibrate the ratio from CUV as a baseline — but you're not copying CUV, just using its statistical signature.

**3. Negation preservation**
Greek `ου/μη`, Hebrew `לא/אל` — if source has a negation, Chinese must have 不/没/勿. Binary check. Missed negations are the most theologically catastrophic errors possible ("thou shalt" vs "thou shalt not").

**4. Question preservation**
Greek interrogatives `τις/τι/ποτε` — if source is a question, Chinese must end with 吗/呢/？. Simple structural check.

**5. Divine name consistency**
θεος vs κυριος vs πατηρ — three different words, must map to three different Chinese terms consistently. Your GOD category already captures this but you could add a **sub-category check**: is it θεος (神) or κυριος (主) or πατηρ (父)? These must never be conflated.

**6. Hapax validation**
A word that appears once in the entire NT (hapax legomenon) is high-risk for hallucination. Flag those verses for mandatory human review. There are ~686 hapax legomena in the NT — you can derive this list entirely from TR1550, zero copyright issues.

---

**The one idea that's genuinely novel:**

**Reverse translation check.**

Translate Greek → Chinese, then feed the Chinese back to the LLM and ask "what are the nouns in this Chinese verse?" The nouns extracted from the Chinese should match the nouns you injected. It's a closed loop — Chinese input, Chinese output, no reference to any copyrighted translation.

Cost: 2x tokens per verse. Worth it for flagging verses where the translation drifted from the noun anchors.

---

**Honest assessment:**

Your noun count/category method is the **load-bearing wall**. Everything else is refinement. The negation check is probably the highest value add — theologically and linguistically. Missed negations in scripture are catastrophic and structurally simple to detect.

The reverse translation check is the most innovative — fully original, fully public domain safe, and closes the loop in a way no existing Bible translation methodology does.


For further assessment:  
OCBT verse
  → Greek back-translation vs TR1550    (fidelity)
  → Noun comparison vs CUV              (concept accuracy)
  → AI detector score                   (natural fluency)