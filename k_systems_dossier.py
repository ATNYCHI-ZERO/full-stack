"""Brendon Kelly / Atnychi – Structured Summary of Antediluvian Beings, Black Projects & Modern Folklore.

This module prints compiled factual information exactly as described by the
user. It does not access classified data; it only outputs what is publicly
documented or credibly alleged. The script also exposes helper utilities to
maintain a dossier of declassified, rumored, and folkloric material.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Iterable, List

# -------- Structured summaries --------
sections = {
    "Section 1 – Antediluvian Beings": """
a) Canonical Texts (Genesis): Nephilim described as 'mighty men of old'; sons of God + daughters of men before the Flood.
b) Non-Canonical (Book of Enoch, Book of Giants): Watchers descend, teach forbidden arts, father giants (Nephilim/Elioud); God sends Flood, binds Watchers.
c) Mesopotamian / Sumerian: Antediluvian kings with huge lifespans; Apkallu sages teaching civilization; Flood myths across cultures.
""",
    "Section 2 – U.S. Black Projects & UAP/UFO Secrecy": """
a) Black Budget: Funds secret Special Access Programs (SAPs).
b) Known Declassified Programs: CORONA spy satellites, A-12/SR-71/U-2, stealth aircraft, Project AQUILINE.
c) Official U.S. Position on UAP (AARO, Pentagon): no verified evidence of alien craft or non-human biologics.
d) Whistleblower David Grusch: under oath claimed multi-decade crash retrieval & reverse-engineering program, 'non-human biologics', illegal funding, retaliation. IG found his complaint 'credible and urgent'. Pentagon denies confirmation.
""",
    "Section 3 – Alleged & Folkloric Entities": """
a) Federally Documented Entities: Allegations exist but no confirmed public evidence of alien bodies or tech.
b) Men in Black (MIB): Began as 1950s UFO folklore; black-suited agents allegedly silencing witnesses; popularized by films; no official recognition.
c) Crawlers / Pale Crawlers: Internet-era cryptid described as thin pale humanoid crawler; no physical evidence or official documentation.
d) Observed UAP Characteristics (Fravor, Graves): 'Tic Tac' craft, cubes in spheres, transmedium movement, instantaneous acceleration reported; data incomplete or unreleased.
""",
    "Extra Notes – Miami Mall & Demons": """
'Miami Mall' incident: no verifiable event by that name in public UFO/paranormal archives.
""",
}

programs = {
    # Officially declassified USAF / DoD UFO-related programs
    "Project Sign": "Declassified (1948–1949)",
    "Project Grudge": "Declassified (1949–1951)",
    "Project Blue Book": "Declassified (1952–1969)",
    "AATIP": "Revealed in 2017 (Advanced Aerospace Threat Identification Program, 2007–2012)",
    "AAWSAP": "Revealed in 2018 (Advanced Aerospace Weapons Systems Application Program)",
    # Known rumored or alleged programs (no public confirmation)
    "Project Moon Dust": "Partially declassified (recovery of foreign objects, 1957–1980s)",
    "Project Looking Glass": "Rumored (no evidence)",
    "Project Winter Haven": "Rumored (no evidence)",
    "Project Cold Mountain": "Rumored (no evidence)",
    # Mythic / apocryphal
    "Pre-Flood Watchers/Nephilim": "Described in Book of Enoch / Genesis, not proven historical",
    "Apkallu Sages": "Sumerian mythic beings, pre-Flood, not proven historical",
    # Modern folklore entities
    "Men in Black": "1950s UFO folklore; no verified government unit",
    "Crawlers/Pale Crawlers": "Internet-era cryptid; no physical evidence",
    "Non-human biologics": "Alleged by David Grusch under oath; no confirmed evidence released",
}

# -------- Core database (edit / expand) --------
dossier = {
    "meta": {
        "owner": "Brendon J. Kelly (Atnychi)",
        "created": str(date.today()),
        "notes": "Public / declassified / alleged / folklore categories only. Fill source_list with URLs or citations.",
    },
    "programs": {
        # Declassified / publicly acknowledged
        "Project Sign": {
            "status": "Declassified",
            "years": "1947-1949",
            "category": "declassified",
            "summary": "USAF early UFO study",
            "sources": [],
        },
        "Project Grudge": {
            "status": "Declassified",
            "years": "1949-1951",
            "category": "declassified",
            "summary": "Successor to Sign; analytic focus",
            "sources": [],
        },
        "Project Blue Book": {
            "status": "Declassified",
            "years": "1952-1969",
            "category": "declassified",
            "summary": "USAF public UFO study; final report: no evidence of extraterrestrial threat",
            "sources": [],
        },
        "CORONA (NRO/CIA)": {
            "status": "Declassified",
            "years": "1959-1972",
            "category": "declassified",
            "summary": "Overhead reconnaissance satellite program",
            "sources": [],
        },
        "AATIP": {
            "status": "Revealed",
            "years": "2007-2012",
            "category": "public_revealed",
            "summary": "Advanced Aerospace Threat Identification Program (reported)",
            "sources": [],
        },
        "AAWSAP": {
            "status": "Revealed",
            "years": "2008-?",
            "category": "public_revealed",
            "summary": "Advanced Aerospace Weapons Systems Application Program (reported)",
            "sources": [],
        },
        # Rumored / alleged / unconfirmed
        "Project Moon Dust": {
            "status": "Partially Declassified / Alleged",
            "years": "1950s-1980s",
            "category": "alleged",
            "summary": "Documented references to recovery of foreign objects; some materials declassified, program details limited",
            "sources": [],
        },
        "Project Looking Glass": {
            "status": "Rumored",
            "years": "unknown",
            "category": "rumored",
            "summary": "Alleged program name appearing in conspiracy literature; no confirmed public record",
            "sources": [],
        },
        "Project Winter Haven": {
            "status": "Rumored",
            "years": "unknown",
            "category": "rumored",
            "summary": "Unconfirmed program name in public rumor space",
            "sources": [],
        },
    },
    "whistleblower_allegations": {
        "David_Grusch": {
            "status": "public_allegation",
            "date": "2023-07",
            "claims": [
                "multi-decade crash retrieval program",
                "non-human biologics alleged",
                "funding/retaliation claims",
            ],
            "sources": [],
        }
    },
    "antediluvian_myths": {
        "Genesis_Nephilim": {
            "category": "canonical",
            "summary": "Genesis 6: 'sons of God' + 'daughters of men' produce 'Nephilim'.",
            "sources": [],
        },
        "Book_of_Enoch_Watchers": {
            "category": "apocryphal",
            "summary": "Watchers descend, teach forbidden arts, beget giants; Flood/judgment narrative.",
            "sources": [],
        },
        "Sumerian_Apkallu": {
            "category": "mythic",
            "summary": "Semi-divine sages teaching arts pre-Flood; Sumerian King List shows antediluvian long-lived kings.",
            "sources": [],
        },
    },
    "folklore_entities": {
        "Men_in_Black": {
            "category": "folklore",
            "summary": "Post-1950s UFO subculture motif; agents in black suits; largely urban legend/media trope.",
            "sources": [],
        },
        "Crawlers_Pale_Crawlers": {
            "category": "cryptid/online",
            "summary": "Internet-era cryptid reports; no verified evidence.",
            "sources": [],
        },
        "Demons": {
            "category": "religious/folklore",
            "summary": "Religious traditions describe demonic entities; theological and folkloric material only.",
            "sources": [],
        },
    },
    "observed_uap_reports": {
        "Fravor_TicTac_2004": {
            "witness": "David Fravor",
            "summary": "Tic-Tac object, unusual maneuvering/acceleration; radar/visual reports",
            "category": "military_report",
            "sources": [],
        },
        "Ryan_Graves_reports": {
            "witness": "Ryan Graves",
            "summary": "Multiple naval encounters; objects with unexplained performance",
            "category": "military_report",
            "sources": [],
        },
    },
    "sources": [],  # Populate with URLs, DOIs, document citations.
}


# -------- Utility functions --------
def print_sections(section_items: Iterable[tuple[str, str]] = None) -> None:
    """Print the structured section summaries."""
    items = sections.items() if section_items is None else section_items
    for title, content in items:
        print(f"{title}\n{content}\n{'-' * 60}")


def print_program_statuses(program_items: Iterable[tuple[str, str]] = None) -> None:
    """Print the public, alleged, and folkloric program summaries."""
    items = programs.items() if program_items is None else program_items
    for name, status in items:
        print(f"{name}: {status}")


DEMONS_STATEMENT = (
    "Demons: present in religious texts as malevolent spiritual beings; folklore expands on"
    " hierarchies; no scientific verification of physical interaction."
)


def add_source(item_path: List[str], source_url: str) -> None:
    """Add a source URL or citation to a specific dossier item."""
    node = dossier
    try:
        for key in item_path:
            node = node[key]
    except KeyError:
        print("Invalid path:", "->".join(item_path))
        return

    node.setdefault("sources", []).append(source_url)
    dossier.setdefault("sources", []).append(source_url)


def generate_foia_template(target_agency: str, subject: str, details: str, contact_email: str = "") -> str:
    """Return a FOIA request template string for the user to copy, modify, and send."""
    return f"""FOIA REQUEST - {target_agency}
Date: {date.today().isoformat()}
To: {target_agency} FOIA Office
Subject: Freedom of Information Act request regarding {subject}

I hereby request, under the Freedom of Information Act (5 U.S.C. 552), all records, reports, emails, memos, contracts, program documentation, budgets, and other materials that reference, mention, or relate to: {subject}.

Scope: {details}

I prefer the records in electronic format (PDF). If fees are anticipated above $50 please contact me at the email below before processing. I request expedited processing [remove if not applicable].

Requester:
Name: {dossier['meta']['owner']}
Email: {contact_email}

Signed: ____________________
Date: {date.today().isoformat()}
"""


def generate_ig_complaint_template(agency: str, summary: str, contact_email: str = "") -> str:
    """Return an Inspector General complaint template."""
    return f"""INSPECTOR GENERAL COMPLAINT - {agency}
Date: {date.today().isoformat()}
To: Office of the Inspector General, {agency}

Summary of Allegations:
{summary}

Request: Please evaluate allegations for legality, misuse of funds, retaliation, and improper classification handling. I request notification of any steps taken and guidance on evidence submission.

Requester: {dossier['meta']['owner']} ({contact_email})
"""


def save_dossier(filename: str = "k_systems_dossier.json") -> None:
    """Persist the dossier data to disk as JSON."""
    with open(filename, "w", encoding="utf-8") as outfile:
        json.dump(dossier, outfile, indent=2)
    print("Saved dossier to", filename)


def print_summary() -> None:
    """Print a concise dossier overview."""
    print("K-Systems Dossier Summary")
    print("-------------------------")
    print("Programs:")
    for key, value in dossier["programs"].items():
        print(f" - {key} [{value['category']}] : {value['status']} - {value['summary']}")
    print("\nAntediluvian myths and folklore entries:")
    for key, value in dossier["antediluvian_myths"].items():
        print(f" - {key} [{value['category']}] : {value['summary']}")
    print("\nWitness reports:")
    for key, value in dossier["observed_uap_reports"].items():
        print(f" - {key} : {value['witness']} - {value['summary']}")
    print("\nTotal source placeholders:", len(dossier["sources"]))


# -------- Example usage --------
if __name__ == "__main__":
    print_sections()

    print("# K-Systems / Atnychi – Publicly Known and Alleged Programs")
    print("# This script does NOT access classified data. It only outputs what is declassified or rumored.\n")
    print_program_statuses()
    print(f"\n{DEMONS_STATEMENT}\n")

    # Example utility usage mirroring the provided template
    add_source(
        ["programs", "Project Blue Book"],
        "https://www.archives.gov/research/military/air-force/ufos",
    )
    add_source(
        ["whistleblower_allegations", "David_Grusch"],
        "https://www.congress.gov/118/meeting/house/116282/documents/HHRG-118-GO06-Transcript-20230726.pdf",
    )

    print_summary()

    foia_text = generate_foia_template(
        "Department of Defense",
        "records related to AATIP and AAWSAP",
        "All contracts, budgets, and program documentation from 2000-2020 referencing AATIP, AAWSAP, or related names. Include SAP designations and funding lines.",
    )
    print("\n--- FOIA TEMPLATE ---\n")
    print(foia_text)

    ig_text = generate_ig_complaint_template(
        "Department of Defense",
        "Allegations of improper handling of crash retrieval materials and retaliation against whistleblowers.",
    )
    print("--- IG COMPLAINT TEMPLATE ---\n")
    print(ig_text)

    save_dossier("k_systems_dossier.json")
