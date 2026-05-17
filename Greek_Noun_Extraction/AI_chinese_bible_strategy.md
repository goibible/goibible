# GOAL - MIT Licensed Chinese Bible

Summary:  I want to create an open, "MIT" licensed Chinese (Mandarin) [Traditional and Simplified] Bible.

Old Testament will be taken from the WLC public domain Hebrew
New Testament will be taken from the TR1550 public domain Greek

Strategy:

1. I have shattered the bible into 31102 Bible verses; as flat files.  So we won't be dealing with more than 1 verse at a time.  We are going to go straight from Hebrew to Chinese; and Greek to Chinese.
2. Hallucination Prevention; we will use multiple methods:
	1. We are going to near word for word interpretation and one verse at a time so the inference engine has no chance to hallucinate.
	2. We are going to take the Greek and the Hebrew; and do a noun count:
		1. We are going to categorize the nouns into four categories:
			1. Names of God
			2. Names of People
			3. Names of Places
			4. Other Nouns
	5. We will go ahead and take a database count of all the nouns; and then we will make consistent and sure in a dictionary compilation, that every time that noun appears; will be translated the same.
	6. We will also do a noun count; if there are 5 nouns in that verse in Hebrew or Greek; there'd better be 5 nouns in the Chinese translation.
	7. Familial Matching:  We will take the Chinese CUV version; and whenever there is a proper noun for name of God, Person or Place, we will take the CUV version of that since then a reader will be familiar with that noun, and taking proper nouns does not effect its licensing.  (i.e. if you use the CUV's version of the name Moses, you can't say that's copying a text.)
	
