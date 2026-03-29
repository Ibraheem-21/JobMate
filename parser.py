import re


ROLE_HINTS = [
    "engineer",
    "developer",
    "analyst",
    "scientist",
    "designer",
    "manager",
    "specialist",
    "coordinator",
    "associate",
    "consultant",
    "intern",
    "administrator",
    "recruiter",
    "product manager",
    "data",
    "software",
    "marketing",
    "sales",
]

SKILL_PATTERNS = [
    "Python",
    "SQL",
    "Excel",
    "Tableau",
    "Power BI",
    "JavaScript",
    "TypeScript",
    "React",
    "Node",
    "AWS",
    "Azure",
    "GCP",
    "Java",
    "C++",
    "C#",
    "Figma",
    "Product Management",
    "Project Management",
    "Machine Learning",
    "Data Analysis",
    "Git",
    "Docker",
    "Kubernetes",
    "Salesforce",
    "HubSpot",
    "Communication",
    "Leadership",
]


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" -|:\t"))


def _first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _clean(match.group(1))
    return ""


def _extract_url(text: str) -> str:
    match = re.search(r"https?://[^\s)>\]]+", text)
    return match.group(0) if match else ""


def _extract_salary(text: str) -> str:
    patterns = [
        r"(\$\s?\d[\d,]*(?:\.\d+)?\s*(?:-|to)\s*\$?\s?\d[\d,]*(?:\.\d+)?\s*(?:per year|yearly|annually|/year|/yr)?)",
        r"(\$\s?\d[\d,]*(?:\.\d+)?\s*(?:per year|yearly|annually|/year|/yr))",
        r"(\$\s?\d[\d,]*(?:\.\d+)?\s*(?:-|to)\s*\$?\s?\d[\d,]*(?:\.\d+)?\s*(?:per hour|hourly|/hour|/hr)?)",
        r"(\$\s?\d[\d,]*(?:\.\d+)?\s*(?:per hour|hourly|/hour|/hr))",
        r"(salary\s*[:\-]\s*[^\n]+)",
        r"(compensation\s*[:\-]\s*[^\n]+)",
        r"(pay range\s*[:\-]\s*[^\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean(match.group(1))
    return ""


def _extract_location(text: str, lines: list[str]) -> str:
    labeled = _first_match(
        [
            r"(?:location|work location|office location)\s*[:\-]\s*([^\n]+)",
            r"(?:based in)\s+([^\n.]+)",
        ],
        text,
    )
    if labeled:
        return labeled

    remote_match = re.search(r"\b(remote|hybrid|on-site|onsite)\b", text, flags=re.IGNORECASE)
    for line in lines[:12]:
        normalized = line.lower()
        if "," in line and len(line) < 60:
            return _clean(line)
        if remote_match and any(word in normalized for word in ["remote", "hybrid", "on-site", "onsite"]):
            return _clean(line)
    return remote_match.group(1).title() if remote_match else ""


def _extract_title(text: str, lines: list[str]) -> str:
    labeled = _first_match(
        [
            r"(?:job title|title|position|role)\s*[:\-]\s*([^\n]+)",
            r"we are hiring a[n]?\s+([^\n.]+)",
            r"we are looking for a[n]?\s+([^\n.]+)",
        ],
        text,
    )
    if labeled:
        return labeled

    for line in lines[:8]:
        line_lower = line.lower()
        if len(line) > 90:
            continue
        if any(hint in line_lower for hint in ROLE_HINTS):
            return _clean(line)
    return _clean(lines[0])[:80] if lines else ""


def _extract_company(text: str, lines: list[str], title: str) -> str:
    labeled = _first_match(
        [
            r"(?:company|organization|employer)\s*[:\-]\s*([^\n]+)",
            r"about\s+([A-Z][A-Za-z0-9&.,' -]{1,60})",
            r"join\s+([A-Z][A-Za-z0-9&.,' -]{1,60})",
            r"at\s+([A-Z][A-Za-z0-9&.,' -]{1,60})",
        ],
        text,
    )
    if labeled and labeled.lower() != title.lower():
        return labeled

    if len(lines) > 1 and len(lines[1]) < 60 and lines[1].lower() != title.lower():
        return _clean(lines[1])
    return ""


def _extract_skills(text: str) -> str:
    hits: list[str] = []
    for skill in SKILL_PATTERNS:
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(skill)
    return ", ".join(dict.fromkeys(hits))


def extract_job_details(job_description: str) -> dict[str, str]:
    lines = [_clean(line) for line in job_description.splitlines() if _clean(line)]
    text = job_description.strip()

    title = _extract_title(text, lines)
    company = _extract_company(text, lines, title)
    location = _extract_location(text, lines)
    salary_range = _extract_salary(text)
    job_link = _extract_url(text)
    skills = _extract_skills(text)

    return {
        "title": title,
        "company": company,
        "location": location,
        "salary_range": salary_range,
        "job_link": job_link,
        "skills": skills,
    }
