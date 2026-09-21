# Target architecture
~~~mermaid
flowchart TD
 Q["Natural-language query"] --> C["Intent/input controller: PLANNED"]
 C --> R["Permitted tool registry: PLANNED"]
 R --> V["VQA: IMPLEMENTED; LoRA EXPERIMENTAL"]
 R --> N["NDVI: IMPLEMENTED"]
 R --> G["Grounding: PLANNED"]
 R --> T["Temporal: PLANNED"]
 R --> S["Optical-SAR: PLANNED"]
 V --> E["Unified evidence/provenance: PARTIAL"]
 N --> E
 G --> E
 T --> E
 S --> E
 E --> U["GUI: IMPLEMENTED; stage viewer PLANNED"]
~~~
No calibrated confidence score exists. Proposed controller validates modalities, dates, alignment and allowed parameters; refuses unsupported workflows.
