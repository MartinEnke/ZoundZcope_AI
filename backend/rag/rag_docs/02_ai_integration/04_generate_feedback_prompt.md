# AI Feedback Prompt Generation (gpt_utils.py)

This module defines constants, templates, and the main function for dynamically assembling
a detailed AI prompt used to generate tailored mixing and mastering feedback for audio tracks.

---

## Key Components

### Reference Track Instruction

- A strict directive to the AI to compare the submitted track’s analysis with reference track data if available.  
- Prevents the AI from mentioning a reference track when no reference data exists.

### Role Contexts

- Defines the AI persona based on feedback type:  
  - **mixdown engineer** for mix feedback  
  - **mastering engineer** for mastering advice or master review  
- Context is customized per genre and subgenre for precise, genre-aware feedback.

### Profile Guidance

- Controls the tone and technical complexity of the AI’s language:  
  - *Simple*: Friendly, non-technical explanations for beginners  
  - *Detailed*: Moderate technicality suitable for intermediate producers  
  - *Pro*: Advanced jargon and precise terminology for experts

### Format Rules

- Specifies the bullet-point structure the AI must follow in its feedback, customized per profile.  
- Ensures consistent, clear formatting with ISSUE and IMPROVEMENT parts.

### Example Outputs

- Sample bullet points for each profile to guide AI response style and content.

---

## Main Function: `generate_feedback_prompt`

This function constructs the final prompt string sent to the AI model by combining:

- The role context (engineer persona) tailored by feedback type and genre.  
- The communication style based on the selected profile.  
- Audio analysis data from the submitted track (peak, LUFS, transient info, dynamic range, etc.).  
- Optional reference track analysis to provide comparative feedback.  
- Formatting instructions and examples to guide the AI’s output.  
- A reasoning step encouraging the AI to reflect on analysis data before generating bullet points.

---

### Function Behavior

- Validates input parameters against allowed genres, subgenres, feedback types, and profiles.  
- Escapes HTML characters in genre and subgenre for safe inclusion in prompts.  
- Includes warnings if peak level issues exist in the analysis data.  
- Returns a fully assembled prompt string adhering to the predefined style and format rules.

---

### Usage

This prompt generation function is central to your AI feedback system, ensuring that the
language model receives detailed, context-aware instructions for generating actionable,
clear, and style-appropriate mixing and mastering advice tailored to the user’s input.

---

*The full source code for this function, including constants and templates, is stored separately for exact retrieval.*
