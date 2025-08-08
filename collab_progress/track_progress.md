---
applyTo: '**'
---

# Progress Tracking Protocol

## Purpose
To ensure all code changes are transparently tracked and reviewable, every implementation or refactor must be accompanied by a progress note in the collab_progress folder.

## Workflow

1. **After Each Change:**
   - Upon completing any significant code change (feature, bugfix, refactor, or test), create a new Markdown file in collab_progress.
   - Name the file descriptively, including the date:  
     `short-description-DD-MM-YYYY.md`  

2. **Progress Note Format:**
   - Each note should be concise and include:
     - **Summary:** What was done and why.
     - **Files Changed:** List of files or modules affected.
     - **Rationale:** Brief reasoning for the change.
     - **Verification:** How the change was tested or validated.
     - **Issues:** Any known issues or limitations.
     - **Next Steps:** Any follow-up actions or open questions.

3. **Deltas, Not Duplicates:**
   - Focus on what changed since the last note, not a restatement of the entire context.

4. **Review & Collaboration:**
   - These notes serve as a shared log for both AI and human collaborators to review, discuss, and plan next actions.
