import requests
from bs4 import BeautifulSoup
import csv
import argparse
import time
from tqdm import tqdm

def fetch_offer_description(url):
    """Fetch and parse the description of a single job offer page."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract paragraphs and lists
        description_parts = []
        for tag in soup.find_all(["p", "ul", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            if text:
                description_parts.append(text)

        return "\n".join(description_parts)

    except Exception as e:
        print(f"⚠️ Error fetching description from {url}: {e}")
        return ""

def fetch_and_parse_job_offers(category, location, workplace, keyword, role):
    """Fetch the job listing page and parse the list of offers."""
    base_url = "https://justjoin.it/job-offers"

    # Build the path based on whether category is provided
    if category:
        url = f"{base_url}/{location}/{category}"
    else:
        url = f"{base_url}/{location}"

    # Add optional query params
    params = {}
    if workplace:
        params["workplace"] = workplace
    if keyword:
        params["keyword"] = keyword
    if role:
        params["titles"] = role

    response = requests.get(url, params=params)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    offer_cards = soup.find_all("a", class_="offer-card")

    print(f"ℹ️ Found {len(offer_cards)} job offers. Fetching full descriptions...\n")

    job_offers = []
    for card in tqdm(offer_cards, desc="Fetching offers", unit="offer"):
        # Role Name
        role_name_tag = card.find("h3")
        role_name = role_name_tag.text.strip() if role_name_tag else ""

        # Company Name
        company = ""
        company_icon = card.find("svg", {"data-testid": "ApartmentRoundedIcon"})
        if company_icon:
            parent_div = company_icon.find_parent("div", class_="MuiBox-root")
            if parent_div:
                company_span = parent_div.find("span")
                company = company_span.text.strip() if company_span else ""

        # Technology Areas
        tech_area_list = []
        tech_area_container = card.find("div", class_="MuiBox-root mui-4o5qaq")
        if tech_area_container:
            for skill_div in tech_area_container.find_all("div", class_=lambda c: c and c.startswith("skill-tag-")):
                skill_text = skill_div.get_text(strip=True)
                if skill_text:
                    tech_area_list.append(skill_text)
        tech_area = ", ".join(tech_area_list)

        # Salary
        salary_div = card.find("div", class_="MuiBox-root mui-18ypp16")
        if salary_div:
            undisclosed = salary_div.find("div")
            if undisclosed:
                salary = undisclosed.text.strip()
            else:
                salary_parts = [part.get_text(strip=True) for part in salary_div.find_all(["span", "div"])]
                salary = " ".join(salary_parts)
        else:
            salary = ""

        # Offer link
        link = "https://justjoin.it" + card.get("href", "")
        short_description = link.split("/")[-1].replace("-", " ").title()

        # Full Description
        full_description = fetch_offer_description(link)

        time.sleep(1)  # Be polite to the server

        # Add offer to results
        job_offers.append({
            "RoleName": role_name,
            "Link to offer Page": link,
            "Company Name": company,
            "Technology Area": tech_area,
            "Salary": salary,
            "Short Description": short_description,
            "Full Description": full_description,
            "Offer End Date": ""
        })

    return job_offers

def main():
    parser = argparse.ArgumentParser(description="Scrape job offers from JustJoin.it")
    parser.add_argument("--category", type=str, default="", help="Job category (e.g., pm, backend, frontend)")
    parser.add_argument("--location", type=str, default="all-locations", help="Job location (e.g., warszawa, remote)")
    parser.add_argument("--workplace", type=str, default="", help="type of office policy (e.g.office, hybrid - optional)")
    parser.add_argument("--keyword", type=str, default="", help="Keyword to search (optional)")
    parser.add_argument("--role", type=str, default="", help="job role to search for (optional)")
    args = parser.parse_args()

    print(f"🔍 Searching for jobs in category '{args.category}' at location '{args.location}' in modality '{args.workplace}' with keyword '{args.keyword}' and job role '{args.role}'\n")

    offers = fetch_and_parse_job_offers(args.category, args.location, args.workplace, args.keyword, args.role)

    # Save to CSV
    csv_file = f"job_offers_{args.category}_{args.location}_{args.workplace}_{args.keyword}_{args.role}.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=offers[0].keys())
        writer.writeheader()
        writer.writerows(offers)

    print(f"\n✅ Saved {len(offers)} offers to '{csv_file}'")

if __name__ == "__main__":
    main()
