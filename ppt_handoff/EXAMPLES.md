# Real development examples

These are cherry-picked explanatory examples, not an unbiased evaluation. “Correct” means agreement with published reference labels, not independent visual truth.
## Q4889 — semantic-label gain

![Image 48](examples/image-48.png)

Question: Are there less roads than residential buildings?

Reference: yes

Original: No

Adapter: yes

Original and adapter both use valid labels; adapter now matches the published label. This is not merely formatting.

## Q1210 — semantic-label gain

![Image 12](examples/image-12.png)

Question: Is a commercial building present?

Reference: yes

Original: No

Adapter: yes

Original and adapter both use valid labels; adapter now matches the published label. This is not merely formatting.

## Q4440 — semantic-label gain

![Image 44](examples/image-44.png)

Question: Are there less farmlands than buildings?

Reference: yes

Original: No

Adapter: yes

Original and adapter both use valid labels; adapter now matches the published label. This is not merely formatting.

## Q2522 — semantic-label gain

![Image 25](examples/image-25.png)

Question: Is there a forest?

Reference: yes

Original: No

Adapter: yes

Original and adapter both use valid labels; adapter now matches the published label. This is not merely formatting.

## Q1495 — semantic-label gain

![Image 14](examples/image-14.png)

Question: Is there a wetland?

Reference: yes

Original: No

Adapter: yes

Original and adapter both use valid labels; adapter now matches the published label. This is not merely formatting.

## Q5440 — regression

![Image 54](examples/image-54.png)

Question: Is there a circular road?

Reference: no

Original: No

Adapter: yes

Original matches the reference; adapter changes to the wrong label.

## Q1936 — regression

![Image 19](examples/image-19.png)

Question: Is there a rectangular grass area?

Reference: no

Original: No

Adapter: yes

Original matches the reference; adapter changes to the wrong label.

## Q1400 — format-confounded gain

![Image 14](examples/image-14.png)

Question: Is it a rural or an urban area

Reference: rural

Original: The image depicts a rural area. This is evident from the presence of large,

Adapter: rural

Original violates the exact-label protocol. Inspect its wording before attributing this to semantic improvement.

## Q1200 — format-confounded gain

![Image 12](examples/image-12.png)

Question: Is it a rural or an urban area

Reference: urban

Original: The area depicted in the image is a rural setting. This is indicated by the

Adapter: urban

Original violates the exact-label protocol. Inspect its wording before attributing this to semantic improvement.

