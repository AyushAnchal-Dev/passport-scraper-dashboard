import random
import hashlib
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.core.config import settings

# ─────────────────────────────────────────────────────────────────────────────
# REAL PLATFORM SIMULATOR TEMPLATES
# These represent posts from Twitter/X, Instagram, LinkedIn, YouTube, Facebook.
# They use deterministic IDs so they never duplicate across scrape cycles.
# Content is drawn from real passport discussion patterns actually found online.
# ─────────────────────────────────────────────────────────────────────────────
PLATFORM_TEMPLATES = [
    # ── TWITTER / X ──────────────────────────────────────────────────────────
    {
        "platform": "twitter", "author": "PassportSeva_Help",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=passportseva",
        "content": "Tatkal passport slots are getting filled within 2 minutes of opening at PSK Delhi. Set your alarm for 9 AM tomorrow and keep refreshing #PassportSeva #Tatkal",
        "likes": 342, "reposts": 89, "comments": 67, "views": 12400,
        "location": {"city": "Delhi", "country": "India"}
    },
    {
        "platform": "twitter", "author": "TravelFreak_Rohit",
        "avatar": "https://api.dicebear.com/7.x/initials/svg?seed=TFR",
        "content": "Finally got my passport renewed after 45 days of waiting! The online tracking system is really good now. Applied through Passport Seva app. 10/10 would recommend #PassportIndia",
        "likes": 211, "reposts": 44, "comments": 38, "views": 8900,
        "location": {"city": "Mumbai", "country": "India"}
    },
    {
        "platform": "twitter", "author": "ConsularAlert",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=consular",
        "content": "⚠️ WARNING: Multiple fake websites are collecting passport application fees and disappearing. The ONLY official portal is passportindia.gov.in — Do NOT pay on any other site! #ScamAlert",
        "likes": 5621, "reposts": 2340, "comments": 189, "views": 98000,
        "location": None
    },
    {
        "platform": "twitter", "author": "MEA_India_Desk",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=meaindia",
        "content": "🇮🇳 Official: Ministry of External Affairs launches 15 new Passport Seva Kendras across Tier-2 cities. Residents of Patna, Surat, Vadodara can now apply locally. Full list: mea.gov.in/passport #GovernmentAnnouncement",
        "likes": 8934, "reposts": 3201, "comments": 421, "views": 145000,
        "location": None
    },
    {
        "platform": "twitter", "author": "GlobalPassportIndex",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=gpi",
        "content": "📊 Breaking: Henley Passport Index Q2 2025 — French and German passports retain #1 spot with 194 visa-free destinations. Indian passport ranks 80th. Full report: henleyglobal.com #PassportRankings #News",
        "likes": 1203, "reposts": 567, "comments": 234, "views": 43000,
        "location": None
    },
    {
        "platform": "twitter", "author": "PranavTravels",
        "avatar": "https://api.dicebear.com/7.x/initials/svg?seed=PT",
        "content": "Lost my passport in Bangkok and the Indian Embassy emergency service was incredible. Got an Emergency Certificate within 4 hours to board my flight. Thank you @MEAIndia! #TravelIssues",
        "likes": 892, "reposts": 145, "comments": 93, "views": 22000,
        "location": {"city": "Bangkok", "country": "Thailand"}
    },
    {
        "platform": "twitter", "author": "VisaHelpDesk",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=visahelp",
        "content": "Schengen visa with Indian passport: Italy Embassy now requires full bank statements for 3 months. Applied last week, processing time is around 15 working days. Tips in thread 👇 #Visa #Schengen",
        "likes": 673, "reposts": 189, "comments": 112, "views": 19400,
        "location": None
    },
    {
        "platform": "twitter", "author": "NRILegal_Update",
        "avatar": "https://api.dicebear.com/7.x/initials/svg?seed=NLU",
        "content": "Appointment booking tip: Use Passport Seva app and check 'Appointment Available' notification. New slots open every day at 9 AM IST. Book within 3 minutes or they're gone! #Appointment #PassportTip",
        "likes": 445, "reposts": 201, "comments": 88, "views": 15600,
        "location": {"city": "Bangalore", "country": "India"}
    },
    # ── INSTAGRAM ────────────────────────────────────────────────────────────
    {
        "platform": "instagram", "author": "wanderlust.priya",
        "avatar": "https://api.dicebear.com/7.x/lorelei/svg?seed=priya",
        "content": "Passport days are DONE ✈️🌍 Finally got my 10-year passport renewed after the entire drama of getting a Tatkal appointment! Swipe to see the journey. The officer at PSK Pune was super helpful and polite. #PassportRenewed #Tatkal #TravelGram",
        "likes": 3421, "reposts": 0, "comments": 187, "views": 42000,
        "location": {"city": "Pune", "country": "India"}
    },
    {
        "platform": "instagram", "author": "travel.tales.neha",
        "avatar": "https://api.dicebear.com/7.x/lorelei/svg?seed=neha",
        "content": "URGENT travel tip from personal experience: Always check your passport validity before booking flights! I almost got denied boarding because my passport had less than 6 months validity for my Dubai trip 😰 #TravelTips #PassportValid #TravelIssues",
        "likes": 5621, "reposts": 0, "comments": 293, "views": 78000,
        "location": {"city": "Mumbai", "country": "India"}
    },
    {
        "platform": "instagram", "author": "passport.facts.india",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=pfi",
        "content": "📣 New Rule Update: MEA India has officially increased the Tatkal passport fee by ₹2000 effective June 2025. Normal processing remains the same. Save this post! #PassportNews #Tatkal #GovernmentAnnouncement",
        "likes": 2890, "reposts": 0, "comments": 456, "views": 61000,
        "location": None
    },
    {
        "platform": "instagram", "author": "scam.busters.india",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=scambuster",
        "content": "🚨 PASSPORT SCAM ALERT 🚨 Facebook groups are selling guaranteed Tatkal slots for ₹5000-₹15000. THIS IS ILLEGAL. Slots cannot be reserved by agents. Report these accounts immediately! @cybercellindia #ScamAlert #PassportFraud",
        "likes": 11200, "reposts": 0, "comments": 892, "views": 210000,
        "location": None
    },
    {
        "platform": "instagram", "author": "expat.life.london",
        "avatar": "https://api.dicebear.com/7.x/lorelei/svg?seed=expatl",
        "content": "Applied for Indian passport renewal at the London High Commission. Process was smooth — appointment booked online, documents verified in 20 minutes, passport delivered in 8 working days! Sharing my checklist in the link in bio 🙌 #NRI #PassportRenewal #London",
        "likes": 1892, "reposts": 0, "comments": 145, "views": 29000,
        "location": {"city": "London", "country": "United Kingdom"}
    },
    # ── LINKEDIN ──────────────────────────────────────────────────────────────
    {
        "platform": "linkedin", "author": "Rajesh Sharma - Immigration Consultant",
        "avatar": "https://api.dicebear.com/7.x/initials/svg?seed=RS",
        "content": "Important update for NRI professionals: The Passport Seva portal has streamlined the online renewal process. As of May 2025, documents can be submitted digitally — no physical visit needed for straightforward renewals. This is a major step forward for Indian diaspora. #PassportIndia #NRI #ImmigrationUpdate",
        "likes": 2341, "reposts": 234, "comments": 189, "views": 45000,
        "location": {"city": "Toronto", "country": "Canada"}
    },
    {
        "platform": "linkedin", "author": "Ananya Mehta - Visa & Travel Lawyer",
        "avatar": "https://api.dicebear.com/7.x/initials/svg?seed=AM",
        "content": "Heads up for anyone applying for Schengen visa with an Indian passport: After the recent EU-India visa talks, processing times at German and French embassies have improved significantly. Average is now 12-15 working days vs 25+ days last year. #Visa #Schengen #TravelLaw",
        "likes": 1876, "reposts": 312, "comments": 156, "views": 38000,
        "location": None
    },
    {
        "platform": "linkedin", "author": "Vikram Patel - Travel & Compliance",
        "avatar": "https://api.dicebear.com/7.x/initials/svg?seed=VP",
        "content": "A client's passport was stolen in Paris last week. Within 24 hours, our team coordinated with the Indian Consulate to arrange an Emergency Certificate. Key learning: Always travel with 2 colour photos and a copy of your passport's data page. #TravelSafety #PassportStolen",
        "likes": 3210, "reposts": 445, "comments": 267, "views": 62000,
        "location": {"city": "Paris", "country": "France"}
    },
    {
        "platform": "linkedin", "author": "Tech4Gov - Digital India",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=tech4gov",
        "content": "The Ministry of External Affairs has approved ₹840 crore for digital transformation of passport services. mPassport Police App now covers 650+ districts. Real-time police verification via mobile is reducing processing delays by 40%. #DigitalIndia #PassportSeva #GovernmentAnnouncement",
        "likes": 5430, "reposts": 890, "comments": 321, "views": 89000,
        "location": None
    },
    # ── YOUTUBE ───────────────────────────────────────────────────────────────
    {
        "platform": "youtube", "author": "PassportGuideIndia",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=pgi",
        "content": "TATKAL PASSPORT COMPLETE GUIDE 2025 | How to Book Appointment, Documents Required, Process Time | Step-by-Step Tutorial | Includes PSK visit experience #TatkalPassport #PassportSeva #India",
        "likes": 18400, "reposts": 0, "comments": 2341, "views": 890000,
        "location": None
    },
    {
        "platform": "youtube", "author": "NRI Life Chronicles",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=nrilc",
        "content": "My PASSPORT RENEWAL experience at VFS UK London 2025 - Documents needed, Timeline, Cost | Avoid these common mistakes! | Watch before you apply | #PassportRenewal #NRILife #UKIndia",
        "likes": 5670, "reposts": 0, "comments": 891, "views": 234000,
        "location": {"city": "London", "country": "United Kingdom"}
    },
    {
        "platform": "youtube", "author": "Travel Scam Busters",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=tsb",
        "content": "EXPOSING Passport Appointment Scams in 2025 | How fake agents steal your money | Real Investigation | How to spot & report fraud websites | #PassportScam #ConsumerAlert",
        "likes": 9210, "reposts": 0, "comments": 1456, "views": 412000,
        "location": None
    },
    {
        "platform": "youtube", "author": "Visa Expert Official",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=veo",
        "content": "Henley Passport Index 2025 FULL BREAKDOWN | Which passport is most powerful? | India rank revealed | Visa-free travel changes | #PassportIndex #HenleyPassport #News",
        "likes": 12300, "reposts": 0, "comments": 1892, "views": 567000,
        "location": None
    },
    # ── FACEBOOK ──────────────────────────────────────────────────────────────
    {
        "platform": "facebook", "author": "Passport Seva Community India",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=psci",
        "content": "📢 COMMUNITY ALERT: Several members have reported receiving calls from fraudsters claiming to be from Passport Seva with 'special offer' slots. DO NOT share OTP or pay any amount. Passport Seva never calls for payment! Report to cybercrime.gov.in #Fraud #ScamAlert #PassportScam",
        "likes": 8941, "reposts": 3201, "comments": 567, "views": 178000,
        "location": None
    },
    {
        "platform": "facebook", "author": "Indian Passport Help Group",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=iphg",
        "content": "IMPORTANT: If you have a police verification appointment, make sure to carry the ORIGINAL form printed from passportindia.gov.in along with all supporting documents. Police officers are NOT accepting digital copies in most districts. Share this to help others! #PoliceVerification #Application",
        "likes": 4562, "reposts": 1890, "comments": 312, "views": 89000,
        "location": {"city": "Delhi", "country": "India"}
    },
    {
        "platform": "facebook", "author": "पासपोर्ट सेवा हिंदी",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=hindi",
        "content": "तत्काल पासपोर्ट के लिए अपॉइंटमेंट कैसे बुक करें? हर सुबह 9 बजे PSK में नए स्लॉट खुलते हैं। 3 मिनट के अंदर बुक करें। सभी जरूरी दस्तावेज पहले से तैयार रखें। #TatkalPassport #PassportSeva #हिंदी",
        "likes": 3421, "reposts": 890, "comments": 445, "views": 67000,
        "location": {"city": "Lucknow", "country": "India"}
    },
    {
        "platform": "facebook", "author": "Global NRI Network",
        "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=gnri",
        "content": "For NRIs planning to visit India: Your OCI card must be carried along with your foreign passport at all times. Also check passport validity — most countries require 6 months validity beyond your stay period. Travel safe! #NRI #OCI #TravelTips",
        "likes": 2341, "reposts": 567, "comments": 234, "views": 45000,
        "location": None
    },
]


class ScraperService:
    @staticmethod
    def scrape_reddit() -> List[Dict[str, Any]]:
        """
        Scrapes real posts from Reddit using the public JSON feed.
        Targets 8 high-yield subreddit+query combinations.
        Uses a 7-day rolling window for sufficient data volume.
        """
        posts = []
        targets = [
            ("Passports", "passport", 25),
            ("travel",    "passport", 20),
            ("india",     "passport", 20),
            ("immigration", "passport", 15),
            ("india",     "tatkal",   15),
            ("travel",    "visa",     15),
            ("Passports", "lost stolen emergency", 15),
            ("Passports", "appointment renewal",   15),
        ]
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        }

        for sub, query, limit in targets:
            try:
                url = (
                    f"https://www.reddit.com/r/{sub}/search.json"
                    f"?q={requests.utils.quote(query)}&sort=new&limit={limit}&restrict_sr=on"
                )
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200:
                    print(f"Reddit r/{sub} q={query}: HTTP {res.status_code}")
                    continue

                children = res.json().get("data", {}).get("children", [])
                for child in children:
                    pd = child.get("data", {})
                    created_utc = pd.get("created_utc")
                    if not created_utc:
                        continue
                    post_time = datetime.utcfromtimestamp(created_utc)
                    if datetime.utcnow() - post_time > timedelta(hours=24):
                        continue

                    title    = pd.get("title", "")
                    selftext = pd.get("selftext", "")
                    content  = f"{title}\n\n{selftext}".strip()[:2000]
                    if len(content) < 20:          # skip near-empty posts
                        continue

                    posts.append({
                        "post_id":      f"reddit_{pd.get('id')}",
                        "platform":     "reddit",
                        "author":       f"u/{pd.get('author', 'unknown')}",
                        "author_avatar": (
                            "https://api.dicebear.com/7.x/identicon/svg?seed="
                            + pd.get("author", "reddit")
                        ),
                        "url":      f"https://reddit.com{pd.get('permalink', '')}",
                        "content":  content,
                        "created_at": post_time,
                        "likes":    pd.get("ups", 0),
                        "reposts":  0,
                        "comments": pd.get("num_comments", 0),
                        "views":    pd.get("ups", 0) * 10,
                        "location": None,
                    })
            except Exception as exc:
                print(f"Error scraping Reddit r/{sub} q={query}: {exc}")

        return posts

    @staticmethod
    def get_platform_posts() -> List[Dict[str, Any]]:
        """
        Returns deterministic multi-platform posts (Twitter/X, Instagram,
        LinkedIn, YouTube, Facebook) derived from real passport discussion patterns.
        These posts have stable IDs (content-hash-based) so they are inserted once
        and never create duplicates across scrape cycles.
        """
        import hashlib
        posts = []
        now = datetime.utcnow()
        # Spread posts across the past 6 days deterministically
        base_time = now.replace(minute=0, second=0, microsecond=0)

        for idx, tpl in enumerate(PLATFORM_TEMPLATES):
            content     = tpl["content"]
            hours_ago   = (idx * 7.2) % (6 * 24)          # spread over 6 days
            created_at  = base_time - timedelta(hours=hours_ago)

            id_seed     = f"{tpl['platform']}_{tpl['author']}_{content[:40]}"
            post_id     = "sim_" + hashlib.md5(id_seed.encode()).hexdigest()[:12]

            posts.append({
                "post_id":       post_id,
                "platform":      tpl["platform"],
                "author":        tpl["author"],
                "author_avatar": tpl["avatar"],
                "url": (
                    f"https://{tpl['platform']}.com/"
                    + tpl["author"].replace(" ", "_").lower()
                ),
                "content":    content,
                "created_at": created_at,
                "likes":      tpl["likes"],
                "reposts":    tpl["reposts"],
                "comments":   tpl["comments"],
                "views":      tpl["views"],
                "location":   tpl.get("location"),
            })
        return posts

    @classmethod
    def fetch_all(cls) -> List[Dict[str, Any]]:
        """
        Fetches from:
          - Real Reddit (24-hour window, targeted queries) if MOCK_SCRAPER_MODE is False
          - Multi-platform simulated posts if MOCK_SCRAPER_MODE is True
        """
        results = []

        if settings.MOCK_SCRAPER_MODE:
            # 1. Multi-platform simulated posts for development/demo
            try:
                platform_posts = cls.get_platform_posts()
                results.extend(platform_posts)
                print(f"MOCK MODE: Added {len(platform_posts)} simulated platform posts.")
            except Exception as exc:
                print(f"Failed to generate platform posts: {exc}")
        else:
            # 2. Real Reddit posts
            try:
                reddit_posts = cls.scrape_reddit()
                results.extend(reddit_posts)
                print(f"PRODUCTION MODE: Scraped {len(reddit_posts)} real posts from Reddit.")
            except Exception as exc:
                print(f"Failed to scrape Reddit: {exc}")

        # Deduplicate by post_id
        seen   = set()
        deduped = []
        for post in results:
            if post["post_id"] not in seen:
                seen.add(post["post_id"])
                deduped.append(post)

        print(f"Total unique posts to process: {len(deduped)}")
        return deduped
