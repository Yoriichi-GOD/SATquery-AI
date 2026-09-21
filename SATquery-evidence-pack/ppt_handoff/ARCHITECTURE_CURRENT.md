# Current architecture
~~~mermaid
flowchart TD
 U["User/local browser: implemented"] --> F["UI explicit mode: implemented"]
 F --> A["FastAPI upload/job API: implemented"]
 A --> V["Pinned RS VQA: implemented"]
 V --> L["Optional LoRA: experimental"]
 A --> N["CPU NDVI: implemented"]
 N --> O["Mask/grid area/exports: implemented"]
 V --> R["Answer/run record: implemented"]
 L --> R
 O --> UI["Evidence UI: implemented"]
 R --> UI
~~~
One shared serial worker; process-local indexes. Explicit selection, not automatic agentic orchestration. Refusal patterns incomplete.
