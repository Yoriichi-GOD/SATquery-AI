# Scene description investigation — 20 September 2026

User reported incomplete whole-scene coverage on the baseball example.

Baseline run 69d2c4d647de4cf38ac5c36af465c973: question and effective prompt were `Describe this image.` Routing was single_image_description. Raw answer was `There are four baseball fields arranged in a square.` The open-visual-v1 presentation preserved it. This was not erroneous count routing or UI truncation.

Trial a32806789418499283b753f124e0434f: appended whole-scene instructions and allowed 192 output tokens. Result mentioned structures and paved areas but speculated about dugouts, locker rooms, administrative buildings and season/urbanization. Rejected.

Trial 4fffb04f192a40eab916d5fcf33a8bb1: explicit region-by-region question. Model invented a larger central field and inferred school/community use; output reached the token limit. Rejected.

Prompt experiment removed. No claim that comprehensive description is fixed. Exact identities/counts of small roofs, pavilions, houses or parking features were not validated. Further visual-coverage improvements require a reference-labelled scene set and evaluation of omissions and invented details, keeping count/presence behavior unchanged.

Evidence page separately fixed: full-height illustration is outside the data scroll container. Browser screenshots before and after scrolling confirmed unchanged illustration placement while tables moved. Regression suite: 50 tests passed during investigation; final server prompt returned to the prior tested version.


## Follow-up: equivalent wording normalized
Controlled same-process replay reproduced the short/long response change using the same two images and different phrasings. Added scene_description.py to recognize whole-scene requests only. These now use `Describe this image in detail.` and a 192-token ceiling. Original question, effective prompt and description_policy remain in saved main-run evidence. Counting, yes/no, subject-specific, compound and explicitly brief queries do not receive this normalization.

Verification: 52 unit/regression tests passed. Four final real runs (two equivalent questions on car and baseball images) completed below the output limit and produced identical raw answers within each image pair. Raw replay records are in paired_lab/evidence/description-20260920.

This fixes wording-dependent brevity, not scientific description accuracy. Final car output includes visible colour/hillside/sky/mountains but also a wrong side-angle claim and a questionable spoiler description. Baseball output includes surrounding grass/buildings/trees but speculates about community/school use. Full model interpretations remain labelled and preserved; none of these inferred details is certified as ground truth. The two images were used to select the prompt and are development checks, not independent accuracy evaluation.
