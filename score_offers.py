import os
import csv
import openai
import re
from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# Load .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

# Function to generate match score and reason using OpenAI
def assess_job_offer(cv_text, job_data):
    prompt = (
        f"You are a job matching assistant. Perform the following steps carefully and output the results in the specified format:\n\n"
        f"1. From the job offer below, extract:\n"
        f"   a. All must-have skills and experiences, clearly listed as required in the description. This includes specific skills, technologies, certifications, and experience levels.\n"
        f"   b. All nice-to-have skills and experiences, clearly listed as optional, preferred, or additional qualifications.\n"
        f"   c. Add the Role Name and each Technology Area as must-have criteria.\n\n"
        f"2. Count how many must-have (R) and nice-to-have (O) criteria you extracted.\n\n"
        f"3. Analyze the following CV. For each criterion:\n"
        f"   - If the CV contains an exact or close match for the criterion, mark it as matched.\n"
        f"   - Count how many must-have and nice-to-have criteria the CV matches. Call these MR and MO.\n\n"
        f"4. Calculate a score out of 100 using a weighted formula:\n"
        f"   - Each must-have match contributes 'a' points.\n"
        f"   - Each nice-to-have match contributes 'b' points.\n"
        f"   - The weights should satisfy this equation: 100 = R * a + O * b, where a > b.\n"
        f"   - Distribute the weight linearly based on the number of matches.\n"
        f"   - If no criteria are matched, the score is 0. If all criteria are matched, the score is 100.\n\n"
        f"5. Provide the output in the following format:\n"
        f"Score: <integer between 1 and 100>\n"
        f"Reason: <a short explanation, ~100 words, explaining how the score was calculated, including how many criteria were matched and highlighting the most relevant matches.>\n\n"
        f"Job Offer:\n"
        f"Role Name: {job_data['RoleName']}\n"
        f"Technology Area(s): {job_data['Technology Area']}\n"
        f"Description:\n{job_data['Full Description']}\n\n"
        f"CV:\n{cv_text}"
    )
    try:
        response = openai.chat.completions.create(
            model=openai_model,
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content

        # Parse the response
        #score_line = next((line for line in answer.splitlines() if "Score:" in line), "Score: 0")
        #reason_line = next((line for line in answer.splitlines() if "Reason:" in line), "Reason: Not provided.")

        #score = int("".join(filter(str.isdigit, score_line)))
        #reason = reason_line.replace("Reason:", "").strip()

        # return min(max(score, 1), 100), reason

        # Extract score line
        score_line = next((line for line in answer.splitlines() if "Score:" in line), None)
        reason_line = next((line for line in answer.splitlines() if "Reason:" in line), "Reason: Not provided.")

        if score_line:
            try:
                # Search for an integer after "Score:"
                match = re.search(r"Score:\s*(\d+)", score_line)
                if match:
                    score = int(match.group(1))
                else:
                    score = 0
            except ValueError:
                score = 0
        else:
            score = 0

        # Clean up reason
        reason = reason_line.replace("Reason:", "").strip()

        return min(max(score, 1), 100), reason

    except Exception as e:
        print(f"⚠️ API error: {e}")
        return 0, "Error in API call."

# === Main Logic ===

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Score job offers against a candidate CV using OpenAI.")
    parser.add_argument("--input", required=True, help="Path to input CSV file from the scraper")
    parser.add_argument("--cv", required=True, help="Path to the CV text file")
    parser.add_argument("--output", default="scored_job_offers.csv", help="Output CSV file")
    parser.add_argument("--separator", default=",", help="CSV separator (default is ',')")

    args = parser.parse_args()

    # Read CV
    with open(args.cv, "r", encoding="utf-8") as cv_file:
        cv_text = cv_file.read()

    # Read job offers CSV
    print(f"📂 Reading input CSV '{args.input}' using separator '{args.separator}'")
    df = pd.read_csv(args.input, sep=args.separator)

    # Prepare result columns
    match_scores = []
    match_reasons = []

    print(f"🔍 Scoring {len(df)} job offers using model '{openai_model}'...\n")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Scoring offers", unit="offer"):
        score, reason = assess_job_offer(cv_text, row)
        match_scores.append(score)
        match_reasons.append(reason)

    # Add results to DataFrame
    df["Match Score (%)"] = match_scores
    df["Match Reason"] = match_reasons

    # Save to CSV with the same separator
    df.to_csv(args.output, index=False, sep=args.separator)
    print(f"\n✅ Saved scored results to '{args.output}'")


if __name__ == "__main__":
    main()
