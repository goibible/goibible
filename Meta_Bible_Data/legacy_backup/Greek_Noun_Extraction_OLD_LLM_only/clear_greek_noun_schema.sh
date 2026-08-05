#!/bin/bash
sqlite3 greek_noun.sqlite3 "
DELETE FROM verse_noun_occurrences;
DELETE FROM noun_translations;
DELETE FROM nouns;
"
