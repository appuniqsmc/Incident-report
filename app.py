def generate_ai_rca(text, domains):

    prompt = f"""
You are a senior ICU quality improvement consultant.

Perform a detailed, structured, institutional-grade Root Cause Analysis.

Incident Description:
{text}

Detected Contributing Domains:
{domains}

Generate a comprehensive RCA report with the following sections:

1. Event Summary
   - What happened
   - Clinical significance

2. Immediate Causes (Active Failures)
   - Direct human or process errors

3. Contributing Factors (By Domain)
   For each domain listed, provide:
   - Specific mechanisms involved
   - How it contributed

4. Latent System-Level Causes
   - Organizational weaknesses
   - System design flaws
   - Safety barrier gaps

5. Risk Assessment
   - Potential recurrence likelihood
   - Patient harm severity implications

6. Corrective Actions (Short-Term)
   - Immediate containment steps

7. Preventive Strategies (Long-Term)
   - Policy
   - Training
   - Monitoring
   - Audit mechanisms

8. Suggested Driver Diagram Mapping
   - Aim
   - Primary drivers
   - Secondary drivers
   - Example change ideas

Write in professional healthcare quality language.
Be analytical and structured.
Avoid generic statements.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a hospital quality and patient safety expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI generation failed: {str(e)}"
