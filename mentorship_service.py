"""
Mentorship and Talent Service for The National Mineral Intelligence Hub
Zimbabwe Innovation Scope 2026
Provides verified senior mining mentors, professional booking sessions,
and a verified directory of Zimbabwean graduates, geomatics engineers, and ASM apprentices.
"""

import datetime
from typing import List, Dict, Any, Optional

class MentorshipService:
    def __init__(self):
        self.mentors: List[Dict[str, Any]] = [
            {
                "id": "MTR-001",
                "name": "Eng. Tendai Chifamba",
                "title": "Chief Exploration Geologist & PGM Specialist",
                "organization": "Fellow, Geological Society of Zimbabwe (ex-Mimosa / Zimplats)",
                "experience_years": 22,
                "rating": 4.96,
                "sessions_conducted": 84,
                "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80",
                "specialties": ["Great Dyke PGM Reefs", "Spectral Exploration", "Underground Geotechnical Safety"],
                "location": "Gweru / Harare",
                "status": "Available",
                "hourly_rate_usd": 0.0, # Subsidized by Zimbabwe Skills Fund
                "bio": "22 years mapping the Great Dyke and Bushveld Complex. Pioneered geochemical vectoring for platinum group metals in Shurugwi and Wedza sub-chambers."
            },
            {
                "id": "MTR-002",
                "name": "Dr. Ruvimbo Marufu",
                "title": "Senior Metallurgist & Clean Extraction Lead",
                "organization": "University of Zimbabwe / Minerals Innovation Council",
                "experience_years": 17,
                "rating": 4.98,
                "sessions_conducted": 112,
                "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=250&q=80",
                "specialties": ["Mercury-Free Gold Extraction", "Spodumene Beneficiation", "Tailings Reprocessing"],
                "location": "Harare / Kwekwe",
                "status": "Available",
                "hourly_rate_usd": 0.0,
                "bio": "Specialist in non-toxic borax gold beneficiation and hard-rock lithium pegmatite flotation kinetics. Technical advisor to ASM mining syndicates nationwide."
            },
            {
                "id": "MTR-003",
                "name": "Surv. Farai Mataruse",
                "title": "Principal Mine Surveyor & Geomatics Consultant",
                "organization": "Survey Institute of Zimbabwe / Ministry Cadastre Advisor",
                "experience_years": 16,
                "rating": 4.92,
                "sessions_conducted": 67,
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=250&q=80",
                "specialties": ["Drone RTK Photogrammetry", "Cadastral Boundary Law", "Volumetric Stockpile Audits"],
                "location": "Bulawayo / Gwanda",
                "status": "Available",
                "hourly_rate_usd": 0.0,
                "bio": "Expert in resolving overlapping artisanal mining boundaries using RTK GNSS and Sentinel-2 ground control. Licensed photogrammetry drone flight instructor."
            },
            {
                "id": "MTR-004",
                "name": "Chipo Dzimba (MSc)",
                "title": "Environmental Compliance & TSF Safety Auditor",
                "organization": "EMA Certified Lead Auditor / Green Mining Advisory",
                "experience_years": 14,
                "rating": 4.94,
                "sessions_conducted": 93,
                "avatar": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=250&q=80",
                "specialties": ["EMA Sec 97 Environmental Compliance", "TSF Failure Prevention", "Acid Mine Drainage"],
                "location": "Mutare / Kadoma",
                "status": "Available",
                "hourly_rate_usd": 0.0,
                "bio": "Specialist in auditing tailings storage facilities, cyanide neutralization, and environmental remediation along sensitive river catchments."
            }
        ]

        self.talent_pool: List[Dict[str, Any]] = [
            {
                "id": "TLT-101",
                "name": "Nyasha Mhere",
                "qualification": "BSc (Hons) Surveying & Geomatics",
                "institution": "University of Zimbabwe (2025)",
                "specialty": "Remote Sensing & Satellite Spectral Processing",
                "verified_field_hours": 320,
                "rating": 4.9,
                "location": "Harare / Midlands",
                "competency_badges": ["Sentinel-2 Band Ratios", "RTK Drone Pilot", "GIS Cadastre"],
                "open_to": "Concession Technical Attachment & Field Sampling",
                "avatar": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=200&q=80"
            },
            {
                "id": "TLT-102",
                "name": "Blessing Moyo",
                "qualification": "BSc (Hons) Geology",
                "institution": "Midlands State University (2025)",
                "specialty": "Archaean Greenstone Belt Gold & Pegmatite Mapping",
                "verified_field_hours": 410,
                "rating": 4.85,
                "location": "Gweru / Shurugwi",
                "competency_badges": ["Core Logging", "Structural Geology", "XRF Spectrometry"],
                "open_to": "Full-Time Exploration Geologist Trainee",
                "avatar": "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?auto=format&fit=crop&w=200&q=80"
            },
            {
                "id": "TLT-103",
                "name": "Kudakwashe Sithole",
                "qualification": "BSc (Hons) Mining Engineering",
                "institution": "University of Zimbabwe (2024)",
                "specialty": "Open Pit Blast Optimization & Artisanal Mechanization",
                "verified_field_hours": 580,
                "rating": 4.95,
                "location": "Kadoma / Kwekwe",
                "competency_badges": ["Mine Planning", "ASM Safety Auditor", "Shotfirer License"],
                "open_to": "Concession Operations & Shaft Modernization",
                "avatar": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=200&q=80"
            },
            {
                "id": "TLT-104",
                "name": "Tariro Ndlovu",
                "qualification": "BSc Environmental Science & Water Resources",
                "institution": "National University of Science and Technology (NUST)",
                "specialty": "Tailings Dam Water Monitoring & AMD Neutralization",
                "verified_field_hours": 290,
                "rating": 4.88,
                "location": "Bulawayo / Gwanda",
                "competency_badges": ["Water Quality Testing", "EMA EIA Reporting", "reNDVI Ecology"],
                "open_to": "Environmental Compliance Officer",
                "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&q=80"
            }
        ]

        self.bookings: List[Dict[str, Any]] = [
            {
                "id": "BOK-901",
                "mentor_id": "MTR-001",
                "mentor_name": "Eng. Tendai Chifamba",
                "applicant_name": "Selukwe Chrome Cooperative",
                "topic": "Great Dyke Sub-Chamber Seam Correlation & Safety",
                "date": "2026-10-08",
                "time": "10:00 AM",
                "session_type": "On-Site Field Inspection",
                "status": "Confirmed"
            }
        ]

    def get_mentors(self) -> List[Dict[str, Any]]:
        return self.mentors

    def get_talent(self) -> List[Dict[str, Any]]:
        return self.talent_pool

    def get_bookings(self) -> List[Dict[str, Any]]:
        return self.bookings

    def book_session(self, mentor_id: str, applicant_name: str, email: str, topic: str, date: str, time: str, session_type: str = "Virtual 1-on-1") -> Dict[str, Any]:
        mentor = next((m for m in self.mentors if m["id"] == mentor_id), None)
        if not mentor:
            raise ValueError(f"Mentor {mentor_id} not found")

        booking_id = f"BOK-{len(self.bookings) + 902}"
        booking = {
            "id": booking_id,
            "mentor_id": mentor["id"],
            "mentor_name": mentor["name"],
            "applicant_name": applicant_name,
            "applicant_email": email,
            "topic": topic,
            "date": date,
            "time": time,
            "session_type": session_type,
            "status": "Confirmed",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "token": f"NMIH-MTR-{booking_id}-SECURE"
        }
        self.bookings.insert(0, booking)
        return booking

mentorship_service = MentorshipService()
