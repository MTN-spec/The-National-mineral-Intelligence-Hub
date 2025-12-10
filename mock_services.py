import random
import datetime

class AkelloService:
    """
    Akello Learning Management System Integration.
    Handles course retrieval, user progress tracking, and dynamic module loading.
    """
    def __init__(self):
        self.courses = [
            {"id": 1, "title": "Intro to Sustainable Mining", "xp": 100, "duration": "2h", "status": "In Progress"},
            {"id": 2, "title": "Sentinel-2 Imagery for Prospecting", "xp": 150, "duration": "3h", "status": "Locked"},
            {"id": 3, "title": "Safety Protocols in Small Scale Mining", "xp": 100, "duration": "1.5h", "status": "Locked"},
            {"id": 4, "title": "Digital Financial Literacy (EcoCash)", "xp": 50, "duration": "1h", "status": "Completed"}
            # {"id": 5, ...} removed in favor of dynamic loading
        ]

    def get_courses(self):
        # Scan data/modules directory for files
        import os
        module_dir = os.path.join(os.getcwd(), "data", "modules")
        
        dynamic_courses = []
        if os.path.exists(module_dir):
            files = [f for f in os.listdir(module_dir) if f.endswith(('.docx', '.pdf', '.txt'))]
            for idx, f in enumerate(files):
                # ID offset by 100 to avoid conflict with static courses
                dynamic_courses.append({
                    "id": 100 + idx,
                    "title": f,
                    "xp": 50, # Standard XP for reading a doc
                    "duration": "Document",
                    "status": "Available"
                })
        
        return self.courses + dynamic_courses

    def complete_course(self, course_id):
        # Handle static course completion
        for c in self.courses:
            if c['id'] == course_id:
                c['status'] = "Completed"
                return True, c['xp']
        
        # Handle dynamic course completion (record progress)
        for course in self.courses:
             return True, 50 # 50 XP for docs
             
        return False, 0

class EcoCashService:
    """
    EcoCash Wallet and Payment Processing Service.
    Manages user balance, transaction history, and payment gateway interactions.
    """
    def __init__(self):
        self.balance = 45.00 # Initial balance in USD/ZiG equivalent
        self.transactions = [
            {"date": "2023-10-25 14:30", "desc": "Gig Payment: Iron data collection", "amount": 20.00, "type": "credit"},
            {"date": "2023-10-24 09:15", "desc": "Akello Course: Premium Unlock", "amount": -5.00, "type": "debit"},
             {"date": "2023-10-20 11:00", "desc": "Data Bundle Purchase", "amount": -10.00, "type": "debit"}
        ]

    def get_balance(self):
        return self.balance

    def pay_user(self, amount, description):
        """Execute payment transaction for completed gig"""
        self.balance += amount
        self.transactions.insert(0, {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "desc": description,
            "amount": amount,
            "type": "credit"
        })
        return True

    def charge_user(self, amount, description):
        """Execute debit transaction for user service"""
        if self.balance >= amount:
            self.balance -= amount
            self.transactions.insert(0, {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "desc": description,
                "amount": -amount,
                "type": "debit"
            })
            return True, "Payment Successful"
        else:
            return False, "Insufficient Funds"

class GigEngine:
    """
    Engine for matching users with Ground Truthing and Online Freelance opportunities.
    Includes briefings and AI grading rubrics.
    """
    def get_gigs(self):
        return [
            {
                "id": 101, 
                "title": "Verify Iron Oxide Anomaly #42", 
                "location": "Mashonaland Central", 
                "reward": 25.00, 
                "status": "Open",
                "type": "Ground Truth",
                "briefing": "Sentinel-2 analysis suggests a high concentration of Iron Oxide near Bindura. We need a physical sample verification. Travel to the coordinates, collect 500g of soil, and upload a photo.",
                "question": "What is the primary visual indicator of Iron Oxide in soil?",
                "expected_answer": "Red color",
                "ai_grading_prompt": "Check if answer mentions 'Red' or 'Rust' color."
            },
            {
                "id": 102, 
                "title": "Clay Deposit Soil Sampling", 
                "location": "Midlands", 
                "reward": 30.00, 
                "status": "Open",
                "type": "Ground Truth",
                "briefing": "Pottery cooperatives need pure clay sources. Area X has shown SWIR signatures matching Kaolinite. Dig 3 test pits.",
                "question": "Which band combination highlights clay minerals best?",
                "expected_answer": "SWIR",
                "ai_grading_prompt": "Check if answer mentions 'SWIR' or 'Shortwave Infrared'."
            },
            {
                "id": 103, 
                "title": "Data Entry: Historical Mining Records", 
                "location": "Online (Remote)", 
                "reward": 15.00, 
                "status": "Open",
                "type": "Freelance",
                "briefing": "We have scanned PDF records of 1980s gold production. Convert the attached page into a CSV format.",
                "question": "What file format is best for structured tabular data?",
                "expected_answer": "CSV",
                "ai_grading_prompt": "Check if answer mentions 'CSV' or 'Excel'."
            },
            {
                "id": 104, 
                "title": "Digitize Geological Map: Mutare", 
                "location": "Online (Remote)", 
                "reward": 45.00, 
                "status": "Open",
                "type": "Freelance",
                "briefing": "Trace the lithological boundaries from the provided scanned map using QGIS. Output must be a Shapefile.",
                "question": "What is the standard vector file format for GIS?",
                "expected_answer": "Shapefile",
                "ai_grading_prompt": "Check if answer mentions 'Shapefile' or 'SHP'."
            },
            {
                "id": 105, 
                "title": "Community Survey: ASM Operations", 
                "location": "Gwanda", 
                "reward": 20.00, 
                "status": "Open",
                "type": "Ground Truth",
                "briefing": "Interview 5 small-scale miners about their mercury usage. Fill in the provided digital questionnaire.",
                "question": "What is the primary health risk of mercury?",
                "expected_answer": "Neurotoxicity",
                "ai_grading_prompt": "Check if answer mentions 'Brain damage' or 'Nervous system'."
            }
        ]

class MentorService:
    """
    Connects users with industry experts.
    """
    def get_mentors(self):
        return [
            {
                "id": 1,
                "name": "Mrs. S. Moyo",
                "role": "Senior Geologist",
                "expertise": "Exploration Geology",
                "bio": "20+ years in gold and lithium exploration across Zimbabwe. Passionate about empowering young women in mining.",
                "availability": "Available",
                "rate": "Free (Community Service)",
                "image": "https://randomuser.me/api/portraits/women/44.jpg"
            },
            {
                "id": 2,
                "name": "Eng. T. Ndlovu",
                "role": "Mining Engineer",
                "expertise": "Small-Scale Operations",
                "bio": "Specialist in optimizing ASM workflows and safety compliance. Former mine manager.",
                "availability": "Limited",
                "rate": "$50/session",
                "image": "https://randomuser.me/api/portraits/men/32.jpg"
            },
            {
                "id": 3,
                "name": "Ms. P. Chidza",
                "role": "Environmental Scientist",
                "expertise": "EIA & Sustainability",
                "bio": "Expert in environmental impact assessments (EIA) for mining projects and reclamation.",
                "availability": "Available",
                "rate": "$30/session",
                "image": "https://randomuser.me/api/portraits/women/68.jpg"
            },
            {
                "id": 4,
                "name": "Mr. K. Banda",
                "role": "GIS Analyst",
                "expertise": "Remote Sensing & Mapping",
                "bio": "Experienced in QGIS, ArcGIS, and satellite imagery analysis for mineral prospecting.",
                "availability": "Available",
                "rate": "$40/session",
                "image": "https://randomuser.me/api/portraits/men/85.jpg"
            },
            {
                "id": 5,
                "name": "Dr. A. Williams",
                "role": "Planetary Geologist",
                "marketing_badge": "NASA",
                "organization": "NASA Jet Propulsion Lab (JPL)",
                "expertise": "Spectral Imaging & Remote Sensing",
                "bio": "Lead researcher on mineral mapping missions. Offering guidance on advanced hyperspectral processing.",
                "availability": "Monthly Workshops",
                "rate": "Free (NASA Outreach)",
                "image": "https://randomuser.me/api/portraits/women/65.jpg"
            },
            {
                "id": 6,
                "name": "Mr. J. Smith",
                "role": "Senior Geophysicist",
                "marketing_badge": "USGS",
                "organization": "U.S. Geological Survey (USGS)",
                "expertise": "Geophysical Surveys",
                "bio": "Specialist in magnetic and radiometric data interpretation for mineral resource assessment.",
                "availability": "Available",
                "rate": "$75/session",
                "image": "https://randomuser.me/api/portraits/men/42.jpg"
            },
            {
                "id": 7,
                "name": "Eng. R. Matema",
                "role": "Production Manager",
                "marketing_badge": "LOCAL",
                "organization": "Mimosa Mining Company",
                "expertise": "PGM Mining & Processing",
                "bio": "Overseeing platinum group metal extraction. Mentoring on industrial-scale mining operations in Zimbabwe.",
                "availability": "Weekends",
                "rate": "Free (CSR Initiative)",
                "image": "https://randomuser.me/api/portraits/men/11.jpg"
            },
            {
                "id": 8,
                "name": "Dr. T. Gwatidzo",
                "role": "Consulting Geologist",
                "marketing_badge": "LOCAL",
                "organization": "RioZim Ltd",
                "expertise": "Gold Exploration",
                "bio": "Expert in Greenstone Belt geology and gold mineralization patterns.",
                "availability": "Available",
                "rate": "$45/session",
                "image": "https://randomuser.me/api/portraits/women/22.jpg"
            }
        ]

class FieldDataService:
    '''
    Service for storing and retrieving Ground Truthing data (GPS points, photos).
    '''
    def __init__(self):
        self.submissions = [
            # Default Field Data
            {"id": 1, "lat": -20.32, "lon": 30.05, "desc": "Pegmatite Outcrop", "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Pegmatite.jpg/320px-Pegmatite.jpg", "user": "Tino"},
            {'id': 2, 'lat': -20.30, 'lon': 30.08, 'desc': 'Possible Lithium indications (Lepidolite)', 'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Lepidolite-2005.jpg/320px-Lepidolite-2005.jpg', 'user': 'Sarah'},
            {'id': 3, 'lat': -20.34, 'lon': 30.02, 'desc': 'Artisanal workings - Shaft 1', 'image': None, 'user': 'Admin'}
        ]
    
    def add_submission(self, lat, lon, desc, image_data=None, user='Anonymous'):
        '''Save a new field submission.'''
        new_id = len(self.submissions) + 1
        # In a real app, we would save the image_data to disk/S3 and store the URL
        # Here we store the object directly
        self.submissions.append({
            "id": new_id,
            "lat": lat,
            "lon": lon,
            "desc": desc,
            "image": "Captured Image", 
            "user": user
        })
        return True
