Master Design Specification: "Zen Focus" Theme

1. Core Philosophy

Vibe: Calm, organic, mindful, non-judgmental, and human-centric.
Goal: To lower the user's anxiety during the interview process. The interface should feel like a breathing exercise, not a test.

2. Color Palette (Tailwind / CSS Variables)

Use these exact hex codes to maintain consistency.

Role

Name

Hex Code

Usage

Background

Cream BG

#FDFBF7

Main page background (Warm, paper-like).

Primary

Sage Dark

#8BAF8B

Primary buttons, active icons, accents.

Secondary

Sage Light

#E8F3E8

Background blobs, subtle highlights.

Accent

Sage Medium

#CDE0CD

Borders, secondary elements.

Text Main

Slate Text

#2C3E50

Headings, main body text.

Text Muted

Gray Muted

#9CA3AF

Placeholders, help text.

Error

Soft Red

#E57373

Error messages (keep soft, not harsh).

3. Typography

Headings: Merriweather (Google Font)

Weights: 300 (Light), 400 (Regular), 700 (Bold).

Style: Italic usage is encouraged for emphasis (e.g., "Speak with confidence").

Usage: All h1, h2, h3 tags.

Body: Inter (Google Font)

Weights: 300, 400, 500.

Usage: Paragraphs, inputs, buttons, UI labels.

4. UI Component Library

A. Buttons

Shape: Fully rounded "Pill" shape (border-radius: 9999px).

Primary Button: Background #8BAF8B, Text White.

Hover: Slight lift (transform: translateY(-2px)) and increased shadow.

Secondary/Outline Button: Transparent background, Border 1px solid #8BAF8B, Text #8BAF8B.

B. Cards & Containers

Background: White (#FFFFFF).

Border Radius: Very soft and large (rounded-2xl or rounded-3xl).

Shadows: Ultra-soft, diffused shadows. Avoid sharp dark shadows.

CSS: box-shadow: 0 20px 40px -15px rgba(0,0,0,0.05);

C. Inputs

Style: Minimalist "Underline" style. No boxes.

Normal: Transparent background, border-bottom: 1px solid #CBD5E0.

Focus: border-bottom: 1px solid #8BAF8B, outline: none.

D. Navigation

Position: Fixed Top.

Progress Indicators: Use subtle dots. Active dot is dark slate, inactive dots are light gray.

5. Animation Guidelines

The interface must feel "alive" but slow.

"Breathe" Effect: For avatars or waiting states.

Scale up to 1.05x and opacity drop to 0.8 over 6 seconds.

"Float" Effect: For background blobs.

Slow vertical movement (translateY) over 10-12 seconds.

Page Transitions: Slow fades (1.0s - 1.2s). Avoid jarring slides.

6. HTML Structure & Classes (Tailwind)

Wrapper: <section class="min-h-screen bg-[#FDFBF7] text-[#2C3E50] font-sans">

Heading: <h1 class="font-serif text-4xl text-gray-800">

Primary Button: <button class="bg-[#8BAF8B] text-white rounded-full px-8 py-3 shadow-sm hover:shadow-lg transition-all transform hover:-translate-y-1">